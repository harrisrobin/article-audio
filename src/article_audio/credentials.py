import json
import os
import stat
from pathlib import Path

from .errors import UserError
from .files import atomic_write, file_lock, private_dir

GROUPS = {
    "gemini": ("GEMINI_API_KEY",),
    "r2": ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"),
}
ALLOWED = frozenset(key for group in GROUPS.values() for key in group)


class CredentialStore:
    def __init__(self, directory: Path | None = None):
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.directory = directory or Path(
            os.environ.get("ARTICLE_AUDIO_CONFIG_DIR", base / "article-audio")
        )
        self.path = self.directory / "credentials.json"

    def _read(self) -> dict[str, str]:
        if not self.path.exists() and not self.path.is_symlink():
            return {}
        private_dir(self.directory)
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, "r") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise UserError("Credential storage must be a regular file.", "unsafe_storage")
                if info.st_uid != os.getuid():
                    raise UserError(
                        "Credential file must be owned by your OS account.", "unsafe_storage"
                    )
                if stat.S_IMODE(info.st_mode) & 0o077:
                    raise UserError(
                        "Credential file must be private (mode 0600).", "unsafe_storage"
                    )
                if info.st_size > 65536:
                    raise ValueError
                values = json.load(stream)
            try:
                return self.validate(values)
            except UserError:
                raise ValueError from None
        except ValueError:
            raise UserError(
                "Saved credentials are damaged. Move credentials.json to a private backup in "
                "the same directory, then re-run auth setup for each provider.",
                "unsafe_storage",
            ) from None
        except OSError:
            raise UserError(
                "Cannot safely open credentials. Check ownership and permissions; "
                "remove symlinks rather than following them.",
                "unsafe_storage",
            ) from None

    @staticmethod
    def validate(values: object) -> dict[str, str]:
        if not isinstance(values, dict) or not values or set(values) - ALLOWED:
            raise UserError("Supply only the supported credential field names.")
        if any(
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 8192
            or any(ord(char) < 32 for char in value)
            for value in values.values()
        ):
            raise UserError("Credential values must be nonempty single-line strings.")
        return {key: value.strip() for key, value in values.items()}

    def get(self, key: str) -> str | None:
        value = os.environ.get(key)
        return value.strip() if value and value.strip() else self._read().get(key)

    def require(self, group: str) -> dict[str, str]:
        values = {key: self.get(key) for key in GROUPS[group]}
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise UserError(
                "Missing credentials: " + ", ".join(missing) + ". Run auth setup.",
                "credentials_required",
            )
        return {key: value for key, value in values.items() if value is not None}

    def status(self, group: str) -> dict:
        keys = GROUPS[group]
        present = [key for key in keys if self.get(key)]
        return {
            "group": group,
            "present": present,
            "missing": [key for key in keys if key not in present],
            "storage_path": str(self.path),
        }

    def save(self, values: dict[str, str]) -> None:
        values = self.validate(values)
        private_dir(self.directory)
        with file_lock(self.directory / ".credentials.lock"):
            combined = self._read() | values
            atomic_write(self.path, json.dumps(combined).encode())

    def import_environment(self, group: str) -> None:
        values = {key: os.environ.get(key, "") for key in GROUPS[group]}
        self.save(values)
