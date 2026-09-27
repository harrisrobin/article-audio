import fcntl
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .errors import UserError


def read_private_json(path: Path):
    if not path.exists() and not path.is_symlink():
        return None
    private_dir(path.parent)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise UserError("Private storage must be a regular file.", "unsafe_storage")
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise UserError(
                    "Private file must be owned by you with mode 0600.", "unsafe_storage"
                )
            if info.st_size > 65536:
                raise ValueError
            return json.load(stream)
    except OSError:
        raise UserError(
            "Cannot safely open private storage. Check paths and permissions.", "unsafe_storage"
        ) from None


def private_dir(path: Path) -> None:
    if path.is_symlink():
        raise UserError("Refusing a symlink as a private directory.", "unsafe_storage")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise UserError("Private directory must be owned by you with mode 0700.", "unsafe_storage")


def atomic_write(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise UserError("Refusing to replace a symlink.", "unsafe_storage")
    fd, name = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(name).unlink(missing_ok=True)


@contextmanager
def file_lock(path: Path):
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    except OSError:
        raise UserError(
            "Cannot safely open the job or credential lock.", "unsafe_storage"
        ) from None
    with os.fdopen(fd, "w") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise UserError(
                "Another process is using this job or credential store.", "busy"
            ) from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)
