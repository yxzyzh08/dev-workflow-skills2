"""Atomic file write and rollback helpers."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
import tempfile
from typing import Iterator


class AtomicWriteError(OSError):
    """Raised when an atomic transaction cannot be completed."""


def _fsync_parent(path: Path) -> None:
    """Fsync the parent directory so the rename/unlink is durable on Linux."""

    try:
        fd = os.open(path.parent, os.O_DIRECTORY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_text(path: str | Path, text: str, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    _fsync_parent(target)


def atomic_replace_from(path: str | Path, source: str | Path) -> None:
    """Atomically replace ``path`` with the contents of ``source`` (text or binary)."""

    target = Path(path)
    src = Path(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as out, src.open("rb") as inp:
            while True:
                chunk = inp.read(65536)
                if not chunk:
                    break
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    _fsync_parent(target)


@dataclass
class AtomicTransaction:
    """A simple all-or-nothing transaction for existing text files."""

    backup_dir: Path | None = None
    _backups: dict[Path, Path | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.backup_dir is None:
            self.backup_dir = Path(tempfile.mkdtemp(prefix="dev-workflow-backup-"))
        else:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, path: str | Path) -> None:
        target = Path(path)
        if target in self._backups:
            return
        if target.exists():
            assert self.backup_dir is not None
            backup_path = self.backup_dir / f"backup-{len(self._backups)}"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            atomic_replace_from(backup_path, target)
            self._backups[target] = backup_path
        else:
            self._backups[target] = None

    def write_text(self, path: str | Path, text: str, encoding: str = "utf-8") -> None:
        self.backup(path)
        atomic_write_text(path, text, encoding=encoding)

    def rollback(self) -> None:
        """Best-effort all-or-nothing rollback.

        Each target is processed independently so a single failing path cannot
        leave earlier targets unrestored. Errors are aggregated and re-raised
        as ``AtomicWriteError`` after every target has been attempted.
        """

        errors: list[tuple[Path, OSError]] = []
        for target, backup_path in reversed(list(self._backups.items())):
            try:
                if backup_path is None:
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        pass
                    else:
                        _fsync_parent(target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    atomic_replace_from(target, backup_path)
            except OSError as exc:
                errors.append((target, exc))
        if errors:
            details = "; ".join(f"{path}: {exc}" for path, exc in errors)
            raise AtomicWriteError(f"Rollback partially failed: {details}")

    def cleanup(self) -> None:
        if self.backup_dir is None or not self.backup_dir.exists():
            return
        # Remove the backup directory without depending on shutil; the directory
        # only contains regular files we created.
        for entry in sorted(self.backup_dir.iterdir(), reverse=True):
            try:
                entry.unlink()
            except OSError:
                # FileNotFoundError is an OSError subclass; OSError covers
                # missing-entry and permission-denied alike.
                pass
        try:
            self.backup_dir.rmdir()
        except OSError:
            pass


@contextmanager
def transaction() -> Iterator[AtomicTransaction]:
    tx = AtomicTransaction()
    try:
        yield tx
    except Exception as primary:
        try:
            tx.rollback()
        except Exception as rollback_exc:
            # Surface the rollback failure but chain the original error so the
            # caller sees both. The primary failure is what triggered rollback.
            raise rollback_exc from primary
        raise
    finally:
        tx.cleanup()
