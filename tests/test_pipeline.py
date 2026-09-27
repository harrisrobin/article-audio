import json

import pytest

from article_audio.audio import decode_audio
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
