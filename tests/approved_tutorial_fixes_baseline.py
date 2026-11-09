"""Exact normalization for the owner-approved November 2026 tutorial fixes.

This newest layer peels only the three reviewed page revisions and two generated
code-inventory assets back to the current main commit. Older historical fixtures
remain unchanged and continue to validate their original published revisions.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "deee52570e14f131d49c26cd29c7e2002fcc297d"
FIXTURE_PATH = ROOT / "tests/fixtures/approved-tutorial-fixes-2026-11.json"
FIXTURE_SHA256 = "9a5195429c906bb40c00bf916cff149d610a0a40371f31beea142e665f05d100"
PAGE_PATHS = (
    "tutorials/git-github-bioinformatics.html",
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/tcr-bcr-repertoire-analysis.html",
)
ASSET_PATHS = (
    "tutorial-code-data.js",
    "tools/tutorial-code-languages.json",
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid approved-fix baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _three_line_context(before, after, label):
    old = before.splitlines(keepends=True)
    new = after.splitlines(keepends=True)
    prefix = 0
    while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(old) - prefix, len(new) - prefix)
           and old[-1 - suffix] == new[-1 - suffix]):
        suffix += 1
    if prefix < 3 or suffix < 3:
        raise AssertionError(f"{label} needs three unchanged context lines on each side")


@lru_cache(maxsize=1)
def _fixture():
    raw = FIXTURE_PATH.read_bytes()
    if _sha(raw) != FIXTURE_SHA256:
        raise AssertionError(f"approved tutorial-fix fixture fingerprint mismatch: {_sha(raw)}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid approved tutorial-fix fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT):
        raise AssertionError("invalid approved tutorial-fix fixture header")

    pages = fixture.get("pages")
    assets = fixture.get("assets")
    if not isinstance(pages, list) or tuple(x.get("path") for x in pages) != PAGE_PATHS:
        raise AssertionError("approved tutorial-fix page scope is not exact")
    if not isinstance(assets, list) or tuple(x.get("path") for x in assets) != ASSET_PATHS:
        raise AssertionError("approved tutorial-fix asset scope is not exact")

    page_map = {}
    for entry in pages:
        if not isinstance(entry, dict) or set(entry) != {
                "path", "current_sha256", "base_sha256", "patches"}:
            raise AssertionError("invalid approved tutorial-fix page entry")
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry[key], str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        if not isinstance(entry["patches"], list) or not entry["patches"]:
            raise AssertionError(f"approved page requires exact hunks: {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"approved-fix base page unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file() or _sha(current_path.read_bytes()) != entry["current_sha256"]:
            raise AssertionError(f"approved-fix current page fingerprint mismatch: {path}")
        text = current_path.read_text(encoding="utf-8")
        for index, patch in enumerate(entry["patches"]):
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch["before"], str)
                    or not isinstance(patch["after"], str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid approved-fix hunk {index} in {path}")
            _three_line_context(patch["before"], patch["after"], f"{path} hunk {index}")
        for patch in reversed(entry["patches"]):
            if text.count(patch["before"]) != 1:
                raise AssertionError(f"approved-fix hunk is not unique in {path}")
            text = text.replace(patch["before"], patch["after"], 1)
        if _sha(text.encode("utf-8")) != entry["base_sha256"]:
            raise AssertionError(f"approved-fix page restoration mismatch: {path}")
        page_map[path] = entry

    asset_map = {}
    for entry in assets:
        if not isinstance(entry, dict) or set(entry) != {"path", "current_sha256", "base_sha256"}:
            raise AssertionError("invalid approved tutorial-fix asset entry")
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry[key], str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"approved-fix base asset unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file() or _sha(current_path.read_bytes()) != entry["current_sha256"]:
            raise AssertionError(f"approved-fix current asset fingerprint mismatch: {path}")
        asset_map[path] = entry

    fixture["page_map"] = page_map
    fixture["asset_map"] = asset_map
    return fixture


def normalize_approved_tutorial_fix(relative_path, text):
    """Reverse one exact approved page revision; preserve unknown mutations."""
    if not isinstance(text, str):
        raise TypeError("approved tutorial-fix normalization requires decoded text")
    entry = _fixture()["page_map"].get(relative_path)
    if entry is None:
        return text
    raw = text.encode("utf-8")
    observed = _sha(raw)
    if observed == entry["base_sha256"]:
        return text
    if observed != entry["current_sha256"]:
        return text
    for index, patch in reversed(list(enumerate(entry["patches"]))):
        before, after = patch["before"], patch["after"]
        if text.count(before) != 1:
            raise AssertionError(f"approved tutorial-fix hunk {index} is not unique in {relative_path}")
        text = text.replace(before, after, 1)
    if _sha(text.encode("utf-8")) != entry["base_sha256"]:
        raise AssertionError(f"approved tutorial-fix restoration mismatch: {relative_path}")
    return text


def restore_approved_tutorial_fix_asset(relative_path, data):
    """Restore only an exact approved code-inventory asset to its main bytes."""
    entry = _fixture()["asset_map"].get(relative_path)
    if entry is None:
        return data
    observed = _sha(data)
    if observed == entry["base_sha256"]:
        return data
    if observed != entry["current_sha256"]:
        return data
    original = _base_bytes(relative_path)
    if original is None or _sha(original) != entry["base_sha256"]:
        raise AssertionError(f"approved tutorial-fix base asset unavailable: {relative_path}")
    return original


def approved_tutorial_fix_page_paths():
    return frozenset(_fixture()["page_map"])


def approved_tutorial_fix_asset_paths():
    return frozenset(_fixture()["asset_map"])
