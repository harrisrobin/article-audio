import base64
import time
from dataclasses import dataclass, field

import httpx

from .audio import decode_audio
from .errors import UserError

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-3.8-flash-tts"
DEFAULT_STYLE = (
    "Thoughtful British narration with a contemporary southern English accent. "
    "Relaxed, assured, lightly expressive, with natural pauses between ideas. "
    "Speak names and numbers clearly. Avoid theatrical or promotional delivery."
)


@dataclass(frozen=True)
class VoiceSettings:
    model: str = field(default=DEFAULT_MODEL, init=False)
    voice: str = field(default="Algenib", init=False)
    style: str = field(default=DEFAULT_STYLE, init=False)
    speed: float = field(default=1.1, init=False)
    chunk_chars: int = 3000

    def __post_init__(self):
        if not 32 <= self.chunk_chars <= 6000:
            raise UserError("Chunk size must be between 32 and 6000 characters.")


class GeminiClient:
    def __init__(self, api_key: str, client: httpx.Client, sleep=time.sleep):
        self.api_key = api_key
        self.client = client
        self.sleep = sleep

    def _request(self, method: str, path: str, **kwargs) -> dict:
        for attempt in range(3):
            try:
                response = self.client.request(
                    method,
                    BASE_URL + path,
                    headers={"x-goog-api-key": self.api_key},
                    timeout=httpx.Timeout(180, connect=15),
                    **kwargs,
                )
            except httpx.TransportError:
                if attempt == 2:
                    raise UserError(
                        "Gemini connection failed after three attempts.", "provider_unavailable"
                    ) from None
                self.sleep(2**attempt)
                continue
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                self.sleep(2**attempt)
                continue
            if not response.is_success:
                messages = {
                    400: "Gemini rejected the fixed narration preset or input. "
                    "Check provider availability and input limits.",
                    401: "Gemini authentication failed. Replace the API key with auth setup.",
                    403: "Gemini denied access. Check the API key, permissions, and billing.",
                    404: "Selected Gemini model unavailable. No model was substituted.",
                    429: "Gemini rate limit or quota exceeded. Retry this job later.",
                }
                raise UserError(
                    messages.get(
                        response.status_code, "Gemini service failed after bounded retries."
                    ),
                    f"gemini_http_{response.status_code}",
                )
            try:
                return response.json()
            except ValueError:
                raise UserError(
                    "Gemini returned an invalid response.", "invalid_provider_response"
                ) from None
        raise AssertionError("Unreachable retry state")

    def synthesize(self, text: str, settings: VoiceSettings) -> bytes:
        part = {"text": text, "speech_metadata": {"style": settings.style}}
        voice = {"voice": settings.voice}
        data = self._request(
            "POST",
            f"/models/{settings.model}:generateContent",
            json={
                "contents": [{"role": "user", "parts": [part]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {"voiceConfig": voice},
                },
            },
        )
        try:
            candidate = data["candidates"][0]
            if not isinstance(candidate, dict):
                raise ValueError
            if candidate.get("finishReason") != "STOP":
                raise UserError(
                    "Gemini narration is incomplete or blocked. No completed audio was accepted; "
                    "try a smaller chunk size or inspect the source.",
                    "incomplete_audio",
                )
            parts = [
                part["inlineData"] for part in candidate["content"]["parts"] if "inlineData" in part
            ]
            if len(parts) != 1:
                raise UserError("Expected one complete audio segment from Gemini.", "invalid_audio")
            audio = parts[0]
            if not isinstance(audio["data"], str) or not isinstance(audio["mimeType"], str):
                raise ValueError
            return decode_audio(base64.b64decode(audio["data"], validate=True), audio["mimeType"])
        except (KeyError, IndexError, TypeError, ValueError):
            raise UserError(
                "Gemini did not return usable audio.", "invalid_provider_response"
            ) from None
