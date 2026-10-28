"""Closed historical adapter for the exact coffee-anchor review delta.

Only the 69 HTML anchor deletions, the one legacy script.js anchor deletion,
and the homepage CSS source-fingerprint comment are recognized. Inputs must
match either the pinned be4429d base bytes or the complete expected reviewed
bytes; strict callers reject every other mutation. Production files are never
written or altered by this adapter.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
from gget_mobile_baseline import restore_gget_mobile_bytes

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "be4429d1ac4cfb0f2164239057cddd95c59620b1"
FIXTURE_PATH = ROOT / "tests/fixtures/coffee-removal-review.json"
FIXTURE_SHA256 = "6f359b70859c3728758d8c6a335a272961199de4b8f4c26f0647dbf0f5dcf461"
EXPECTED_HTML_COUNT = 69
EXPECTED_PATH_COUNT = EXPECTED_HTML_COUNT + 2


def _base_bytes(relative_path):
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned coffee-removal base unavailable: {relative_path}")
    return result.stdout


@lru_cache(maxsize=1)
def coffee_removal_fixture():
    """Verify the frozen manifest and both whole-file digests for every path."""
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"coffee-removal fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AssertionError("invalid coffee-removal fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or len(fixture["files"]) != EXPECTED_PATH_COUNT):
        raise AssertionError("invalid coffee-removal fixture header or path count")
    paths = set(fixture["files"])
    html_paths = {path for path in paths if path.endswith(".html")}
    if (len(html_paths) != EXPECTED_HTML_COUNT
            or paths != html_paths | {"script.js", "home-page.min.css"}
            or any(not isinstance(path, str) or path.startswith("/")
                   or "\\" in path or ".." in Path(path).parts
                   for path in paths)):
        raise AssertionError("coffee-removal fixture has an unapproved path scope")
    validated = {}
    for relative_path, entry in fixture["files"].items():
        if (not isinstance(entry, dict) or set(entry) != {
                "kind", "base_sha256", "current_sha256"}
                or entry.get("kind") != "source"):
            raise AssertionError(f"invalid coffee-removal record: {relative_path}")
        base_hash = entry.get("base_sha256")
        current_hash = entry.get("current_sha256")
        if (not isinstance(base_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", base_hash)
                or not isinstance(current_hash, str)
                or not re.fullmatch(r"[0-9a-f]{64}", current_hash)
                or base_hash == current_hash):
            raise AssertionError(f"invalid before/after digest: {relative_path}")
        base = _base_bytes(relative_path)
        if hashlib.sha256(base).hexdigest() != base_hash:
            raise AssertionError(f"pinned coffee-removal base digest mismatch: {relative_path}")
        validated[relative_path] = {
            "base_sha256": base_hash,
            "current_sha256": current_hash,
            "base_bytes": base,
        }
    return validated


def restore_coffee_removal_bytes(relative_path, data, *, strict=True):
    """Restore only the exact reviewed bytes, rejecting unrecognized edits.

    Unknown paths are outside this adapter's scope and pass through untouched.
    For one of the explicitly pinned paths, an exact base input is idempotent,
    an exact reviewed input maps to its base bytes, and every other input raises
    unless a layered historical helper explicitly opts into pass-through mode.
    """
    if not isinstance(data, bytes):
        raise TypeError("coffee-removal restoration requires bytes")
    data = restore_gget_mobile_bytes(relative_path, data)
    entry = coffee_removal_fixture().get(relative_path)
    if entry is None:
        return data
    observed = hashlib.sha256(data).hexdigest()
    if observed == entry["base_sha256"]:
        return data
    if observed != entry["current_sha256"]:
        if strict:
            raise AssertionError(
                f"unrecognized coffee-removal mutation in {relative_path}: {observed}"
            )
        return data
    restored = entry["base_bytes"]
    if hashlib.sha256(restored).hexdigest() != entry["base_sha256"]:
        raise AssertionError(f"coffee-removal before-digest check failed: {relative_path}")
    if hashlib.sha256(data).hexdigest() != entry["current_sha256"]:
        raise AssertionError(f"coffee-removal after-digest check failed: {relative_path}")
    return restored


def restore_coffee_removal_text(relative_path, text, *, strict=True):
    """UTF-8 text wrapper around the byte-exact historical adapter."""
    if not isinstance(text, str):
        raise TypeError("coffee-removal restoration requires decoded text")
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TypeError("coffee-removal restoration requires valid UTF-8 text") from exc
    return restore_coffee_removal_bytes(relative_path, data, strict=strict).decode("utf-8")
