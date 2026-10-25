"""Exact compatibility for the approved 2026-10-25 Marked.js removals.

Only the 51 tutorial files listed below are eligible. A file is restored to
published-base bytes only when its complete current SHA-256 matches the frozen
after-hash and the fixture independently proves that deleting exactly the
listed literal block from the published-base bytes yields those bytes.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "991991f99455d921a2fbc688621681b3a2295e1d"
FIXTURE_PATH = ROOT / "tests/fixtures/navigation-performance-edits.json"
FIXTURE_SHA256 = "277de8705c999457309688e40ec4ebbaf0f939f49946a6bf89ffabcdffcc69af"
WORKFLOW_PATH = ".github/workflows/tutorial-review.yml"
APPROVED_PATHS = frozenset({
    "tutorials/16s-rrna-prokka-annotation.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/advanced-visualization-packages.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
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
    "tutorials/metagenomics-assembly-mapping.html",
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/metatranscriptomics-functional-pathways.html",
    "tutorials/metatranscriptomics-guide.html",
    "tutorials/modern-bioinformatics-methods-2026.html",
    "tutorials/phylogenomics-orthofinder.html",
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
    "tutorials/spatial-transcriptomics-r-python.html",
    "tutorials/statistics-for-bioinformatics.html",
    "tutorials/tcr-bcr-repertoire-analysis.html",
    "tutorials/transcriptomics-differential-expression.html",
    "tutorials/wes-variant-calling-pipeline.html",
})
FIXTURE_PATHS = APPROVED_PATHS | {WORKFLOW_PATH}


def _base_bytes(path):
    if path not in FIXTURE_PATHS:
        raise AssertionError(f"unapproved navigation-performance path: {path!r}")
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"published navigation-performance base unavailable: {path}")
    return result.stdout


@lru_cache(maxsize=1)
def navigation_performance_fixture():
    """Load the pinned 51-file manifest and verify each exact deletion."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("navigation-performance fixture is not frozen")
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"navigation-performance fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid navigation-performance fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT
            or not isinstance(fixture.get("files"), dict)
            or set(fixture["files"]) != FIXTURE_PATHS):
        raise AssertionError("invalid navigation-performance fixture header or scope")
    validated = {}
    for path, entry in fixture["files"].items():
        expected_keys = (
            {"removed_block", "before_sha256", "after_sha256"}
            if path in APPROVED_PATHS else
            {"added_after", "added_block", "before_sha256", "after_sha256"}
        )
        if set(entry) != expected_keys:
            raise AssertionError(f"invalid navigation-performance record: {path}")
        if path in APPROVED_PATHS:
            if not isinstance(entry["removed_block"], str) or not entry["removed_block"]:
                raise AssertionError(f"invalid removed block: {path}")
        elif (not isinstance(entry["added_after"], str) or not entry["added_after"]
              or not isinstance(entry["added_block"], str) or not entry["added_block"]):
            raise AssertionError(f"invalid workflow addition: {path}")
        for key in ("before_sha256", "after_sha256"):
            if not isinstance(entry[key], str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key}: {path}")
        before = _base_bytes(path)
        if hashlib.sha256(before).hexdigest() != entry["before_sha256"]:
            raise AssertionError(f"published-base hash mismatch: {path}")
        if path in APPROVED_PATHS:
            block_bytes = entry["removed_block"].encode("utf-8")
            if before.count(block_bytes) != 1:
                raise AssertionError(f"approved literal must occur exactly once in published base: {path}")
            after = before.replace(block_bytes, b"", 1)
        else:
            anchor = entry["added_after"].encode("utf-8")
            block_bytes = entry["added_block"].encode("utf-8")
            if before.count(anchor) != 1:
                raise AssertionError(f"workflow anchor must occur exactly once in published base: {path}")
            after = before.replace(anchor, anchor + block_bytes, 1)
        if hashlib.sha256(after).hexdigest() != entry["after_sha256"]:
            raise AssertionError(f"approved removal does not reconstruct pinned after bytes: {path}")
        validated[path] = {**entry, "before_bytes": before, "after_bytes": after}
    return validated


def normalize_navigation_performance(relative_path, text):
    """Restore published-base text only for an exact complete-file after hash."""
    if not isinstance(text, str):
        raise TypeError("navigation-performance normalization requires decoded text")
    return restore_navigation_performance_bytes(relative_path, text.encode("utf-8")).decode("utf-8")


def restore_navigation_performance_bytes(relative_path, data):
    """Byte-preserving form used by historical asset restorers."""
    if not isinstance(data, bytes):
        raise TypeError("navigation-performance byte restoration requires bytes")
    entry = navigation_performance_fixture().get(relative_path)
    if entry is None:
        return data
    current = data
    if hashlib.sha256(current).hexdigest() != entry["after_sha256"]:
        return data
    if current != entry["after_bytes"]:
        raise AssertionError(f"pinned navigation-performance bytes disagree: {relative_path}")
    return entry["before_bytes"]
