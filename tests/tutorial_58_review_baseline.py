"""Exact restoration layer for the owner-authorized 58-tutorial review fixes.

Only complete files at explicitly listed paths and exact SHA-256 digests are
restored. Any partial or unknown mutation remains visible to older guards.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "29ee0f0355503538dda39d5ceffb38bbe33f8318"
FIXTURE_PATH = ROOT / "tests/fixtures/tutorial-58-review-hashes.json"
FIXTURE_SHA256 = "b17af0d4ef727f61ff59e14bd75607dc0c6c15a563fe0b2a5f9f399adbd350fc"
REVIEW_PATHS = frozenset({
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/cell-cell-communication.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/tcr-bcr-repertoire-analysis.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/single-cell-deconvolution.html",
    "tutorials/16s-rrna-prokka-annotation.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/metatranscriptomics-functional-pathways.html",
    "tutorials/cite-seq-wnn-multiomics.html",
    "tutorials/hpc-submission-part1.html",
    "tutorials/mcp-zotero.html",
    "files/tutorial-examples/research-reporting-interpretation/research-reporting-workflow.Rmd",
    "tools/catalogue-learning.json",
    "tools/tutorial-code-groups.json",
    "tools/tutorial-code-languages.json",
    "tutorial-code-data.js",
})


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or "\\" in relative_path or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid 58-review path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned pre-review file unavailable: {relative_path}")
    return result.stdout


@lru_cache(maxsize=1)
def review_fixture():
    raw = FIXTURE_PATH.read_bytes()
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256) or _sha(raw) != FIXTURE_SHA256:
        raise AssertionError(f"58-review fixture fingerprint mismatch: {_sha(raw)}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid 58-review fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != REVIEW_PATHS):
        raise AssertionError("invalid 58-review fixture header or explicit path scope")
    validated = {}
    for relative_path, entry in fixture["files"].items():
        if not isinstance(entry, dict) or set(entry) != {"base_sha256", "current_sha256"}:
            raise AssertionError(f"invalid 58-review fixture record: {relative_path}")
        base = _base_bytes(relative_path)
        if not re.fullmatch(r"[0-9a-f]{64}", entry["base_sha256"]):
            raise AssertionError(f"invalid pre-review digest: {relative_path}")
        if _sha(base) != entry["base_sha256"]:
            raise AssertionError(f"pre-review source hash mismatch: {relative_path}")
        if (not re.fullmatch(r"[0-9a-f]{64}", entry["current_sha256"])
                or entry["current_sha256"] == entry["base_sha256"]):
            raise AssertionError(f"invalid review-result digest: {relative_path}")
        validated[relative_path] = {**entry, "base_bytes": base}
    return validated


def normalize_58_review(relative_path, text):
    """Restore one exact, complete review article; leave partial edits visible."""
    if not isinstance(text, str):
        raise TypeError("58-review normalization requires decoded text")
    entry = review_fixture().get(relative_path)
    if entry is None:
        return text
    current = text.encode("utf-8")
    if _sha(current) != entry["current_sha256"]:
        return text
    if _sha(entry["base_bytes"]) != entry["base_sha256"]:
        raise AssertionError(f"58-review source verification failed: {relative_path}")
    return entry["base_bytes"].decode("utf-8")


def restore_58_review_asset(relative_path, data):
    """Restore a listed supporting/generated asset only at its full exact hash."""
    if not isinstance(data, bytes):
        raise TypeError("58-review asset restoration requires bytes")
    entry = review_fixture().get(relative_path)
    if entry is None or _sha(data) != entry["current_sha256"]:
        return data
    if _sha(entry["base_bytes"]) != entry["base_sha256"]:
        raise AssertionError(f"58-review asset verification failed: {relative_path}")
    return entry["base_bytes"]
