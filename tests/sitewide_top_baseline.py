"""Exact reversible baseline adapter for shared sitewide top-control wiring.

Only the explicitly listed shared-script and 404-page changes are normalized.
Fixture chunks are literal three-line-context diffs against the published
fa26faa baseline; unrelated or altered text remains visible to old tests.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

from reader_text_colour_baseline import normalize_reader_text

ROOT = Path(__file__).resolve().parents[1]
SITEWIDE_TOP_BASELINE = "fa26faa8d20a31de1211652e8ebffcf99534b9a6"
FIXTURE_PATH = ROOT / "tests/fixtures/sitewide-top-review-edits.json"
FIXTURE_SHA256 = "893d2fb6c4715cce4c7021f7d3600edbecdae94d43c91a24fbdc4476e9ed6e33"
SITEWIDE_TOP_PATHS = frozenset({"subscribe-fab.js", "404.html"})


def _git_show(relative_path):
    if relative_path not in SITEWIDE_TOP_PATHS:
        raise AssertionError(f"not an authorized sitewide-top historical path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{SITEWIDE_TOP_BASELINE}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _validate_context(before, after, label, at_eof=False):
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    full_context = (min(len(old_lines), len(new_lines)) >= 6
                    and old_lines[-3:] == new_lines[-3:])
    eof_context = (at_eof and min(len(old_lines), len(new_lines)) >= 5
                   and old_lines[-2:] == new_lines[-2:])
    if (min(len(old_lines), len(new_lines)) < 6 and not eof_context
            or old_lines[:3] != new_lines[:3]
            or not (full_context or eof_context)):
        raise AssertionError(f"{label} does not preserve its literal three-line context")


@lru_cache(maxsize=1)
def sitewide_top_patches():
    """Load and validate the frozen exact-chunk fixture against fa26faa."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError(
            "Sitewide-top fixture pin not refreshed; run refresh-sitewide-top-baselines.py after freeze"
        )
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"sitewide-top fixture is not frozen yet: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"sitewide-top fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid sitewide-top fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("published_commit") != SITEWIDE_TOP_BASELINE
            or set(fixture.get("files", {})) != SITEWIDE_TOP_PATHS):
        raise AssertionError("invalid exact sitewide-top fixture header or scope")

    validated = {}
    for relative_path, patches in fixture["files"].items():
        if not isinstance(patches, list):
            raise AssertionError(f"fixture chunks must be a list for {relative_path}")
        original = _git_show(relative_path)
        if original is None:
            raise AssertionError(f"pinned fa26faa source unavailable for {relative_path}")
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
            _validate_context(before, after, label, at_eof=source.endswith(before))
            if source.count(before) != 1:
                raise AssertionError(f"{label} must occur exactly once in fa26faa")
            source = source.replace(before, after, 1)
        validated[relative_path] = patches
    return validated


def normalize_sitewide_top(relative_path, text):
    """Reverse only exact frozen chunks; unknown and mutated edits remain visible."""
    if not isinstance(text, str):
        raise TypeError("sitewide-top normalization requires decoded text")
    text = normalize_reader_text(relative_path, text)
    if relative_path not in SITEWIDE_TOP_PATHS:
        return text
    for index, patch in reversed(list(enumerate(sitewide_top_patches()[relative_path]))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(
                f"duplicate exact sitewide-top patch chunk {index} in {relative_path}"
            )
        if count == 1:
            text = text.replace(after, before, 1)
    return text
