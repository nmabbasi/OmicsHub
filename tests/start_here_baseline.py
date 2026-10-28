"""Exact, bounded normalization for the reviewed Start Here simplification.

The HTML adapter reverses only literal chunks recorded against the pre-review
page. It does not parse or discard a body, script, claim, or selector. New
standalone Start Here assets are independently byte-pinned once the page owner
finishes them; back-to-top.css remains pinned by tutorial_ui_baseline.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
from latest_review_baseline import normalize_latest_review
from start_here_desktop_baseline import (
    normalize_start_here_desktop_html, restore_start_here_desktop_asset,
)
from reader_text_colour_baseline import (
    READER_TEXT_ASSET_SHA256, normalize_reader_text, restore_reader_text_asset,
)

ROOT = Path(__file__).resolve().parents[1]
PRE_REVIEW_COMMIT = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
FIXTURE_PATH = ROOT / "tests/fixtures/start-here-review-edits.json"
# Exact reviewed HTML/sitemap chunks and final frozen asset digests; no broad normalization.
FIXTURE_SHA256 = "0e22504380045a5a8b2274cca0736fc7557fb87481a99458326708a7e07ee3fa"
# Replace None with the final SHA-256 pins after the owner-authored assets land.
START_HERE_ASSET_SHA256 = {
    "start-here.css": "cf4d37fa66592705203fffaa2924f9cc068c2bd24080778b0d115bed2ec73acd",
    "start-here.js": "e2102a67a41b7d14bf81a11aa1351c9d950ad8082b0eff02f1afbd1a7172f7c7",
}
START_HERE_ASSET_PATHS = frozenset(START_HERE_ASSET_SHA256)


def _three_context_lines_are_preserved(before, after, label):
    """Require literal three-line context on both sides of a changed chunk."""
    old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
    if min(len(old_lines), len(new_lines)) < 7:
        raise AssertionError(f"{label} must include three unchanged context lines on each side")
    if old_lines[:3] != new_lines[:3] or old_lines[-3:] != new_lines[-3:]:
        raise AssertionError(f"{label} does not preserve its literal three-line context")


@lru_cache(maxsize=1)
def page_patches():
    """Load the pinned fixture and prove its old chunks belong to the pinned source."""
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"cannot read Start Here review fixture: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256) or observed != FIXTURE_SHA256:
        raise AssertionError(
            "Start Here review fixture fingerprint mismatch or parent pin not refreshed: "
            + observed
        )
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid Start Here review fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("pre_review_commit") != PRE_REVIEW_COMMIT
            or set(fixture.get("files", {})) != {"start-here.html", "sitemap.xml"}):
        raise AssertionError("invalid exact Start Here review fixture header or scope")
    for relative_path, patches in fixture["files"].items():
        if not isinstance(patches, list) or not patches:
            raise AssertionError(f"Start Here fixture requires literal chunks for {relative_path}")
        original = pre_review_bytes(relative_path)
        if original is None:
            raise AssertionError(f"pinned pre-review source unavailable for {relative_path}")
        source = original.decode("utf-8")
        for index, patch in enumerate(patches):
            label = f"{relative_path} fixture chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch.get("before"), str)
                    or not isinstance(patch.get("after"), str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            before, after = patch["before"], patch["after"]
            _three_context_lines_are_preserved(before, after, label)
            if source.count(before) != 1:
                raise AssertionError(f"{label} must occur exactly once in the pinned pre-review source")
            source = source.replace(before, after, 1)
    return fixture["files"]


def pre_review_bytes(relative_path):
    """Return raw bytes for one path at the fixed pre-review commit, if present."""
    if relative_path not in {"start-here.html", "sitemap.xml", "start-here.css"}:
        raise AssertionError(f"not an authorized Start Here historical source: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{PRE_REVIEW_COMMIT}:{relative_path}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def normalize_start_here(relative_path, text):
    """Reverse exact reviewed chunks in start-here.html; leave every other byte alone."""
    if not isinstance(text, str):
        raise TypeError("Start Here normalization requires decoded text")
    text = normalize_latest_review(relative_path, text)
    text = normalize_start_here_desktop_html(relative_path, text)
    text = normalize_reader_text(relative_path, text)
    if relative_path != "start-here.html":
        return text
    for index, patch in reversed(list(enumerate(page_patches()["start-here.html"]))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(f"duplicate exact Start Here patch chunk {index}")
        if count == 1:
            text = text.replace(after, before, 1)
    return text


def normalize_start_here_sitemap(data):
    """Reverse only the fixture-pinned Start Here chunks in sitemap.xml."""
    as_text = isinstance(data, str)
    if not as_text and not isinstance(data, bytes):
        raise TypeError("Start Here sitemap normalization requires text or bytes")
    text = data if as_text else data.decode("utf-8")
    for index, patch in reversed(list(enumerate(page_patches()["sitemap.xml"]))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(f"duplicate exact Start Here sitemap patch chunk {index}")
        if count == 1:
            text = text.replace(after, before, 1)
    return text if as_text else text.encode("utf-8")


def verify_start_here_file(relative_path, data):
    """Verify an explicitly approved Start Here asset by its complete byte hash."""
    if relative_path not in START_HERE_ASSET_PATHS:
        raise AssertionError(f"not an authorized Start Here asset: {relative_path}")
    expected = START_HERE_ASSET_SHA256[relative_path]
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise AssertionError(f"parent must refresh the exact SHA-256 pin for {relative_path}")
    original_data = data
    if relative_path == "start-here.css":
        data = restore_start_here_desktop_asset(relative_path, data)
    if hashlib.sha256(data).hexdigest() == READER_TEXT_ASSET_SHA256.get(relative_path):
        data = restore_reader_text_asset(relative_path, data)
    observed = hashlib.sha256(data).hexdigest()
    if observed != expected:
        raise AssertionError(f"Start Here asset fingerprint mismatch for {relative_path}: {observed}")
    return original_data


def normalize_start_here_asset(relative_path, data):
    """Verify an exact Start Here asset; restore CSS, explicitly exempt new JS."""
    verify_start_here_file(relative_path, data)
    if relative_path == "start-here.css":
        original = pre_review_bytes(relative_path)
        if original is None:
            raise AssertionError("pinned pre-review Start Here CSS is unavailable")
        return original
    if relative_path == "start-here.js":
        return None
    raise AssertionError(f"not an authorized Start Here asset: {relative_path}")
