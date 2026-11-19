"""Exact normalization layer for the Nov 18, 2026 final tutorial polish.

Peels only the final-polish revision (rendered maths/inline code in place of raw
LaTeX/Markdown, hidden Services links, a removed duplicate paragraph, aligned
author/dateModified JSON-LD with LinkedIn sameAs, and bottom author cards) back
to commit c7c39cb6e9c785660f1f6b20a12ed980e2801555, so every older historical
fixture keeps validating its original published bytes unchanged.  Any byte
sequence other than the exact pinned current page is returned untouched, so
unknown mutations remain visible to the older baselines.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "c7c39cb6e9c785660f1f6b20a12ed980e2801555"
FIXTURE_PATH = ROOT / "tests/fixtures/final-polish-2026-11.json"
FIXTURE_SHA256 = "4bc71d574e62f25812cf5048d94826b56723f29ebca368ee3863852cf6caf412"
PAGE_COUNT = 58


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid final-polish baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _apply(text, patches, label):
    for index, patch in reversed(list(enumerate(patches))):
        if text.count(patch["before"]) != 1:
            raise AssertionError(f"final-polish hunk {index} is not unique in {label}")
        text = text.replace(patch["before"], patch["after"], 1)
    return text


@lru_cache(maxsize=1)
def _fixture():
    raw = FIXTURE_PATH.read_bytes()
    if _sha(raw) != FIXTURE_SHA256:
        raise AssertionError(f"final-polish fixture fingerprint mismatch: {_sha(raw)}")
    fixture = json.loads(raw)
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT):
        raise AssertionError("invalid final-polish fixture header")
    pages = fixture.get("pages")
    expected = sorted(f"tutorials/{p.name}" for p in (ROOT / "tutorials").glob("*.html"))
    if (not isinstance(pages, list) or len(pages) != PAGE_COUNT
            or [entry.get("path") for entry in pages] != expected):
        raise AssertionError("final-polish page scope is not exact")
    page_map = {}
    for entry in pages:
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get(key))):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"final-polish base page unavailable or changed: {path}")
        page_map[path] = entry
    return page_map


def pinned_paths():
    return tuple(_fixture())


def normalize_final_polish(relative_path, text):
    """Reverse the exact final-polish page revision; preserve unknown mutations."""
    if not isinstance(text, str):
        raise TypeError("final-polish normalization requires decoded text")
    from homepage_redesign_baseline import normalize_homepage_redesign
    text = normalize_homepage_redesign(relative_path, text)
    entry = _fixture().get(relative_path)
    if entry is None:
        return text
    observed = _sha(text.encode("utf-8"))
    if observed != entry["current_sha256"]:
        return text
    text = _apply(text, entry["patches"], relative_path)
    if _sha(text.encode("utf-8")) != entry["base_sha256"]:
        raise AssertionError(f"final-polish restoration mismatch: {relative_path}")
    return text


def normalize_final_polish_bytes(relative_path, data):
    """Byte wrapper used by readers that compare raw file bytes."""
    if not isinstance(data, bytes):
        raise TypeError("final-polish byte normalization requires bytes")
    if _fixture().get(relative_path) is None:
        return data
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return normalize_final_polish(relative_path, decoded).encode("utf-8")
