"""Newest exact normalization layer for the 2026-10-25 sitewide review.

The frozen fixture is intentionally not generated while source edits are in
progress. Once frozen, text changes are represented as unique literal chunks
with unchanged context; modified assets are restored only when their complete
current SHA-256 matches the fixture. Unknown text edits remain visible and
unknown asset bytes are returned unchanged.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "36bc46d"
FIXTURE_PATH = ROOT / "tests/fixtures/latest-review-edits.json"
# Refreshed only after SOURCES FINAL; malformed/empty means the layer remains
# dormant during active source work rather than inferring a baseline from it.
FIXTURE_SHA256 = "024b629b71452ef0de3f74764d0fe9659369ddeedfeef109cd515e9e1f00ea45"
FIXTURE_PATHS = frozenset({
    ".github/workflows/tutorial-review.yml", "home-page.min.css", "index.html",
    "script.js", "services.html", "sitemap.xml", "style.css", "tutorials.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/biological-data-formats.html", "tutorials/command-line-part1.html",
    "tutorials/command-line-part2.html", "tutorials/computer-data-fundamentals.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/evolutionary-phylogeny-analysis.html", "tutorials/git-github-bioinformatics.html",
    "tutorials/hpc-support.html", "tutorials/introduction-to-bioinformatics.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/metagenomics-assembly-mapping.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/notebooklm-research-brain.html",
    "tutorials/scrna-seq-basics.html",
    "tutorials/scrna-seq-integration-strategies.html",
    "tutorials/single-cell-foundation-models.html", "tutorials/wes-variant-calling-pipeline.html",
})


def _safe_relative_path(path):
    return (
        isinstance(path, str)
        and path
        and not path.startswith("/")
        and "\\" not in path
        and ".." not in Path(path).parts
    )


def _git_base_bytes(relative_path):
    if not _safe_relative_path(relative_path):
        raise AssertionError(f"unsafe latest-review fixture path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _check_context(before, after, label, at_file_start=False, at_file_end=False):
    """Require three unchanged lines at each available hunk boundary."""
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    prefix = 0
    for left, right in zip(old, new):
        if left != right:
            break
        prefix += 1
    suffix = 0
    for left, right in zip(reversed(old[prefix:]), reversed(new[prefix:])):
        if left != right:
            break
        suffix += 1
    # Hunk boundaries at the beginning/end of a file cannot have context on
    # that edge; elsewhere retain at least three unchanged lines.
    if (prefix < 3 and not at_file_start) or (suffix < 3 and not at_file_end):
        raise AssertionError(f"{label} lacks literal three-line context")
    if not prefix and not suffix:
        raise AssertionError(f"{label} has no unchanged hunk context")


def normalize_patch_chunks(text, patches, relative_path="<input>"):
    """Reverse exact chunks, rejecting duplicates and preserving unmatched edits."""
    if not isinstance(text, str):
        raise TypeError("latest-review text normalization requires decoded text")
    for index, patch in reversed(list(enumerate(patches))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(
                f"duplicate exact latest-review patch chunk {index} in {relative_path}"
            )
        if count == 1:
            text = text.replace(after, before, 1)
    return text


@lru_cache(maxsize=1)
def latest_review_fixture():
    """Load the hash-pinned fixture and prove every patch against 36bc46d."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("latest-review fixture is not frozen; await SOURCES FINAL")
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"latest-review fixture is unavailable: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"latest-review fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid latest-review fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != FIXTURE_PATHS):
        raise AssertionError("invalid latest-review fixture header or scope")
    validated = {}
    for relative_path, entry in fixture["files"].items():
        if not _safe_relative_path(relative_path) or not isinstance(entry, dict):
            raise AssertionError(f"invalid latest-review path or record: {relative_path!r}")
        kind = entry.get("kind")
        base = _git_base_bytes(relative_path)
        if base is None:
            raise AssertionError(f"pinned 36bc46d source unavailable: {relative_path}")
        if hashlib.sha256(base).hexdigest() != entry.get("base_sha256"):
            raise AssertionError(f"latest-review base hash mismatch: {relative_path}")
        current_hash = entry.get("current_sha256")
        if not isinstance(current_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", current_hash):
            raise AssertionError(f"invalid latest-review current hash: {relative_path}")
        if kind == "asset":
            if set(entry) != {"kind", "base_sha256", "current_sha256"}:
                raise AssertionError(f"invalid latest-review asset record: {relative_path}")
            validated[relative_path] = {**entry, "base_bytes": base}
            continue
        patches = entry.get("patches")
        if kind != "text" or set(entry) != {"kind", "base_sha256", "current_sha256", "patches"}:
            raise AssertionError(f"invalid latest-review text record: {relative_path}")
        if not isinstance(patches, list) or not patches:
            raise AssertionError(f"text record requires literal chunks: {relative_path}")
        reconstructed = base.decode("utf-8")
        for index, patch in enumerate(patches):
            label = f"{relative_path} fixture chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch["before"], str)
                    or not isinstance(patch["after"], str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            before = patch["before"]
            count = reconstructed.count(before)
            if count != 1:
                raise AssertionError(f"{label} must occur exactly once in 36bc46d: found {count}")
            position = reconstructed.find(before)
            _check_context(
                before, patch["after"], label,
                at_file_start=position == 0,
                at_file_end=position + len(before) == len(reconstructed),
            )
            reconstructed = reconstructed.replace(before, patch["after"], 1)
        if hashlib.sha256(reconstructed.encode("utf-8")).hexdigest() != current_hash:
            raise AssertionError(f"literal chunks do not reconstruct pinned review file: {relative_path}")
        validated[relative_path] = {**entry, "patches": patches, "base_bytes": base}
    return validated


def normalize_latest_review(relative_path, text):
    """Reverse only fixture-listed literal changes; leave unknown edits visible."""
    if not isinstance(text, str):
        raise TypeError("latest-review text normalization requires decoded text")
    # While owners are still editing, the deliberately empty hash disables this
    # layer. The frozen manifest and pin are committed together after finalization.
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        return text
    entry = latest_review_fixture().get(relative_path)
    if entry is None or entry["kind"] != "text":
        return text
    restored = normalize_patch_chunks(text, entry["patches"], relative_path)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["current_sha256"]:
        if hashlib.sha256(restored.encode("utf-8")).hexdigest() != entry["base_sha256"]:
            raise AssertionError(f"exact latest-review restoration failed: {relative_path}")
    return restored


def restore_latest_review_asset(relative_path, data):
    """Restore any reviewed file only for its exact complete current SHA-256 pin."""
    if not isinstance(data, bytes):
        raise TypeError("latest-review asset restoration requires bytes")
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        return data
    entry = latest_review_fixture().get(relative_path)
    if entry is None:
        return data
    if hashlib.sha256(data).hexdigest() != entry["current_sha256"]:
        return data
    if hashlib.sha256(entry["base_bytes"]).hexdigest() != entry["base_sha256"]:
        raise AssertionError(f"latest-review asset base verification failed: {relative_path}")
    return entry["base_bytes"]
