import fcntl
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .errors import UserError


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
