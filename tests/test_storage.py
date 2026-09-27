import hashlib
import io

import httpx
import pytest
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import ClientError

from article_audio.errors import UserError
from article_audio.storage import publish, r2_client


@pytest.mark.parametrize("jurisdiction", ["default", "eu", "us", "fedramp"])
def test_r2_jurisdiction_selects_cloudflare_endpoint(jurisdiction):
    account = "a" * 32
    client = r2_client(
        {"R2_ACCOUNT_ID": account, "R2_ACCESS_KEY_ID": "test", "R2_SECRET_ACCESS_KEY": "test"},
        jurisdiction=jurisdiction,
    )
    suffix = "" if jurisdiction == "default" else f".{jurisdiction}"
    assert client.meta.endpoint_url == f"https://{account}{suffix}.r2.cloudflarestorage.com"


def test_invalid_jurisdiction_cannot_redirect_credentials():
    with pytest.raises(UserError, match="jurisdiction"):
        r2_client(
            {"R2_ACCOUNT_ID": "a" * 32, "R2_ACCESS_KEY_ID": "test", "R2_SECRET_ACCESS_KEY": "test"},
            jurisdiction="attacker.example",
        )


class Bucket:
    def __init__(self):
        self.data = None
        self.uploads = 0

    def head_object(self, **kwargs):
        if self.data is None:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {
            "ContentLength": len(self.data),
            "ContentType": "audio/mpeg",
            "Metadata": {"sha256": hashlib.sha256(self.data).hexdigest()},
        }

    def upload_file(self, filename, bucket, key, ExtraArgs):
        from pathlib import Path

        self.uploads += 1
        self.data = Path(filename).read_bytes()
        assert ExtraArgs["ContentType"] == "audio/mpeg"

    def get_object(self, **kwargs):
        assert kwargs["Range"] == "bytes=0-1023"
        data = self.data[:1024]
        return {
            "Body": io.BytesIO(data),
            "ResponseMetadata": {"HTTPStatusCode": 206},
            "ContentRange": f"bytes 0-{len(data) - 1}/{len(self.data)}",
        }

    def generate_presigned_url(self, operation, Params, ExpiresIn):
        assert operation == "get_object"
        assert ExpiresIn == 604800
        return "https://account.r2.cloudflarestorage.com/bucket/audio?signature=private"


def range_response(data):
    sample = data[:1024]
    return httpx.Response(
        206,
        headers={"Content-Range": f"bytes 0-{len(sample) - 1}/{len(data)}"},
        content=sample,
    )


def test_private_upload_is_verified_and_reused(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    bucket = Bucket()
    requests = []

    def serve(request):
        requests.append(request)
        assert request.headers["range"] == "bytes=0-1023"
        return range_response(path.read_bytes())

    http = httpx.Client(transport=httpx.MockTransport(serve))
    result = publish(path, bucket, "audio-bucket", http=http)
    assert result["access"] == "private"
    assert result["expires_at"]
    assert result["verified"] is True
    publish(path, bucket, "audio-bucket", http=http)
    assert bucket.uploads == 1
    assert len(requests) == 2
    assert "signature" in requests[0].url.query.decode()


def test_inaccessible_signed_url_cannot_report_success(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(403)))
    with pytest.raises(UserError, match="Playback URL"):
        publish(path, Bucket(), "audio-bucket", http=http)


def test_public_upload_verifies_actual_playback_url(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)

    def serve(request):
        assert request.url.host == "audio.example.com"
        return range_response(path.read_bytes())

    http = httpx.Client(transport=httpx.MockTransport(serve))
    result = publish(
        path, Bucket(), "audio-bucket", public_base_url="https://audio.example.com", http=http
    )
    assert result["access"] == "public"
    assert result["expires_at"] is None


def test_invalid_range_response_cannot_report_success(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    bucket = Bucket()
    bucket.get_object = lambda **_: {
        "Body": io.BytesIO(b"wrong"),
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    with pytest.raises(UserError):
        publish(path, bucket, "audio-bucket")


def test_public_mode_requires_an_https_domain(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3")
    with pytest.raises(UserError):
        publish(path, Bucket(), "audio-bucket", public_base_url="http://example.com")


def test_managed_upload_errors_are_safe(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3")
    bucket = Bucket()

    def fail(*args, **kwargs):
        raise S3UploadFailedError("provider details must stay private")

    bucket.upload_file = fail
    with pytest.raises(UserError, match="R2 upload") as error:
        publish(path, bucket, "audio-bucket")
    assert "provider details" not in str(error.value)


@pytest.mark.parametrize(
    "url",
    [
        "https://audio.example.com/existing/object.mp3",
        "https://audio.example.com/prefix/",
        "https://audio.example.com:invalid",
        "https://[invalid",
        "https://audio.example.com\n",
        "https://audio.example.com?",
        "https://audio.example.com#",
        "https://audio.example.com/?",
        "https://audio.example.com/#",
    ],
)
def test_invalid_bucket_base_stops_before_upload(tmp_path, url):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3")
    bucket = Bucket()
    with pytest.raises(UserError, match="bucket base URL"):
        publish(path, bucket, "audio-bucket", public_base_url=url)
    assert bucket.uploads == 0


@pytest.mark.parametrize("damage", ["missing-range", "wrong-total", "wrong-length", "extra-body"])
def test_incorrect_playback_range_cannot_be_verified(tmp_path, damage):
    data = b"ID3" + b"x" * 4096
    path = tmp_path / "audio.mp3"
    path.write_bytes(data)

    def serve(_):
        response = range_response(data)
        if damage == "missing-range":
            del response.headers["Content-Range"]
        elif damage == "wrong-total":
            response.headers["Content-Range"] = "bytes 0-1023/1024"
        elif damage == "wrong-length":
            response.headers["Content-Length"] = "1"
        else:
            response = httpx.Response(
                206,
                headers={"Content-Range": f"bytes 0-1023/{len(data)}", "Content-Length": "1024"},
                content=data[:1024] + b"unexpected",
            )
        return response

    with httpx.Client(transport=httpx.MockTransport(serve)) as http:
        with pytest.raises(UserError) as error:
            publish(path, Bucket(), "audio-bucket", http=http)
    assert error.value.code == "playback_url_unverified"


def test_wrong_s3_range_total_cannot_be_verified(tmp_path):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 4096)
    bucket = Bucket()
    get = bucket.get_object

    def wrong_range(**kwargs):
        result = get(**kwargs)
        result["ContentRange"] = "bytes 0-1023/1024"
        return result

    bucket.get_object = wrong_range
    with pytest.raises(UserError) as error:
        publish(path, bucket, "audio-bucket")
    assert error.value.code == "upload_verification_failed"


def test_short_audio_and_root_slash_are_supported(tmp_path):
    data = b"ID3" + b"x" * 100
    path = tmp_path / "audio.mp3"
    path.write_bytes(data)
    with httpx.Client(transport=httpx.MockTransport(lambda _: range_response(data))) as http:
        result = publish(
            path, Bucket(), "audio-bucket", public_base_url="https://audio.example/", http=http
        )
    assert result["verified"] is True
    assert result["audio_url"].startswith("https://audio.example/audio/")


@pytest.mark.parametrize("missing", ["ContentLength", "Body"])
def test_incomplete_s3_response_is_reported_safely(tmp_path, missing):
    path = tmp_path / "audio.mp3"
    path.write_bytes(b"ID3" + b"x" * 2048)
    bucket = Bucket()
    bucket.data = path.read_bytes()
    method = "head_object" if missing == "ContentLength" else "get_object"
    original = getattr(bucket, method)

    def malformed(**kwargs):
        result = original(**kwargs)
        removed = result.pop(missing)
        if missing == "Body":
            removed.close()
        return result

    setattr(bucket, method, malformed)
    with pytest.raises(UserError) as error:
        publish(path, bucket, "audio-bucket")
    assert error.value.code == "upload_verification_failed"
