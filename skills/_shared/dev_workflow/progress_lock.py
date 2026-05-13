"""POSIX advisory lock for progress.md mutations.

Phase 5 commands that mutate progress.md (``init`` / ``update`` /
``recover`` / ``release-*`` / ``bug-*`` / ``incident-*``) must serialize
through a single advisory lock so concurrent runs cannot interleave a
state-machine transition.

The lock file lives at ``<root>/.progress.lock`` and is held via
``fcntl.flock`` (Linux/macOS). Read-only commands (``query``) do not lock.

This helper only provides the lock primitive; per-command atomic write
discipline (backup → tmp → rename) is still owned by
``skills._shared.dev_workflow.atomic``.
"""

from __future__ import annotations

from contextlib import contextmanager
import errno
import fcntl
import os
import time
from pathlib import Path
from typing import Iterator


LOCK_FILENAME = ".progress.lock"


class ProgressLockError(RuntimeError):
    """Raised when the progress lock cannot be acquired in time."""


@contextmanager
def progress_lock(
    root: str | Path,
    *,
    timeout: float = 5.0,
    poll_interval: float = 0.05,
) -> Iterator[Path]:
    """Acquire the per-project ``.progress.lock`` exclusively.

    The lock uses ``fcntl.flock`` advisory locking. We poll non-blocking
    locks at ``poll_interval`` so the helper can honour ``timeout``
    deterministically and surface a clear ``ProgressLockError`` rather
    than blocking indefinitely.

    Yields the path of the lock file (mostly useful for tests).
    """

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    lock_path = root_path / LOCK_FILENAME

    deadline = time.monotonic() + max(timeout, 0.0)
    fd: int | None = None
    try:
        # Open / create the lock file for writing. Using O_RDWR avoids
        # truncating any pid hint we may write later; for now the file
        # contents are not load-bearing, but we keep the interface
        # forward-compatible.
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EACCES):
                    raise
                if time.monotonic() >= deadline:
                    raise ProgressLockError(
                        f"progress lock at {lock_path} is held by another process "
                        f"(timeout {timeout:.2f}s)"
                    ) from exc
                time.sleep(poll_interval)
        try:
            yield lock_path
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                # Best-effort unlock; closing the fd will release the
                # lock as well per fcntl(2) semantics.
                pass
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
