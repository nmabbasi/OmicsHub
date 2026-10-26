"""Exact regression adapter for the frozen 2026-10-25 tutorial execution delta.

This layer is intentionally independent of the immutable R-first fixture. It
reverses only individually pinned page bytes and literal-context hunks, and it
recognizes assets only by explicit path and complete-file SHA-256.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "122bd466feb11efd304769faff19e77bd40a98b4"
FIXTURE_PATH = ROOT / "tests/fixtures/tutorial-execution-exact-delta.json"
FIXTURE_SHA256 = "8d0c9125c92830f9b0f47fa956a593bf42da25db22093342d4064b72eaa42240"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


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
    if prefix + suffix < 3:
        raise AssertionError(f"{label} lacks three unchanged literal context lines")


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid execution-delta path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


@lru_cache(maxsize=1)
def _fixture():
    raw = FIXTURE_PATH.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256) or _sha(raw) != FIXTURE_SHA256:
        raise AssertionError(f"execution-delta fixture fingerprint mismatch: {_sha(raw)}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid execution-delta fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT):
        raise AssertionError("invalid execution-delta fixture header")

    pages = fixture.get("pages")
    assets = fixture.get("overlapping_assets")
    new_assets = fixture.get("new_assets")
    date_paths = fixture.get("date_modified_paths")
    if not isinstance(pages, list) or len(pages) != 58:
        raise AssertionError("execution-delta page scope must contain the explicit 58-page list")
    if not isinstance(assets, list) or not isinstance(new_assets, list) or len(new_assets) != 14:
        raise AssertionError("execution-delta asset scope is invalid")
    if date_paths != [
            "tutorials/r-tidyverse-fundamentals.html",
            "tutorials/wes-variant-calling-pipeline.html"]:
        raise AssertionError("execution-delta date exception list is invalid")
    seen = set()
    for entry in pages:
        if (not isinstance(entry, dict) or set(entry) != {
                "path", "current_sha256", "base_sha256", "patches"}):
            raise AssertionError("invalid execution-delta page entry")
        path = entry["path"]
        if (not isinstance(path, str) or not path.startswith("tutorials/")
                or not path.endswith(".html") or path in seen):
            raise AssertionError(f"invalid or duplicate execution-delta page path: {path!r}")
        seen.add(path)
        if not re.fullmatch(r"[0-9a-f]{64}", entry["current_sha256"]):
            raise AssertionError(f"invalid current page digest for {path}")
        if not re.fullmatch(r"[0-9a-f]{64}", entry["base_sha256"]):
            raise AssertionError(f"invalid base page digest for {path}")
        if not isinstance(entry["patches"], list) or not entry["patches"]:
            raise AssertionError(f"execution-delta page requires literal hunks: {path}")
        for patch in entry["patches"]:
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch["before"], str)
                    or not isinstance(patch["after"], str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid literal hunk in {path}")
            _three_line_context(patch["before"], patch["after"], path)

    def validate_assets(entries, label, require_base):
        paths = set()
        for entry in entries:
            expected_keys = {"path", "current_sha256"}
            if require_base:
                expected_keys.add("base_sha256")
            if not isinstance(entry, dict) or set(entry) != expected_keys:
                raise AssertionError(f"invalid {label} asset entry")
            path = entry["path"]
            if not isinstance(path, str) or path in paths or path in seen:
                raise AssertionError(f"invalid or duplicate {label} asset path: {path!r}")
            paths.add(path)
            for digest_key in expected_keys - {"path"}:
                if not isinstance(entry[digest_key], str) or not re.fullmatch(
                        r"[0-9a-f]{64}", entry[digest_key]):
                    raise AssertionError(f"invalid {label} digest for {path}")
        return paths

    overlapping_paths = validate_assets(assets, "overlapping", True)
    new_paths = validate_assets(new_assets, "new", False)
    fixture["page_map"] = {entry["path"]: entry for entry in pages}
    fixture["overlapping_asset_map"] = {entry["path"]: entry for entry in assets}
    fixture["new_asset_map"] = {entry["path"]: entry for entry in new_assets}
    if overlapping_paths & new_paths:
        raise AssertionError("overlapping and new asset scopes must remain disjoint")
    return fixture


def normalize_execution_delta(relative_path, text):
    """Reverse one exact current page to 122bd bytes; leave mutations untouched."""
    if not isinstance(text, str):
        raise TypeError("execution-delta normalization requires decoded text")
    from navigation_performance_baseline import normalize_navigation_performance
    text = normalize_navigation_performance(relative_path, text)
    from latest_review_baseline import latest_review_fixture, normalize_latest_review
    latest = latest_review_fixture().get(relative_path)
    if latest is not None and _sha(text.encode('utf-8')) == latest['current_sha256']:
        text = normalize_latest_review(relative_path, text)
    entry = _fixture()["page_map"].get(relative_path)
    if entry is None:
        return text
    raw = text.encode("utf-8")
    if _sha(raw) == entry["base_sha256"]:
        return text
    if _sha(raw) != entry["current_sha256"]:
        return text
    for index, patch in reversed(list(enumerate(entry["patches"]))):
        before, after = patch["before"], patch["after"]
        count = text.count(before)
        if count != 1:
            raise AssertionError(
                f"execution-delta literal hunk {index} is not unique in {relative_path}"
            )
        text = text.replace(before, after, 1)
    if _sha(text.encode("utf-8")) != entry["base_sha256"]:
        raise AssertionError(f"execution-delta restoration mismatch for {relative_path}")
    return text


def verify_new_execution_asset(relative_path, data):
    """Verify a newly introduced asset by explicit path and complete digest."""
    entry = _fixture()["new_asset_map"].get(relative_path)
    if entry is None:
        raise AssertionError(f"not an authorized new execution asset: {relative_path}")
    observed = _sha(data)
    if observed != entry["current_sha256"]:
        raise AssertionError(f"execution asset fingerprint mismatch for {relative_path}: {observed}")
    return data


def restore_overlapping_execution_asset(relative_path, data):
    """Return exact 122bd bytes for an overlapping asset only at its pinned digest."""
    from startup_performance_baseline import restore_startup_performance_asset
    data = restore_startup_performance_asset(relative_path, data)
    if relative_path == "sitemap.xml":
        # The newest review is a text-delta layer over the execution snapshot.
        # Compose it here only for its exact current whole-file pin; partial
        # mutations stay byte-for-byte visible to the caller's older row guards.
        from latest_review_baseline import latest_review_fixture, normalize_latest_review
        latest = latest_review_fixture().get(relative_path)
        if latest is not None and _sha(data) == latest["current_sha256"]:
            data = normalize_latest_review(relative_path, data.decode("utf-8")).encode("utf-8")
    entry = _fixture()["overlapping_asset_map"].get(relative_path)
    if entry is None:
        return data
    observed = _sha(data)
    if observed == entry["base_sha256"]:
        return data
    if observed != entry["current_sha256"]:
        return data
    original = _base_bytes(relative_path)
    if original is None or _sha(original) != entry["base_sha256"]:
        raise AssertionError(f"pinned execution asset baseline unavailable: {relative_path}")
    return original


def verify_execution_asset_or_overlapping(relative_path, data):
    """Verify either one exact new asset or one exact overlapping asset revision."""
    from latest_review_baseline import restore_latest_review_asset
    original_data = data
    data = restore_latest_review_asset(relative_path, data)
    fixture = _fixture()
    new = fixture["new_asset_map"].get(relative_path)
    if new is not None:
        verify_new_execution_asset(relative_path, data)
        return original_data
    overlap = fixture["overlapping_asset_map"].get(relative_path)
    if overlap is not None:
        observed = _sha(data)
        if observed == overlap["current_sha256"]:
            return original_data
        if observed == overlap["base_sha256"]:
            return original_data
        raise AssertionError(f"execution asset fingerprint mismatch for {relative_path}: {observed}")
    raise AssertionError(f"not an authorized execution asset: {relative_path}")


def new_execution_asset_paths():
    return frozenset(_fixture()["new_asset_map"])


def overlapping_execution_asset_paths():
    return frozenset(_fixture()["overlapping_asset_map"])


def execution_date_paths():
    return frozenset(_fixture()["date_modified_paths"])
