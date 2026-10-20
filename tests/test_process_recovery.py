"""Real process interruption at seven publication boundaries, not power-loss tests."""

import json
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import unittest

from history_poc.store import History, verify_history

ROOT = Path(__file__).resolve().parents[1]

# Wrappers execute the real operation first, then let the parent send SIGKILL.
# No write, fsync, validation or rename is mocked away.
CHILD = """
import json
from pathlib import Path
import sys
from history_poc import store

stage, destination = sys.argv[1:]
fixture = json.loads(Path("fixtures/account_changes.json").read_text())
target = Path(destination)
original_write = store.durable_write
original_rename = Path.rename
original_sync = store.sync_directory

def checkpoint(name):
    if name == stage:
        print("READY", flush=True)
        sys.stdin.buffer.read(1)
        raise RuntimeError("Parent must kill the paused child")

def write(path, raw):
    original_write(path, raw)
    checkpoint("write:" + path.name)

def rename(path, destination):
    result = original_rename(path, destination)
    checkpoint("rename:" + Path(destination).name)
    return result

def sync(path):
    original_sync(path)
    if path == target and (target / "manifest.json").exists():
        checkpoint("published-directory-sync")

store.durable_write = write
Path.rename = rename
store.sync_directory = sync
store.build_history(fixture, target)
"""


class ProcessRecoveryTests(unittest.TestCase):
    def test_sigkill_at_each_publication_boundary(self):
        stages = (
            ("write:payload.zst", False),
            ("write:index.zst", False),
            ("write:manifest.pending", False),
            ("write:manifest.pending.sha256", False),
            ("rename:manifest.json.sha256", False),
            ("rename:manifest.json", True),
            ("published-directory-sync", True),
        )
        fixture = json.loads((ROOT / "fixtures/account_changes.json").read_text())
        for stage, published in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "history"
                child = subprocess.Popen(
                    [sys.executable, "-c", CHILD, stage, str(target)],
                    cwd=ROOT,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                try:
                    ready, _, _ = select.select([child.stdout], [], [], 10)
                    self.assertTrue(ready, f"Child failed to reach {stage}")
                    self.assertEqual(child.stdout.readline().strip(), "READY")
                    child.kill()
                    _, stderr = child.communicate(timeout=5)
                    self.assertEqual(child.returncode, -signal.SIGKILL, stderr)
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.communicate(timeout=5)
                    for stream in (child.stdin, child.stdout, child.stderr):
                        stream.close()
                if published:
                    reader = History(target)
                    self.assertEqual(
                        verify_history(reader, fixture), reader.manifest["version_count"]
                    )
                else:
                    with self.assertRaises(FileNotFoundError):
                        History(target)
