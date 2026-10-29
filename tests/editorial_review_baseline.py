"""Exact editorial-review restoration for historical source-scope tests.

This layer reverses only reviewed literal chunks on nine explicit public paths,
proved against the immutable deployed-main commit. It is intentionally applied
before every older baseline adapter; unmatched edits remain visible.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
from coffee_removal_baseline import (
    restore_coffee_removal_bytes,
    restore_coffee_removal_text,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "e846ce3fb6053ed611dc87fc62748865499913d0"
FIXTURE_PATH = ROOT / "tests/fixtures/editorial-review-edits.json"
FIXTURE_SHA256 = "40b70db4d6dd10bd5b2ddcd73c94027063ef7f476fa85adf7b23f69f5fef0995"
PUBLIC_PATHS = frozenset({
    "autonomous-research-orchestrator.html",
    "tools/generate_legacy_redirects.py",
    "tools/legacy-redirects.json",
    "tutorials.html",
    "tutorials/advanced-ai-orchestration-bioinformatics.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/modern-bioinformatics-methods-2026.html",
    "tutorials/scrna-seq-trajectory-inference.html",
})


def _base_bytes(relative_path):
    if relative_path not in PUBLIC_PATHS:
        raise AssertionError(f"unapproved editorial-review path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"deployed-main editorial base unavailable: {relative_path}")
    return result.stdout


def _check_context(before, after, label, at_file_start=False, at_file_end=False):
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    prefix = 0
    for old, new in zip(old_lines, new_lines):
        if old != new:
            break
        prefix += 1
    suffix = 0
    for old, new in zip(reversed(old_lines[prefix:]), reversed(new_lines[prefix:])):
        if old != new:
            break
        suffix += 1
    if ((prefix < 3 and not at_file_start)
            or (suffix < 3 and not at_file_end)
            or (prefix == 0 and suffix == 0)):
        raise AssertionError(f"{label} lacks three unchanged context lines")


@lru_cache(maxsize=1)
def editorial_review_fixture():
    """Validate the frozen fixture, its closed path scope, and every exact edit."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("editorial-review fixture is not frozen")
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"editorial-review fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AssertionError("invalid editorial-review fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != PUBLIC_PATHS):
        raise AssertionError("invalid editorial-review fixture header or exact path scope")
    validated = {}
    for relative_path, entry in fixture["files"].items():
        if not isinstance(entry, dict) or entry.get("kind") != "text" or set(entry) != {
            "kind", "base_sha256", "current_sha256", "patches"
        }:
            raise AssertionError(f"invalid editorial-review record: {relative_path}")
        base = _base_bytes(relative_path)
        if hashlib.sha256(base).hexdigest() != entry.get("base_sha256"):
            raise AssertionError(f"deployed-main base hash mismatch: {relative_path}")
        current_hash = entry.get("current_sha256")
        if not isinstance(current_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", current_hash):
            raise AssertionError(f"invalid current hash: {relative_path}")
        try:
            reconstructed = base.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(f"editorial base is not UTF-8: {relative_path}") from exc
        patches = entry.get("patches")
        if not isinstance(patches, list) or not patches:
            raise AssertionError(f"editorial record requires exact chunks: {relative_path}")
        for index, patch in enumerate(patches):
            label = f"{relative_path} editorial chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not all(isinstance(patch.get(k), str) for k in ("before", "after"))
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            before, after = patch["before"], patch["after"]
            count = reconstructed.count(before)
            if count != 1:
                raise AssertionError(f"{label} must occur exactly once in pinned base (found {count})")
            offset = reconstructed.find(before)
            _check_context(
                before, after, label,
                at_file_start=offset == 0,
                at_file_end=offset + len(before) == len(reconstructed),
            )
            if reconstructed.count(after) > 1:
                raise AssertionError(f"duplicate after-chunk in pinned base: {label}")
            reconstructed = reconstructed.replace(before, after, 1)
        if hashlib.sha256(reconstructed.encode("utf-8")).hexdigest() != current_hash:
            raise AssertionError(f"chunks do not reconstruct the reviewed source: {relative_path}")
        validated[relative_path] = {
            **entry, "patches": patches, "base_bytes": base,
        }
    return validated


def normalize_editorial_review(relative_path, text):
    """Reverse only exact fixture chunks; unknown changes stay visible."""
    if not isinstance(text, str):
        raise TypeError("editorial-review normalization requires decoded text")
    # The coffee-review adapter runs first so every older fixture sees the
    # immutable be4429d source. Unknown source edits pass through untouched.
    text = restore_coffee_removal_text(relative_path, text, strict=False)
    entry = editorial_review_fixture().get(relative_path)
    if entry is None:
        return text
    restored = text
    for index, patch in reversed(list(enumerate(entry["patches"]))):
        after, before = patch["after"], patch["before"]
        count = restored.count(after)
        if count > 1:
            raise AssertionError(
                f"duplicate exact editorial-review chunk {index} in {relative_path}"
            )
        if count == 1:
            restored = restored.replace(after, before, 1)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["current_sha256"]:
        if hashlib.sha256(restored.encode("utf-8")).hexdigest() != entry["base_sha256"]:
            raise AssertionError(f"exact editorial-review restoration failed: {relative_path}")
    return restored


def normalize_editorial_review_bytes(relative_path, data):
    """Byte-preserving adapter for text assets; never treats a directory as scope."""
    if not isinstance(data, bytes):
        raise TypeError("editorial-review byte normalization requires bytes")
    data = restore_coffee_removal_bytes(relative_path, data, strict=False)
    if relative_path not in PUBLIC_PATHS:
        return data
    try:
        return normalize_editorial_review(relative_path, data.decode("utf-8")).encode("utf-8")
    except UnicodeDecodeError:
        return data
