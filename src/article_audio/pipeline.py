import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .audio import decode_audio, encode_mp3, probe_audio, require_ffmpeg, split_text
from .errors import UserError
from .files import atomic_write, file_lock, private_dir
from .gemini import VoiceSettings


class Narrator(Protocol):
    def synthesize(self, text: str, settings: VoiceSettings) -> bytes: ...


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan(text: str, settings: VoiceSettings) -> dict:
    chunks = split_text(text, settings.chunk_chars)
    # Include the encoder contract so changing an export setting invalidates old jobs.
    identity = {
        "schema": 1,
        "text_sha256": digest(text.encode()),
        "settings": asdict(settings),
        "export": {"sample_rate": 44100, "channels": 1, "bitrate": "128k"},
    }
    return {
        **identity,
        "job_id": digest(json.dumps(identity, sort_keys=True).encode())[:24],
        "characters": len(text),
        "words": len(text.split()),
        "chunks": [
            {"index": i, "characters": len(chunk), "sha256": digest(chunk.encode())}
            for i, chunk in enumerate(chunks)
        ],
        "estimated_minutes": round(len(text.split()) / (150 * settings.speed), 2),
    }


def generate(
    text: str,
    settings: VoiceSettings,
    jobs: Path,
    narrator: Narrator,
    metadata: dict | None = None,
    progress=None,
) -> dict:
    require_ffmpeg()
    specification = plan(text, settings)
    private_dir(jobs)
    directory = jobs / specification["job_id"]
    private_dir(directory)
    with file_lock(directory / ".lock"):
        manifest_path = directory / "manifest.json"
        manifest = {
            **specification,
            "status": "pending",
            "segments": {},
            "created_at": datetime.now(UTC).isoformat(),
        }
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                if (
                    not isinstance(manifest, dict)
                    or any(manifest.get(key) != value for key, value in specification.items())
                    or not isinstance(manifest.get("segments"), dict)
                    or any(
                        not isinstance(segment, dict) or not isinstance(segment.get("sha256"), str)
                        for segment in manifest["segments"].values()
                    )
                ):
                    raise ValueError
            except (ValueError, KeyError):
                raise UserError(
                    "Job manifest is damaged. Choose a new output directory.", "invalid_job"
                ) from None
        output = directory / "audio.mp3"
        if output.is_file() and manifest.get("audio_sha256") == digest(output.read_bytes()):
            duration = probe_audio(output)
            return _result(directory, specification, duration, cached=True)
        atomic_write(directory / "transcript.txt", text.encode())
        if metadata:
            atomic_write(directory / "source.json", json.dumps(metadata, indent=2).encode())
        chunks_dir = directory / "chunks"
        private_dir(chunks_dir)

        def save():
            atomic_write(manifest_path, json.dumps(manifest, indent=2).encode())

        manifest["status"] = "generating"
        save()
        audio_paths = []
        try:
            for index, chunk in enumerate(split_text(text, settings.chunk_chars)):
                path = chunks_dir / f"{index:04d}.wav"
                previous = manifest["segments"].get(str(index), {})
                valid = False
                if path.exists() and previous.get("sha256") == digest(path.read_bytes()):
                    try:
                        decode_audio(path.read_bytes(), "audio/wav")
                        valid = True
                    except UserError:
                        pass
                if not valid:
                    # An all-whitespace tail has no speech to synthesize.
                    if not chunk.strip():
                        continue
                    audio = narrator.synthesize(chunk, settings)
                    decode_audio(audio, "audio/wav")
                    atomic_write(path, audio)
                    manifest["segments"][str(index)] = {"sha256": digest(audio)}
                    save()
                audio_paths.append(path)
                if progress:
                    progress(index + 1, len(specification["chunks"]), valid)
            manifest["status"] = "encoding"
            save()
            duration = encode_mp3(audio_paths, output, settings.speed)
            manifest.update(
                status="complete",
                duration_seconds=duration,
                audio_sha256=digest(output.read_bytes()),
            )
            manifest.pop("error_code", None)
            save()
        except UserError as error:
            manifest.update(status="failed", error_code=error.code)
            save()
            raise
        return _result(directory, specification, duration, cached=False)


def _result(directory, specification, duration, cached):
    return {
        "job_id": specification["job_id"],
        "audio_path": str((directory / "audio.mp3").resolve()),
        "manifest_path": str((directory / "manifest.json").resolve()),
        "duration_seconds": round(duration, 3),
        "cached": cached,
        "model": specification["settings"]["model"],
        "voice": specification["settings"]["voice"],
    }
