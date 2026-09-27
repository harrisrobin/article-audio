import base64
import json

import httpx
import pytest

from article_audio.errors import UserError
from article_audio.gemini import GeminiClient, VoiceSettings


def response_data(finish="STOP"):
    return {
        "candidates": [
            {
                "finishReason": finish,
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "audio/L16;rate=24000",
                                "data": base64.b64encode(b"\x00\x01" * 240).decode(),
                            }
                        }
                    ]
                },
            }
        ]
    }


def test_current_model_keeps_directions_out_of_spoken_text():
    def handler(request):
        assert request.headers["x-goog-api-key"] == "secret"
        assert "secret" not in str(request.url)
        body = json.loads(request.content)
        part = body["contents"][0]["parts"][0]
        assert part["text"] == "The complete article."
        assert part["speech_metadata"]["style"] == "Warm British narration"
        return httpx.Response(200, json=response_data())

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        audio = GeminiClient("secret", transport).synthesize(
            "The complete article.", VoiceSettings(style="Warm British narration")
        )
    assert audio.startswith(b"RIFF")


def test_retries_transient_failures_but_not_authentication():
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(503 if len(attempts) == 1 else 200, json=response_data())

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        GeminiClient("secret", transport, sleep=lambda _: None).synthesize("Text", VoiceSettings())
    assert len(attempts) == 2
    attempts.clear()

    def denied(request):
        attempts.append(request)
        return httpx.Response(403, text="sensitive provider error secret")

    with httpx.Client(transport=httpx.MockTransport(denied)) as transport:
        with pytest.raises(UserError) as error:
            GeminiClient("secret", transport, sleep=lambda _: None).synthesize(
                "Text", VoiceSettings()
            )
    assert len(attempts) == 1
    assert "secret" not in str(error.value)


def test_truncation_never_becomes_a_successful_recording():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=response_data("MAX_TOKENS"))
        )
    ) as transport:
        with pytest.raises(UserError, match="incomplete"):
            GeminiClient("secret", transport).synthesize("Text", VoiceSettings())


def test_legacy_model_uses_its_own_request_schema():
    def handler(request):
        body = json.loads(request.content)
        voice = body["generationConfig"]["speechConfig"]["voiceConfig"]
        assert voice["prebuiltVoiceConfig"]["voiceName"] == "Algenib"
        assert "TRANSCRIPT" in body["contents"][0]["parts"][0]["text"]
        return httpx.Response(200, json=response_data())

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        GeminiClient("secret", transport).synthesize(
            "Text", VoiceSettings(model="gemini-3.1-flash-tts-preview")
        )
