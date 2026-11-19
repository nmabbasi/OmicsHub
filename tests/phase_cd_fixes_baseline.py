"""Exact normalization layer for the Phase C & D tutorial depth and polish upgrades.

Peels only the 43 Phase C/D tutorial revisions and 3 generated UI metadata assets
back to commit 35ebb97cc8e23a185438a964e4530985afb15a94 so older historical
fixtures continue to validate their original published revisions unchanged.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "35ebb97cc8e23a185438a964e4530985afb15a94"
FIXTURE_PATH = ROOT / "tests/fixtures/phase-cd-fixes-2026-11.json"
FIXTURE_SHA256 = "360d63b916303ef58c02720eb4685ad69db1c01833cdcdb6b3e3cbfbf7d568d3"
PAGE_PATHS = (
    "start-here.html",
    "tutorials/16s-rrna-prokka-annotation.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/advanced-visualization-packages.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/biological-data-formats.html",
    "tutorials/cell-cell-communication.html",
    "tutorials/cell-type-annotation-methods.html",
    "tutorials/cite-seq-wnn-multiomics.html",
    "tutorials/command-line-part1.html",
    "tutorials/command-line-part2.html",
    "tutorials/conda-mamba-part1.html",
    "tutorials/data-visualization-fundamentals.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/docker-singularity-bioinformatics.html",
    "tutorials/evolutionary-phylogeny-analysis.html",
    "tutorials/experimental-design-batch-effects.html",
    "tutorials/git-github-bioinformatics.html",
    "tutorials/hpc-connection.html",
    "tutorials/hpc-submission-part1.html",
    "tutorials/hpc-support.html",
    "tutorials/infercnv-copy-number-variation.html",
    "tutorials/introduction-to-bioinformatics.html",
    "tutorials/metagenomics-assembly-mapping.html",
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/metatranscriptomics-functional-pathways.html",
    "tutorials/metatranscriptomics-guide.html",
    "tutorials/notebooklm-research-brain.html",
    "tutorials/phylogenomics-orthofinder.html",
    "tutorials/quality-control-fundamentals.html",
    "tutorials/r-tidyverse-fundamentals.html",
    "tutorials/reference-genomes-annotation.html",
    "tutorials/reproducible-workflows-snakemake-nextflow.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/scrna-seq-basics.html",
    "tutorials/scrna-seq-integration-strategies.html",
    "tutorials/scrna-seq-trajectory-inference.html",
    "tutorials/single-cell-deconvolution.html",
    "tutorials/spatial-transcriptomics-r-python.html",
    "tutorials/statistics-for-bioinformatics.html",
    "tutorials/tcr-bcr-repertoire-analysis.html",
    "tutorials/transcriptomics-differential-expression.html",
    "tutorials/wes-variant-calling-pipeline.html",
)
ASSET_PATHS = (
    "home-page.min.css",
    "index.html",
    "mobile-navigation.js",
    "script.js",
    "start-here.css",
    "tools/catalogue-learning.json",
    "tools/tutorial-code-groups.json",
    "tools/tutorial-code-languages.json",
    "tutorial-code-data.js",
    "tutorial-library.css",
)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _base_bytes(relative_path):
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid phase-cd baseline path: {relative_path!r}")
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
        raise AssertionError(f"phase-cd fixture fingerprint mismatch: {_sha(raw)}")
    fixture = json.loads(raw)
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("base_commit") != BASE_COMMIT):
        raise AssertionError("invalid phase-cd fixture header")
    pages = fixture.get("pages")
    assets = fixture.get("assets")
    if not isinstance(pages, list) or tuple(x.get("path") for x in pages) != PAGE_PATHS:
        raise AssertionError("phase-cd page scope is not exact")
    if not isinstance(assets, list) or tuple(x.get("path") for x in assets) != ASSET_PATHS:
        raise AssertionError("phase-cd asset scope is not exact")

    page_map = {}
    for entry in pages:
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"phase-cd base page unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file():
            raise AssertionError(f"phase-cd current page fingerprint mismatch: {path}")
        from homepage_redesign_baseline import normalize_homepage_redesign
        from final_polish_baseline import normalize_final_polish
        text = normalize_homepage_redesign(path, current_path.read_text(encoding="utf-8"))
        text = normalize_final_polish(path, text)
        if _sha(text.encode("utf-8")) != entry["current_sha256"]:
            raise AssertionError(f"phase-cd current page fingerprint mismatch: {path}")
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
                raise AssertionError(f"phase-cd hunk is not unique in {path}")
            text = text.replace(patch["before"], patch["after"], 1)
        if _sha(text.encode("utf-8")) != entry["base_sha256"]:
            raise AssertionError(f"phase-cd page restoration mismatch: {path}")
        page_map[path] = entry

    asset_map = {}
    for entry in assets:
        path = entry["path"]
        for key in ("current_sha256", "base_sha256"):
            if not isinstance(entry.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", entry[key]):
                raise AssertionError(f"invalid {key} for {path}")
        original = _base_bytes(path)
        if original is None or _sha(original) != entry["base_sha256"]:
            raise AssertionError(f"phase-cd base asset unavailable or changed: {path}")
        current_path = ROOT / path
        if not current_path.is_file():
            raise AssertionError(f"phase-cd current asset fingerprint mismatch: {path}")
        from homepage_redesign_baseline import normalize_homepage_redesign_bytes
        asset_bytes = normalize_homepage_redesign_bytes(path, current_path.read_bytes())
        if _sha(asset_bytes) != entry["current_sha256"]:
            raise AssertionError(f"phase-cd current asset fingerprint mismatch: {path}")
        asset_map[path] = entry

    fixture["page_map"] = page_map
    fixture["asset_map"] = asset_map
    return fixture


def normalize_phase_cd_fix(relative_path, text):
    """Reverse one exact Phase C/D page revision; preserve unknown mutations."""
    if not isinstance(text, str):
        raise TypeError("phase-cd normalization requires decoded text")
    from homepage_redesign_baseline import normalize_homepage_redesign
    text = normalize_homepage_redesign(relative_path, text)
    from final_polish_baseline import normalize_final_polish
    text = normalize_final_polish(relative_path, text)
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
            raise AssertionError(f"phase-cd hunk {index} is not unique in {relative_path}")
        text = text.replace(before, after, 1)
    if _sha(text.encode("utf-8")) != entry["base_sha256"]:
        raise AssertionError(f"phase-cd restoration mismatch: {relative_path}")
    return text


def restore_phase_cd_asset(relative_path, data):
    """Restore only an exact Phase C/D UI metadata asset to its 35ebb97c bytes."""
    from homepage_redesign_baseline import normalize_homepage_redesign_bytes
    data = normalize_homepage_redesign_bytes(relative_path, data)
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
        raise AssertionError(f"phase-cd base asset unavailable: {relative_path}")
    return original
