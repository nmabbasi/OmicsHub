"""Exact normalization layer for the Phase B Tier 1 rebuilds and AI/Python upgrades.

Peels only the 12 Phase B tutorial revisions and 3 generated UI metadata assets
back to commit d4ebce4552c6f09805d8a38515a80344c181a895 so older historical
fixtures continue to validate their original published revisions unchanged.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "d4ebce4552c6f09805d8a38515a80344c181a895"
FIXTURE_PATH = ROOT / "tests/fixtures/phase-b-fixes-2026-11.json"
FIXTURE_SHA256 = "0285a47aa2ffbe828afd408a2fcb9d67c730efcf150178076e6b1ce844a80ede"
PAGE_PATHS = (
    "tutorials/advanced-ai-orchestration-bioinformatics.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/mcp-zotero.html",
    "tutorials/modern-bioinformatics-methods-2026.html",
    "tutorials/protein-structure-design-alphafold.html",
    "tutorials/python-fundamentals-bioinformatics.html",
    "tutorials/reproducible-project-structure.html",
    "tutorials/scrna-seq-downstream-analysis.html",
    "tutorials/scrna-seq-quality-control.html",
    "tutorials/single-cell-foundation-models.html",
)
ASSET_PATHS = (
    "tools/tutorial-code-groups.json",
    "tools/tutorial-code-languages.json",
    "tutorial-code-data.js",
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid phase-b baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _three_line_context(before, after, label, at_start=False, at_end=False):
    old = before.splitlines(keepends=True)
    new = after.splitlines(keepends=True)
    prefix = 0
    while prefix < min(len(old), len(new)) and old[prefix] == new[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < min(len(old) - prefix, len(new) - prefix)
           and old[-1 - suffix] == new[-1 - suffix]):
        suffix += 1
    if (prefix < 3 and not at_start) or (suffix < 3 and not at_end):
        raise AssertionError(f"{label} needs three unchanged context lines on each side")


@lru_cache(maxsize=1)
def _fixture():
    raw = FIXTURE_PATH.read_bytes()
    if _sha(raw) != FIXTURE_SHA256:
        raise AssertionError(f"phase-b fixture fingerprint mismatch: {_sha(raw)}")
    fixture = json.loads(raw)
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT):
        raise AssertionError("invalid phase-b fixture header")
    pages = fixture.get("pages")
    assets = fixture.get("assets")
    if not isinstance(pages, list) or tuple(x.get("path") for x in pages) != PAGE_PATHS:
        raise AssertionError("phase-b page scope is not exact")
    if not isinstance(assets, list) or tuple(x.get("path") for x in assets) != ASSET_PATHS:
        raise AssertionError("phase-b asset scope is not exact")

    page_map = {}
    for entry in pages:
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"phase-b base page unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file() or _sha(current_path.read_bytes()) != entry["current_sha256"]:
            raise AssertionError(f"phase-b current page fingerprint mismatch: {path}")
        text = current_path.read_text(encoding="utf-8")
        full_current = text
        for index, patch in enumerate(entry["patches"]):
            pos = full_current.find(patch["before"])
            _three_line_context(
                patch["before"],
                patch["after"],
                f"{path} hunk {index}",
                at_start=(pos == 0),
                at_end=(pos + len(patch["before"]) == len(full_current)),
            )
        for patch in reversed(entry["patches"]):
            if text.count(patch["before"]) != 1:
                raise AssertionError(f"phase-b hunk is not unique in {path}")
            text = text.replace(patch["before"], patch["after"], 1)
        if _sha(text.encode("utf-8")) != entry["base_sha256"]:
            raise AssertionError(f"phase-b page restoration mismatch: {path}")
        page_map[path] = entry

    asset_map = {}
    for entry in assets:
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"phase-b base asset unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file() or _sha(current_path.read_bytes()) != entry["current_sha256"]:
            raise AssertionError(f"phase-b current asset fingerprint mismatch: {path}")
        asset_map[path] = entry

    fixture["page_map"] = page_map
    fixture["asset_map"] = asset_map
    return fixture


def normalize_phase_b_fix(relative_path, text):
    """Reverse one exact Phase B page revision; preserve unknown mutations."""
    if not isinstance(text, str):
        raise TypeError("phase-b normalization requires decoded text")
    entry = _fixture()["page_map"].get(relative_path)
    if entry is None:
        return text
    observed = _sha(text.encode("utf-8"))
    if observed == entry["base_sha256"]:
        return text
    if observed != entry["current_sha256"]:
        return text
    for index, patch in reversed(list(enumerate(entry["patches"]))):
        before, after = patch["before"], patch["after"]
        if text.count(before) != 1:
            raise AssertionError(f"phase-b hunk {index} is not unique in {relative_path}")
        text = text.replace(before, after, 1)
    if _sha(text.encode("utf-8")) != entry["base_sha256"]:
        raise AssertionError(f"phase-b restoration mismatch: {relative_path}")
    return text


def restore_phase_b_asset(relative_path, data):
    """Restore only an exact Phase B UI metadata asset to its d4ebce45 bytes."""
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
        raise AssertionError(f"phase-b base asset unavailable: {relative_path}")
    return original
