"""Exact source adapter for the approved gget mobile table change.

Only the two full files changed by PR #32 are recognized. The pinned fixture
proves each exact diff against the immutable main commit; unknown edits stay
visible to every older scope guard.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

from navigation_guard_baseline import (
    restore_navigation_guard_asset,
    normalize_navigation_guard_text,
)
from current_publication_baseline import normalize_current_publication

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "0caaeabb050845dcb07905fc5bf99cd699866baa"
FIXTURE_PATH = ROOT / "tests/fixtures/gget-mobile-baseline.json"
FIXTURE_SHA256 = "0f26480bceb98d0d231b67b5fc96619b0f21dc3ab2feb7fc5454af73e4283d97"
APPROVED_PATHS = frozenset({
    "tutorial-library.css",
    "tutorials/deterministic-retrieval-gget-ai.html",
})


def _base_bytes(relative_path):
    if relative_path not in APPROVED_PATHS:
        raise AssertionError(f"unapproved gget mobile baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned gget mobile base unavailable: {relative_path}")
    return result.stdout


def _check_context(before, after, label, at_file_start=False, at_file_end=False):
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    prefix = 0
    for left, right in zip(old, new):
        if left != right:
            break
        prefix += 1
    suffix = 0
    for left, right in zip(reversed(old[prefix:]), reversed(new[prefix:])):
        if left != right:
            break
        suffix += 1
    if ((prefix < 3 and not at_file_start)
            or (suffix < 3 and not at_file_end)
            or (prefix == 0 and suffix == 0)):
        raise AssertionError(f"{label} lacks three unchanged context lines")


@lru_cache(maxsize=1)
def gget_mobile_fixture():
    """Verify the closed fixture, exact diffs, and both full-file hashes."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("gget mobile fixture is not frozen")
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"gget mobile fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AssertionError("invalid gget mobile fixture JSON") from exc
    if (not isinstance(fixture, dict) or set(fixture) != {"schema", "base_commit", "files"}
            or fixture.get("schema") != 1 or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != APPROVED_PATHS):
        raise AssertionError("invalid gget mobile fixture header or exact path scope")

    validated = {}
    for relative_path, entry in fixture["files"].items():
        if (not isinstance(entry, dict)
                or set(entry) != {"base_sha256", "current_sha256", "patches"}
                or not isinstance(entry.get("patches"), list)
                or not entry["patches"]):
            raise AssertionError(f"invalid gget mobile fixture entry: {relative_path}")
        base = _base_bytes(relative_path)
        base_sha = hashlib.sha256(base).hexdigest()
        if base_sha != entry.get("base_sha256"):
            raise AssertionError(f"gget mobile base hash mismatch: {relative_path}")
        current_sha = entry.get("current_sha256")
        if (not isinstance(current_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", current_sha)
                or current_sha == base_sha):
            raise AssertionError(f"invalid gget mobile current hash: {relative_path}")

        reconstructed = base.decode("utf-8")
        for index, patch in enumerate(entry["patches"]):
            label = f"{relative_path} chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch.get("before"), str)
                    or not isinstance(patch.get("after"), str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            before, after = patch["before"], patch["after"]
            if reconstructed.count(before) != 1:
                raise AssertionError(f"{label} must occur exactly once in pinned main")
            position = reconstructed.find(before)
            _check_context(
                before, after, label,
                at_file_start=position == 0,
                at_file_end=position + len(before) == len(reconstructed),
            )
            reconstructed = reconstructed.replace(before, after, 1)
        if hashlib.sha256(reconstructed.encode("utf-8")).hexdigest() != current_sha:
            raise AssertionError(f"exact chunks do not reconstruct PR #32 bytes: {relative_path}")
        validated[relative_path] = {
            "base_sha256": base_sha,
            "current_sha256": current_sha,
            "base_bytes": base,
        }
    return validated


def restore_gget_mobile_bytes(relative_path, data):
    """Restore only complete, exact PR #32 files; preserve all other bytes."""
    if not isinstance(data, bytes):
        raise TypeError("gget mobile restoration requires bytes")
    data = normalize_current_publication(relative_path, data)
    data = restore_navigation_guard_asset(relative_path, data)
    entry = gget_mobile_fixture().get(relative_path)
    if entry is None:
        return data
    observed = hashlib.sha256(data).hexdigest()
    if observed == entry["base_sha256"]:
        return data
    if observed == entry["current_sha256"]:
        return entry["base_bytes"]
    return data


def restore_gget_mobile_text(relative_path, text):
    """UTF-8 text wrapper around the exact full-file adapter."""
    if not isinstance(text, str):
        raise TypeError("gget mobile restoration requires decoded text")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TypeError("gget mobile restoration requires valid UTF-8 text") from exc
    return restore_gget_mobile_bytes(relative_path, data).decode("utf-8")
