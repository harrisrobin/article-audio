import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import httpx

from . import __version__
from .audio import probe_audio
from .cloudflare import provision_r2
from .credentials import GROUPS, CredentialStore
from .errors import UserError
from .gemini import DEFAULT_STYLE, MODELS, GeminiClient, VoiceSettings
from .onboarding import SetupServer
from .pipeline import generate, plan
from .storage import R2_JURISDICTIONS, publish, r2_client


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Narrate article text with Gemini and optionally R2."
    )
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument(
        "--config-dir", type=Path, help="Private credentials directory, outside the repo"
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "doctor", help="Check dependencies and credential presence without showing values"
    )
    commands.add_parser("models", help="List Gemini TTS models available to the configured key")
    auth = commands.add_parser(
        "auth", help="Configure credentials without placing values in arguments"
    )
    actions = auth.add_subparsers(dest="auth_command", required=True)
    actions.add_parser("status", help="Report missing credential names")
    provision = actions.add_parser(
        "provision-r2", help="Create a private bucket and scoped upload key"
    )
    provision.add_argument(
        "--retry-token",
        action="store_true",
        help="Retry only after revoking an uncertain previous upload token",
    )
    actions.add_parser("import-json", help="Read credential JSON on stdin from a secure handoff")
    injected = actions.add_parser("import-env", help="Persist credentials injected by the host")
    injected.add_argument("provider", choices=GROUPS)
    setup = actions.add_parser(
        "setup", help="Collect credentials with a local form or hidden terminal input"
    )
    setup.add_argument("provider", choices=GROUPS)
    setup.add_argument("--method", choices=("form", "terminal"), default="form")
    for name in ("plan", "generate"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path, help="Complete UTF-8 narration transcript")
        command.add_argument("--model", choices=MODELS, default=MODELS[0])
        command.add_argument("--voice", default="Algenib")
        command.add_argument("--speed", type=float, default=1.1)
        command.add_argument("--chunk-chars", type=int, default=3000)
        command.add_argument(
            "--style-file", type=Path, help="Voice direction, separate from spoken text"
        )
        if name == "generate":
            data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
            command.add_argument(
                "--output-dir",
                type=Path,
                default=Path(os.environ.get("ARTICLE_AUDIO_DATA_DIR", data / "article-audio/jobs")),
            )
            command.add_argument("--title")
            command.add_argument("--author")
            command.add_argument("--source-url")
            command.add_argument("--max-chunks", type=int, default=100)
    upload = commands.add_parser(
        "publish", help="Upload an existing MP3 and return a verified R2 link"
    )
    upload.add_argument("audio", type=Path)
    upload.add_argument("--expires", type=int, default=604800)
    upload.add_argument(
        "--jurisdiction",
        choices=R2_JURISDICTIONS,
        default=os.environ.get("R2_JURISDICTION", "default"),
        help="Bucket jurisdiction, also configurable with R2_JURISDICTION",
    )
    upload.add_argument("--public-base-url", help="Explicitly request a public HTTPS playback link")
    return root


def _status(store):
    return {group: store.status(group) for group in GROUPS}


def dispatch(args) -> dict:
    store = CredentialStore(args.config_dir)
    if args.command == "doctor":
        return {
            "version": __version__,
            "python": sys.version.split()[0],
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "ffprobe": bool(shutil.which("ffprobe")),
            "credentials": _status(store),
        }
    if args.command == "auth":
        if args.auth_command == "status":
            return _status(store)
        if args.auth_command == "provision-r2":
            with httpx.Client(trust_env=False) as http:
                return provision_r2(store, http, retry_token=args.retry_token)
        if args.auth_command == "import-json":
            try:
                raw = sys.stdin.read(65537)
                if len(raw) > 65536:
                    raise ValueError
                values = json.loads(raw)
            except ValueError:
                raise UserError("Provide valid credential JSON on stdin, at most 64 KiB.") from None
            store.save(values)
        elif args.auth_command == "import-env":
            store.import_environment(args.provider)
        elif args.method == "form":
            SetupServer(store, args.provider).run()
        else:
            if not sys.stdin.isatty():
                raise UserError(
                    "Hidden input needs a terminal. Use the local form or a secure import."
                )
            store.save({key: getpass.getpass(f"{key}: ") for key in GROUPS[args.provider]})
        return {"saved": True, "credentials": _status(store)}
    if args.command == "models":
        key = store.require("gemini")["GEMINI_API_KEY"]
        with httpx.Client() as http:
            return {"models": GeminiClient(key, http).models()}
    if args.command == "publish":
        duration = probe_audio(args.audio)
        credentials = store.require("r2")
        result = publish(
            args.audio,
            r2_client(credentials, args.jurisdiction),
            credentials["R2_BUCKET"],
            args.expires,
            args.public_base_url,
        )
        return {**result, "duration_seconds": round(duration, 3)}
    if args.input.stat().st_size > 1_000_000:
        raise UserError("Transcript exceeds the 1 MB input limit. Split it into separate articles.")
    text = args.input.read_text(encoding="utf-8")
    style = args.style_file.read_text(encoding="utf-8") if args.style_file else DEFAULT_STYLE
    settings = VoiceSettings(args.model, args.voice, style, args.speed, args.chunk_chars)
    specification = plan(text, settings)
    if args.command == "plan":
        return specification
    if len(specification["chunks"]) > args.max_chunks:
        raise UserError(
            "This job exceeds --max-chunks. Review the plan before increasing the limit."
        )
    key = store.require("gemini")["GEMINI_API_KEY"]
    with httpx.Client() as http:
        return generate(
            text,
            settings,
            args.output_dir,
            GeminiClient(key, http),
            metadata={"title": args.title, "author": args.author, "source_url": args.source_url},
            progress=lambda done, total, cached: print(
                json.dumps(
                    {
                        "segment": done,
                        "total": total,
                        "cached": cached,
                    }
                ),
                file=sys.stderr,
                flush=True,
            ),
        )


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        # Generated articles and temporary audio should be private by default too.
        os.umask(0o077)
        result = dispatch(args)
        print(json.dumps(result, indent=2), flush=True)
        return 0
    except UserError as error:
        print(json.dumps({"error": {"code": error.code, "message": str(error)}}))
        return 2
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        print(
            json.dumps(
                {
                    "error": {
                        "code": "local_io_failed",
                        "message": "Local file or process failed. Check paths and dependencies.",
                    }
                }
            )
        )
        return 2
    except KeyboardInterrupt:
        print(
            json.dumps(
                {
                    "error": {
                        "code": "interrupted",
                        "message": "Interrupted. Completed audio segments are saved.",
                    }
                }
            )
        )
        return 130
