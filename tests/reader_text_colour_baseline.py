"""Narrow restoration for the authorized reader foreground-colour pass.

HTML restoration uses only fingerprinted, literal chunks recorded against the
frozen c6d5 baseline. Changed CSS/generated assets are accepted only by full
SHA-256 and can then be restored byte-for-byte for older historical checks.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRE_READER_TEXT_COMMIT = "c6d5a9cbf059570ad87b972c7b0fbffe7ed97801"
FIXTURE_PATH = ROOT / "tests/fixtures/reader-text-colour-edits.json"
FIXTURE_SHA256 = "2a14ddda16eeb0ecec8a44e6ab69a8d567c01b9cd04b6769e1008fff9598b906"
READER_TEXT_VERSION = "20261025-reader-colours-v1"
READER_TEXT_ASSET_SHA256 = {
    "start-here.css": "cbc36b830dbd7356a1c47a313775f6191b5a30b1539849fbd2ad776f42ff2793",
    "home-catalogue.css": "1f5d32d83d6230e5d37065bdce11894a30e3c93da6a1c8233130db420d52369d",
    "style.css": "92cd9efb1cd9f09294461e658e3289b658b0a3976dbe61fef2f55053c4f16c97",
    "tutorial-navigation.css": "725db31e5855afdb868a43d9ada12787fe76723657ca454be9e1ac89904cd3e8",
    "home-page.min.css": "c4bc6262003d9fdff311a02b0b8939adef7362d15ef970e7940796b729f838bc",
    "tools/generate_tutorial_ui.py": "f482d695b3820acc1ad9156c633dc977ff432afa4084ef9cec51bea5f215ed04",
}
READER_TEXT_ASSET_PATHS = frozenset(READER_TEXT_ASSET_SHA256)


def pre_reader_text_bytes(relative_path):
    """Return raw bytes from the immutable baseline for one authorized source."""
    if relative_path not in READER_TEXT_ASSET_PATHS and (
        not isinstance(relative_path, str) or not relative_path.endswith(".html")
        or relative_path.startswith("/") or ".." in Path(relative_path).parts
    ):
        raise AssertionError(f"not an authorized reader-text baseline path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{PRE_READER_TEXT_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _three_context_lines(before, after, label):
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    if min(len(old_lines), len(new_lines)) < 6:
        raise AssertionError(f"{label} needs three unchanged context lines on both sides")
    if old_lines[:3] != new_lines[:3] or old_lines[-3:] != new_lines[-3:]:
        raise AssertionError(f"{label} does not preserve its literal three-line context")


@lru_cache(maxsize=1)
def page_patches():
    """Validate fixture fingerprint, schema, exact unique chunks and c6d5 provenance."""
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"reader-text exact-fragment fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid reader-text exact-fragment fixture JSON") from exc
    files = fixture.get("files") if isinstance(fixture, dict) else None
    if (fixture.get("schema") != 1 or fixture.get("pre_reader_text_commit") != PRE_READER_TEXT_COMMIT
            or not isinstance(files, dict) or len(files) != 70):
        raise AssertionError("invalid reader-text fixture header or scope")
    validated = {}
    for relative_path, patches in files.items():
        if (not isinstance(relative_path, str) or not relative_path.endswith(".html")
                or not isinstance(patches, list) or not patches):
            raise AssertionError(f"invalid reader-text HTML fixture entry: {relative_path}")
        original = pre_reader_text_bytes(relative_path)
        if original is None:
            raise AssertionError(f"pinned reader-text source unavailable: {relative_path}")
        source = original.decode("utf-8")
        for index, patch in enumerate(patches):
            label = f"{relative_path} chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not all(isinstance(patch.get(key), str) and patch[key] for key in ("before", "after"))
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            _three_context_lines(patch["before"], patch["after"], label)
            count = source.count(patch["before"])
            if count != 1:
                raise AssertionError(f"{label} must occur exactly once in c6d5: found {count}")
            source = source.replace(patch["before"], patch["after"], 1)
        validated[relative_path] = patches
    return validated


def normalize_reader_text(relative_path, text):
    """Reverse only exact frozen HTML chunks; leave all unrecognized edits visible."""
    if not isinstance(text, str):
        raise TypeError("reader-text normalization requires decoded text")
    patches = page_patches().get(relative_path)
    if patches is None:
        return text
    for index, patch in reversed(list(enumerate(patches))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(f"duplicate exact reader-text patch chunk {index} in {relative_path}")
        if count == 1:
            text = text.replace(after, before, 1)
    return text


def verify_reader_text_file(relative_path, data):
    """Accept a modified asset only when its complete current bytes are pinned."""
    if relative_path not in READER_TEXT_ASSET_PATHS:
        raise AssertionError(f"not an authorized reader-text asset: {relative_path}")
    expected = READER_TEXT_ASSET_SHA256[relative_path]
    observed = hashlib.sha256(data).hexdigest()
    if observed != expected:
        raise AssertionError(f"reader-text asset fingerprint mismatch for {relative_path}: {observed}")
    return data


def restore_reader_text_asset(relative_path, data):
    """Verify an authorized asset and return its exact c6d5 bytes for older baselines."""
    verify_reader_text_file(relative_path, data)
    original = pre_reader_text_bytes(relative_path)
    if original is None:
        raise AssertionError(f"pinned reader-text asset unavailable: {relative_path}")
    return original
