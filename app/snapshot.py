import hashlib
import os
import subprocess
import uuid
from typing import Optional, Iterable
import time

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
}

MAX_FILE_BYTES = 200_000  # safety cap for LLM context


def clone_repo(repo_url: str, retries: int = 3) -> str:
    """
    Clones the repo
    """
    session_id = str(uuid.uuid4())
    path = f"/tmp/safeagent/{session_id}"

    os.makedirs("/tmp/safeagent", exist_ok=True)

    for attempt in range(retries):
        try:
            subprocess.check_call(
                ["git", "clone", "--depth=1", repo_url, path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            return path

        except subprocess.CalledProcessError as e:
            if attempt == retries - 1:
                raise RuntimeError(
                    f"Git clone failed after {retries} attempts for {repo_url}: {e}"
                )
            time.sleep(1.5)


def hash_files(root: str) -> dict[str, str]:
    """Returns SHA256 hash of every readable file"""
    manifest = {}

    for rootdir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for f in files:
            full = os.path.join(rootdir, f)
            rel = full.replace(root + "/", "")

            try:
                with open(full, "rb") as fp:
                    manifest[rel] = hashlib.sha256(fp.read()).hexdigest()
            except Exception:
                # skip unreadable/binary files
                continue

    return manifest


def load_files(
    root: str,
    *,
    content: bool = True,
    include: Optional[Iterable[str]] = None,
    max_bytes: int = MAX_FILE_BYTES,
) -> dict[str, Optional[str]]:
    """
    Loads files from a repo.

    Modes:
    - content=False → return {path: None} for listing only
    - include=[...] → only load selected files
    - content=True → return actual file contents (UTF-8 safe)

    Always skips binary/unreadable files safely.
    """

    include_set = set(include) if include else None
    results = {}

    for rootdir, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for name in filenames:
            full = os.path.join(rootdir, name)
            rel = full.replace(root + "/", "")

            # Skip non-selected files if include filter is active
            if include_set and rel not in include_set:
                continue

            # Filename-only mode
            if not content:
                results[rel] = None
                continue

            # Content mode
            try:
                with open(full, "r", encoding="utf-8") as f:
                    results[rel] = f.read(max_bytes)
            except Exception:
                # skip binaries / unreadable
                continue

    return results
