import hashlib
import re
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import boto3
import httpx
from boto3.exceptions import S3UploadFailedError
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .errors import UserError

R2_JURISDICTIONS = ("default", "eu", "us", "fedramp")


def r2_client(credentials: dict, jurisdiction: str = "default"):
    account = credentials["R2_ACCOUNT_ID"]
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account):
        raise UserError("R2_ACCOUNT_ID must be a 32-character Cloudflare account ID.")
    if jurisdiction not in R2_JURISDICTIONS:
        raise UserError("Unsupported R2 jurisdiction. Choose default, eu, us, or fedramp.")
    suffix = "" if jurisdiction == "default" else f".{jurisdiction}"
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account}{suffix}.r2.cloudflarestorage.com",
        aws_access_key_id=credentials["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=credentials["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=15,
            read_timeout=60,
        ),
    )


def publish(
    path: Path,
    client,
    bucket: str,
    expires: int = 604800,
    public_base_url: str | None = None,
    *,
    http: httpx.Client | None = None,
) -> dict:
    if not 1 <= expires <= 604800:
        raise UserError("Link expiry must be between 1 and 604800 seconds.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise UserError("Invalid R2 bucket name.")
    if public_base_url:
        try:
            parsed = urlsplit(public_base_url)
            port = parsed.port
        except ValueError:
            raise UserError("Public audio requires a clean HTTPS bucket base URL.") from None
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or "?" in public_base_url
            or "#" in public_base_url
            or parsed.path not in ("", "/")
            or port not in (None, 443)
            or any(char.isspace() or ord(char) < 32 for char in public_base_url)
        ):
            raise UserError("Public audio requires a clean HTTPS bucket base URL.")
    data = path.read_bytes()
    if not data:
        raise UserError("Cannot upload empty audio.")
    checksum = hashlib.sha256(data).hexdigest()
    key = f"audio/{checksum}.mp3"
    try:
        try:
            existing = client.head_object(Bucket=bucket, Key=key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey", "NotFound"):
                raise
            existing = None
        if existing is None:
            client.upload_file(
                str(path),
                bucket,
                key,
                ExtraArgs={
                    "ContentType": "audio/mpeg",
                    "ContentDisposition": "inline",
                    "Metadata": {"sha256": checksum},
                },
            )
        head = client.head_object(Bucket=bucket, Key=key)
        if (
            head.get("ContentLength") != len(data)
            or head.get("ContentType") != "audio/mpeg"
            or head.get("Metadata", {}).get("sha256") != checksum
        ):
            raise UserError(
                "Uploaded object failed metadata verification.", "upload_verification_failed"
            )
        remote = client.get_object(Bucket=bucket, Key=key, Range="bytes=0-1023")
        sample_size = min(1024, len(data))
        content_range = f"bytes 0-{sample_size - 1}/{len(data)}"
        body = remote.get("Body")
        if body is None:
            raise UserError("Uploaded audio response has no body.", "upload_verification_failed")
        try:
            sample = body.read(sample_size + 1)
        finally:
            body.close()
        if (
            remote.get("ResponseMetadata", {}).get("HTTPStatusCode") != 206
            or remote.get("ContentRange") != content_range
            or sample != data[:sample_size]
        ):
            raise UserError(
                "Uploaded audio failed ranged-read verification.", "upload_verification_failed"
            )
        if public_base_url:
            url = f"{public_base_url.rstrip('/')}/{key}"
            expiry = None
        else:
            url = client.generate_presigned_url(
                "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires
            )
            expiry = (datetime.now(UTC) + timedelta(seconds=expires)).isoformat()
        connection = nullcontext(http) if http is not None else httpx.Client()
        with connection as delivery:
            with delivery.stream(
                "GET", url, headers={"Range": "bytes=0-1023"}, timeout=30, follow_redirects=False
            ) as response:
                if (
                    response.status_code != 206
                    or response.headers.get("Content-Range") != content_range
                    or response.headers.get("Content-Length", str(sample_size)) != str(sample_size)
                ):
                    raise UserError(
                        "Playback URL is not serving ranged audio correctly.",
                        "playback_url_unverified",
                    )
                sample = b""
                for chunk in response.iter_bytes(chunk_size=1024):
                    sample += chunk
                    if len(sample) > sample_size:
                        break
                if sample != data[:sample_size]:
                    raise UserError(
                        "Playback URL returned an incorrect audio range.", "playback_url_unverified"
                    )
    except (ClientError, BotoCoreError, S3UploadFailedError, httpx.HTTPError):
        raise UserError(
            "R2 upload or verification failed. Check credentials, bucket and connectivity.",
            "r2_failed",
        ) from None
    return {
        "audio_url": url,
        "object_key": key,
        "access": "public" if public_base_url else "private",
        "expires_at": expiry,
        "verified": True,
    }
