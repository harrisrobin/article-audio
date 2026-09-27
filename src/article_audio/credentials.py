import json
import os
from pathlib import Path

from .errors import UserError
from .files import atomic_write, file_lock, private_dir, read_private_json

GROUPS = {
    "gemini": ("GEMINI_API_KEY",),
    "r2": ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"),
    "cloudflare": ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
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
        try:
            values = read_private_json(self.path)
            if values == {}:
                return {}
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
        return self._snapshot((key,))[key]

    def _snapshot(self, keys: tuple[str, ...]) -> dict[str, str | None]:
        environment = dict(os.environ)
        values = {key: environment.get(key, "").strip() for key in keys}
        saved = self._read() if not all(values.values()) else {}
        return {key: values[key] or saved.get(key) for key in keys}

    def snapshot(self, group: str) -> dict[str, str | None]:
        return self._snapshot(GROUPS[group])

    def require(self, group: str) -> dict[str, str]:
        values = self.snapshot(group)
        missing = [key for key, value in values.items() if not value]
        if missing:
            raise UserError(
                "Missing credentials: " + ", ".join(missing) + ". Run auth setup.",
                "credentials_required",
            )
        return {key: value for key, value in values.items() if value is not None}

    def status(self, group: str) -> dict:
        keys = GROUPS[group]
        values = self.snapshot(group)
        present = [key for key in keys if values[key]]
        return {
            "group": group,
            "present": present,
            "missing": [key for key in keys if key not in present],
            "storage_path": str(self.path),
        }

    def save(
        self,
        values: dict[str, str],
        *,
        remove_if_matches: dict[str, str | None] | None = None,
        if_absent: tuple[str, ...] = (),
        if_unchanged: dict[str, str | None] | None = None,
    ) -> bool:
        """Merge values; return whether conditional removal completed or was already absent."""
        values = self.validate(values) if values or not remove_if_matches else {}
        private_dir(self.directory)
        with file_lock(self.directory / ".credentials.lock"):
            current = self._read()
            environment = dict(os.environ)
            if any(current.get(key) or environment.get(key, "").strip() for key in if_absent) or (
                if_unchanged is not None
                and any(
                    (environment.get(key, "").strip() or current.get(key)) != value
                    for key, value in if_unchanged.items()
                )
            ):
                raise UserError(
                    "Credentials changed during setup; existing values were preserved.",
                    "credentials_changed",
                )
            combined = current | values
            removed = remove_if_matches is not None and all(
                current.get(key) in (None, value) for key, value in remove_if_matches.items()
            )
            if removed:
                for key in remove_if_matches:
                    combined.pop(key, None)
            atomic_write(self.path, json.dumps(combined).encode())
            return removed

    def import_environment(self, group: str) -> None:
        values = {key: os.environ.get(key, "") for key in GROUPS[group]}
        self.save(values)
