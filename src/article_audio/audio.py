import io
import json
import math
import re
import shutil
import subprocess
import wave
from pathlib import Path

from .errors import UserError


def split_text(text: str, max_chars: int = 3000) -> list[str]:
    if not text.strip():
        raise UserError("The transcript is empty.")
    if max_chars < 32 or max_chars > 6000:
        raise UserError("Chunk size must be between 32 and 6000 characters.")
    chunks = []
    while len(text) > max_chars:
        window = text[:max_chars]
        candidates = [match.end() for match in re.finditer(r"\n\s*\n", window)]
        if not candidates or candidates[-1] < max_chars // 3:
            candidates = [match.end() for match in re.finditer(r"[.!?]\s+|\s+", window)]
        split = candidates[-1] if candidates else max_chars
        chunks.append(text[:split])
        text = text[split:]
    if text:
        chunks.append(text)
    # Trailing whitespace belongs to the preceding segment, not a synthesis request.
    if len(chunks) > 1 and not chunks[-1].strip():
        suffix = chunks.pop()
        if len(chunks[-1]) + len(suffix) <= max_chars:
            chunks[-1] += suffix
        else:
            chunks.append(suffix)
    return chunks


def decode_audio(data: bytes, mime_type: str) -> bytes:
    mime = mime_type.lower()
    if not data:
        raise UserError("Gemini returned empty audio.", "invalid_audio")
    if mime.startswith("audio/l16") or mime.startswith("audio/pcm"):
        match = re.search(r"rate=(\d+)", mime)
        rate = int(match[1]) if match else 24000
        if len(data) % 2 or rate not in (8000, 16000, 24000, 44100, 48000):
            raise UserError("Invalid PCM audio format.", "invalid_audio")
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(data)
        data = output.getvalue()
    elif not mime.startswith(("audio/wav", "audio/x-wav")):
        raise UserError("Unsupported Gemini audio encoding.", "invalid_audio")
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            expected = wav.getnframes() * wav.getnchannels() * wav.getsampwidth()
            if (
                not expected
                or wav.getnchannels() != 1
                or wav.getsampwidth() != 2
                or len(wav.readframes(wav.getnframes())) != expected
            ):
                raise UserError("Empty, truncated, or unsupported WAV audio.", "invalid_audio")
    except (wave.Error, EOFError):
        raise UserError("Gemini returned an invalid WAV file.", "invalid_audio") from None
    return data


def require_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise UserError(
            "Install FFmpeg and ffprobe, then rerun the same job.", "dependency_missing"
        )


def check_narration_duration(text: str, seconds: float) -> None:
    characters = sum(character.isalnum() for character in text)
    # A loose ceiling catches gross truncation without mistaking headings for missing speech.
    if characters >= 200 and seconds < characters / 100:
        raise UserError(
            "Narration is implausibly short for the transcript. Retry generation and audition it.",
            "suspiciously_short_audio",
        )


def validate_narration(audio: bytes, text: str) -> None:
    decode_audio(audio, "audio/wav")
    with wave.open(io.BytesIO(audio), "rb") as wav:
        check_narration_duration(text, wav.getnframes() / wav.getframerate())


def encode_mp3(chunks: list[Path], destination: Path, speed: float) -> float:
    require_ffmpeg()
    combined = destination.with_suffix(".joined.wav")
    pending = destination.with_suffix(".pending.mp3")
    try:
        with wave.open(str(combined), "wb") as output:
            shape = None
            for path in chunks:
                with wave.open(str(path), "rb") as source:
                    current = (source.getnchannels(), source.getsampwidth(), source.getframerate())
                    if shape is None:
                        shape = current
                        output.setnchannels(current[0])
                        output.setsampwidth(current[1])
                        output.setframerate(current[2])
                    elif current != shape:
                        raise UserError(
                            "Audio segments have inconsistent formats.", "invalid_audio"
                        )
                    while frames := source.readframes(65536):
                        output.writeframes(frames)
        result = subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-y",
                "-i",
                str(combined),
                "-map_metadata",
                "-1",
                "-af",
                f"atempo={speed}",
                "-ar",
                "44100",
                "-ac",
                "1",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(pending),
            ],
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise UserError("FFmpeg could not encode the narration.", "audio_encoding_failed")
        duration = probe_audio(pending)
        pending.replace(destination)
        return duration
    finally:
        combined.unlink(missing_ok=True)
        pending.unlink(missing_ok=True)


def probe_audio(path: Path) -> float:
    require_ffmpeg()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        timeout=30,
    )
    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        if (
            result.returncode
            or not math.isfinite(duration)
            or duration <= 0
            or data["streams"][0]["codec_name"] != "mp3"
        ):
            raise ValueError
        return duration
    except (ValueError, KeyError, IndexError, TypeError):
        raise UserError("The file could not be validated as an MP3.", "invalid_audio") from None
