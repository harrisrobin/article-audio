import hashlib
import json
from pathlib import Path

import pytest

from article_audio.audio import decode_audio, encode_mp3
from article_audio.errors import UserError
from article_audio.files import file_lock, private_dir
from article_audio.gemini import VoiceSettings
from article_audio.pipeline import generate, plan


class Narrator:
    def __init__(self, fail_at=None):
        self.calls = []
        self.fail_at = fail_at

    def synthesize(self, text, settings):
        self.calls.append(text)
        if len(self.calls) == self.fail_at:
            raise UserError("Temporary provider failure", "provider_unavailable")
        return decode_audio(b"\x00\x01" * 12000, "audio/L16;rate=24000")


def test_resume_skips_completed_segments_and_repeat_reuses_mp3(tmp_path):
    text = "First paragraph contains a sentence.\n\nSecond paragraph contains another sentence."
    settings = VoiceSettings(chunk_chars=40)
    first = Narrator(fail_at=2)
    with pytest.raises(UserError):
        generate(text, settings, tmp_path / "jobs", first)
    resumed = Narrator()
    result = generate(text, settings, tmp_path / "jobs", resumed)
    assert len(resumed.calls) == len(plan(text, settings)["chunks"]) - 1
    assert result["duration_seconds"] > 0
    repeat = Narrator()
    cached = generate(text, settings, tmp_path / "jobs", repeat)
    assert cached["cached"] is True
    assert repeat.calls == []
    manifest = json.loads((tmp_path / "jobs" / result["job_id"] / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    assert "api_key" not in str(manifest)


def test_settings_change_creates_new_job():
    assert (
        plan("Article", VoiceSettings())["job_id"]
        != plan("Article", VoiceSettings(voice="Charon"))["job_id"]
    )


def test_plan_does_not_expose_article_text():
    result = plan("Unpublished private article", VoiceSettings())
    assert "Unpublished" not in str(result)


def test_cached_generation_updates_supplied_metadata_and_preserves_omitted_fields(tmp_path):
    settings = VoiceSettings()
    original = generate(
        "Article",
        settings,
        tmp_path / "jobs",
        Narrator(),
        metadata={"title": "Wrong title", "author": "Author", "source_url": "https://x.com/one"},
    )
    narrator = Narrator()
    cached = generate(
        "Article", settings, tmp_path / "jobs", narrator, metadata={"title": "Correct title"}
    )
    assert cached["cached"] and not narrator.calls
    source = tmp_path / "jobs" / original["job_id"] / "source.json"
    assert json.loads(source.read_text()) == {
        "title": "Correct title",
        "author": "Author",
        "source_url": "https://x.com/one",
    }


@pytest.mark.parametrize("damage", [[], {"segments": []}, {"segments": {"0": "bad"}}])
def test_damaged_manifest_stops_before_provider_calls(tmp_path, damage):
    settings = VoiceSettings()
    specification = plan("Article", settings)
    directory = tmp_path / "jobs" / specification["job_id"]
    private_dir(tmp_path / "jobs")
    private_dir(directory)
    manifest = {**specification, **damage} if isinstance(damage, dict) else damage
    (directory / "manifest.json").write_text(json.dumps(manifest))
    narrator = Narrator()
    with pytest.raises(UserError, match="manifest is damaged"):
        generate("Article", settings, tmp_path / "jobs", narrator)
    assert narrator.calls == []


def test_concurrent_run_stops_before_provider_calls(tmp_path):
    settings = VoiceSettings()
    directory = tmp_path / "jobs" / plan("Article", settings)["job_id"]
    private_dir(tmp_path / "jobs")
    private_dir(directory)
    narrator = Narrator()
    with file_lock(directory / ".lock"), pytest.raises(UserError, match="Another process"):
        generate("Article", settings, tmp_path / "jobs", narrator)
    assert narrator.calls == []


def test_implausibly_short_provider_audio_cannot_complete(tmp_path):
    settings = VoiceSettings()
    text = "An entire article deserves its complete narration. " * 50
    with pytest.raises(UserError, match="short"):
        generate(text, settings, tmp_path / "jobs", Narrator())
    manifest_path = tmp_path / "jobs" / plan(text, settings)["job_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "failed"
    assert not manifest.get("audio_sha256")


def test_implausibly_short_output_cannot_hide_in_small_chunks(tmp_path):
    settings = VoiceSettings(chunk_chars=40)
    text = "An entire article deserves its complete narration. " * 10

    class BriefNarrator:
        def synthesize(self, text, settings):
            return decode_audio(b"\x00\x01" * 240, "audio/L16;rate=24000")

    with pytest.raises(UserError, match="short"):
        generate(text, settings, tmp_path / "jobs", BriefNarrator())
    manifest_path = tmp_path / "jobs" / plan(text, settings)["job_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "failed"
    assert manifest["segments"] == {}


@pytest.mark.parametrize("cached_format", ["wav", "mp3"])
def test_short_legacy_cache_is_regenerated(tmp_path, cached_format):
    text = "The full article should be narrated. " * 10
    settings = VoiceSettings()

    class FullNarrator(Narrator):
        def synthesize(self, text, settings):
            self.calls.append(text)
            return decode_audio(b"\x00\x01" * 120000, "audio/L16;rate=24000")

    result = generate(text, settings, tmp_path / "jobs", FullNarrator())
    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text())
    chunk_path = manifest_path.parent / "chunks/0000.wav"
    chunk_path.write_bytes(decode_audio(b"\x00\x01" * 12000, "audio/L16;rate=24000"))
    manifest["segments"]["0"]["sha256"] = hashlib.sha256(chunk_path.read_bytes()).hexdigest()
    output = Path(result["audio_path"])
    if cached_format == "mp3":
        encode_mp3([chunk_path], output, settings.speed)
        manifest["audio_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    else:
        output.unlink()
    manifest_path.write_text(json.dumps(manifest))
    narrator = FullNarrator()
    regenerated = generate(text, settings, tmp_path / "jobs", narrator)
    assert regenerated["cached"] is False
    assert narrator.calls == [text]
