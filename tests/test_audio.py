import io
import wave

import pytest

from article_audio.audio import decode_audio, probe_audio, split_text
from article_audio.errors import UserError


def test_chunking_preserves_all_text_including_long_unbroken_unicode():
    text = "Heading\n\nFirst sentence. Second sentence.\n\n" + "語" * 501 + "\nThe end."
    chunks = split_text(text, max_chars=100)
    assert "".join(chunks) == text
    assert all(0 < len(chunk) <= 100 for chunk in chunks)


def test_empty_article_is_rejected():
    with pytest.raises(UserError):
        split_text(" \n\t")


def test_raw_pcm_is_wrapped_once():
    pcm = b"\x00\x01" * 2400
    data = decode_audio(pcm, "audio/L16;codec=pcm;rate=24000")
    with wave.open(io.BytesIO(data), "rb") as wav:
        assert wav.getframerate() == 24000
        assert wav.getnframes() == 2400
        assert wav.readframes(2400) == pcm


def test_wav_is_not_double_wrapped():
    data = decode_audio(b"\x00\x01" * 200, "audio/L16;rate=24000")
    assert decode_audio(data, "audio/wav") == data


def test_invalid_or_unknown_audio_is_rejected():
    for data, mime in [(b"broken", "audio/wav"), (b"abc", "audio/L16"), (b"abc", "text/plain")]:
        with pytest.raises(UserError):
            decode_audio(data, mime)


def test_publish_probe_rejects_non_mp3_audio(tmp_path):
    path = tmp_path / "mistakenly-named.mp3"
    path.write_bytes(decode_audio(b"\x00\x01" * 2400, "audio/L16;rate=24000"))
    with pytest.raises(UserError):
        probe_audio(path)
