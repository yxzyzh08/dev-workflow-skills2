"""Tests for skills/_shared/dev_workflow/progress_lock.py."""

from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from skills._shared.dev_workflow.progress_lock import (
    LOCK_FILENAME,
    ProgressLockError,
    progress_lock,
)


class ProgressLockBasicTests(unittest.TestCase):
    def test_acquire_creates_lock_file_and_releases_on_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with progress_lock(root, timeout=1.0) as lock_path:
                self.assertEqual(lock_path.name, LOCK_FILENAME)
                self.assertTrue(lock_path.exists())
            # File persists; lock is released, so a second acquisition is fine.
            with progress_lock(root, timeout=1.0):
                pass

    def test_creates_root_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "nested" / "project"
            self.assertFalse(root.exists())
            with progress_lock(root, timeout=1.0):
                self.assertTrue(root.exists())

    def test_second_acquire_in_same_process_via_subprocess_blocks(self):
        # fcntl.flock on the SAME process is reentrant in Linux, so simulate
        # cross-process contention with os.fork(). Skip on platforms where
        # fork is unavailable.
        if not hasattr(os, "fork"):
            self.skipTest("fork required for cross-process flock test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r, w = os.pipe()
            child = os.fork()
            if child == 0:  # child
                os.close(r)
                try:
                    with progress_lock(root, timeout=2.0):
                        os.write(w, b"locked\n")
                        time.sleep(0.5)
                    os._exit(0)
                except Exception:
                    os._exit(2)
            os.close(w)
            try:
                # Wait for child to grab the lock.
                self.assertEqual(os.read(r, 7), b"locked\n")
                with self.assertRaises(ProgressLockError):
                    with progress_lock(root, timeout=0.2):
                        self.fail("parent should not have acquired the lock")
            finally:
                os.close(r)
                os.waitpid(child, 0)

    def test_timeout_raises_progress_lock_error(self):
        if not hasattr(os, "fork"):
            self.skipTest("fork required for cross-process flock test")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r, w = os.pipe()
            child = os.fork()
            if child == 0:
                os.close(r)
                try:
                    with progress_lock(root, timeout=2.0):
                        os.write(w, b"go\n")
                        time.sleep(0.4)
                    os._exit(0)
                except Exception:
                    os._exit(2)
            os.close(w)
            try:
                self.assertEqual(os.read(r, 3), b"go\n")
                start = time.monotonic()
                with self.assertRaises(ProgressLockError):
                    with progress_lock(root, timeout=0.1):
                        pass
                elapsed = time.monotonic() - start
                self.assertLess(elapsed, 0.5, f"timeout took {elapsed:.2f}s")
            finally:
                os.close(r)
                os.waitpid(child, 0)


class ProgressLockReentryTests(unittest.TestCase):
    def test_serial_threads_in_same_process_can_acquire_sequentially(self):
        # Same-process fcntl.flock is not strictly serialising, but our
        # context manager opens a fresh fd each time so sequential acquires
        # must not raise. This documents that behaviour.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for _ in range(3):
                with progress_lock(root, timeout=0.5):
                    pass


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
