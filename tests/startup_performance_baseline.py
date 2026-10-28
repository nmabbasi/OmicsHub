"""Newest exact normalization layer for the controlled startup-performance work.

Only the 58 frozen tutorial HTML paths and three explicitly named generator/runtime
assets are eligible. Text reversals use unique contextual literals; assets are
restored only for an exact complete-file digest match.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
from editorial_review_baseline import normalize_editorial_review, normalize_editorial_review_bytes
BASE_COMMIT = "93f06260550dbc91c0f020c24e1e2b00b7e017b5"
FIXTURE_PATH = ROOT / "tests/fixtures/startup-performance-edits.json"
# Set only after the deterministic fixture is generated and reviewed.
FIXTURE_SHA256 = "16ddc83bd6cb4fc831cc83e78989c9986818e4835457dd613b7426e9f3f7b25a"
TUTORIAL_PATHS = frozenset({
    "tutorials/16s-rrna-prokka-annotation.html",
    "tutorials/advanced-ai-orchestration-bioinformatics.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/advanced-visualization-packages.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/biological-data-formats.html",
    "tutorials/cell-cell-communication.html",
    "tutorials/cell-type-annotation-methods.html",
    "tutorials/cite-seq-wnn-multiomics.html",
    "tutorials/command-line-part1.html",
    "tutorials/command-line-part2.html",
    "tutorials/command-line-part3.html",
    "tutorials/computer-data-fundamentals.html",
    "tutorials/conda-mamba-part1.html",
    "tutorials/data-visualization-fundamentals.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/docker-singularity-bioinformatics.html",
    "tutorials/evolutionary-phylogeny-analysis.html",
    "tutorials/experimental-design-batch-effects.html",
    "tutorials/git-github-bioinformatics.html",
    "tutorials/hpc-basic-commands.html",
    "tutorials/hpc-connection.html",
    "tutorials/hpc-submission-part1.html",
    "tutorials/hpc-support.html",
    "tutorials/infercnv-copy-number-variation.html",
    "tutorials/introduction-to-bioinformatics.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/mcp-zotero.html",
    "tutorials/metagenomics-assembly-mapping.html",
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/metatranscriptomics-functional-pathways.html",
    "tutorials/metatranscriptomics-guide.html",
    "tutorials/modern-bioinformatics-methods-2026.html",
    "tutorials/notebooklm-research-brain.html",
    "tutorials/phylogenomics-orthofinder.html",
    "tutorials/protein-structure-design-alphafold.html",
    "tutorials/python-fundamentals-bioinformatics.html",
    "tutorials/quality-control-fundamentals.html",
    "tutorials/r-tidyverse-fundamentals.html",
    "tutorials/reference-genomes-annotation.html",
    "tutorials/reproducible-project-structure.html",
    "tutorials/reproducible-workflows-snakemake-nextflow.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/scrna-seq-basics.html",
    "tutorials/scrna-seq-downstream-analysis.html",
    "tutorials/scrna-seq-integration-strategies.html",
    "tutorials/scrna-seq-quality-control.html",
    "tutorials/scrna-seq-trajectory-inference.html",
    "tutorials/single-cell-deconvolution.html",
    "tutorials/single-cell-foundation-models.html",
    "tutorials/spatial-transcriptomics-r-python.html",
    "tutorials/statistics-for-bioinformatics.html",
    "tutorials/tcr-bcr-repertoire-analysis.html",
    "tutorials/transcriptomics-differential-expression.html",
    "tutorials/wes-variant-calling-pipeline.html",
})
ASSET_PATHS = frozenset({"code-tabs.js", "subscribe-fab.js", "tools/generate_tutorial_ui.py"})
FIXTURE_PATHS = TUTORIAL_PATHS | ASSET_PATHS


def _base_bytes(relative_path):
    if relative_path not in FIXTURE_PATHS:
        raise AssertionError(f"unapproved startup-performance path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"published startup-performance base unavailable: {relative_path}")
    return result.stdout


def normalize_patch_chunks(text, patches, relative_path="<input>"):
    """Reverse unique exact after-chunks, rejecting duplicates and leaving unknown edits."""
    if not isinstance(text, str):
        raise TypeError("startup-performance text normalization requires decoded text")
    for index, patch in reversed(list(enumerate(patches))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(
                f"duplicate exact startup-performance patch chunk {index} in {relative_path}"
            )
        if count == 1:
            text = text.replace(after, before, 1)
    return text


@lru_cache(maxsize=1)
def startup_performance_fixture():
    """Load the pinned fixture and prove its closed scope and every edit against the base."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("startup-performance fixture is not frozen")
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"startup-performance fixture is unavailable: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"startup-performance fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AssertionError("invalid startup-performance fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != FIXTURE_PATHS):
        raise AssertionError("invalid startup-performance fixture header or scope")

    validated = {}
    for relative_path, entry in fixture["files"].items():
        if not isinstance(entry, dict):
            raise AssertionError(f"invalid startup-performance record: {relative_path}")
        base = _base_bytes(relative_path)
        if (not isinstance(entry.get("base_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["base_sha256"])
                or hashlib.sha256(base).hexdigest() != entry["base_sha256"]):
            raise AssertionError(f"startup-performance base hash mismatch: {relative_path}")
        current_hash = entry.get("current_sha256")
        if not isinstance(current_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", current_hash):
            raise AssertionError(f"invalid startup-performance current hash: {relative_path}")

        if relative_path in ASSET_PATHS:
            if set(entry) != {"kind", "base_sha256", "current_sha256"} or entry.get("kind") != "asset":
                raise AssertionError(f"invalid startup-performance asset record: {relative_path}")
            validated[relative_path] = {**entry, "base_bytes": base}
            continue

        if (entry.get("kind") != "text"
                or set(entry) != {"kind", "base_sha256", "current_sha256", "patches"}
                or not isinstance(entry.get("patches"), list)
                or not entry["patches"]):
            raise AssertionError(f"invalid startup-performance text record: {relative_path}")
        try:
            reconstructed = base.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(f"startup-performance text base is not UTF-8: {relative_path}") from exc
        for index, patch in enumerate(entry["patches"]):
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch["before"], str)
                    or not isinstance(patch["after"], str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid startup-performance chunk {index}: {relative_path}")
            before, after = patch["before"], patch["after"]
            count = reconstructed.count(before)
            if count != 1:
                raise AssertionError(
                    f"startup-performance before chunk {index} must occur exactly once in base: "
                    f"{relative_path} (found {count})"
                )
            # Literal contexts must retain at least three unchanged lines on each
            # available edge; file-boundary hunks may omit context only there.
            old_lines, new_lines = before.splitlines(keepends=True), after.splitlines(keepends=True)
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
            offset = reconstructed.find(before)
            at_start = offset == 0
            at_end = offset + len(before) == len(reconstructed)
            if (prefix < 3 and not at_start) or (suffix < 3 and not at_end) or (prefix == 0 and suffix == 0):
                raise AssertionError(f"startup-performance chunk lacks three-line context: {relative_path}")
            after_count = reconstructed.count(after)
            if after_count > 1:
                raise AssertionError(f"duplicate startup-performance after chunk in base: {relative_path}")
            reconstructed = reconstructed.replace(before, after, 1)
        if hashlib.sha256(reconstructed.encode("utf-8")).hexdigest() != current_hash:
            raise AssertionError(f"startup-performance chunks do not reconstruct pinned source: {relative_path}")
        validated[relative_path] = {**entry, "patches": entry["patches"], "base_bytes": base}
    return validated


def normalize_startup_performance(relative_path, text):
    """Reverse only exact fixture-listed contextual changes; preserve unknown edits."""
    if not isinstance(text, str):
        raise TypeError("startup-performance text normalization requires decoded text")
    text = normalize_editorial_review(relative_path, text)
    entry = startup_performance_fixture().get(relative_path)
    if entry is None or entry["kind"] != "text":
        return text
    restored = normalize_patch_chunks(text, entry["patches"], relative_path)
    if hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["current_sha256"]:
        if hashlib.sha256(restored.encode("utf-8")).hexdigest() != entry["base_sha256"]:
            raise AssertionError(f"exact startup-performance restoration failed: {relative_path}")
    return restored


def restore_startup_performance_asset(relative_path, data):
    """Restore a listed asset only when its entire current SHA-256 matches."""
    if not isinstance(data, bytes):
        raise TypeError("startup-performance asset restoration requires bytes")
    data = normalize_editorial_review_bytes(relative_path, data)
    entry = startup_performance_fixture().get(relative_path)
    if entry is None or entry["kind"] != "asset":
        return data
    if hashlib.sha256(data).hexdigest() != entry["current_sha256"]:
        return data
    if hashlib.sha256(entry["base_bytes"]).hexdigest() != entry["base_sha256"]:
        raise AssertionError(f"startup-performance asset base verification failed: {relative_path}")
    return entry["base_bytes"]
