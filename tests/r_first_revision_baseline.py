"""Exact historical restoration for the R-first tutorial/navigation revision.

This adapter reverses only fixture-pinned literal chunks from the immutable
2ad7731 baseline. The 58-page navigation scope stays distinct from the 27
article-content paths and the separate Start Here copy delta. Changed public
assets are accepted only by explicit path and complete SHA-256 digest.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

from latest_review_baseline import normalize_latest_review, restore_latest_review_asset
from start_here_desktop_baseline import normalize_start_here_desktop_html

ROOT = Path(__file__).resolve().parents[1]
PRE_R_FIRST_COMMIT = "2ad77315c9fbc48ac5b941df9998bbad4b76fb2f"
FIXTURE_PATH = ROOT / "tests/fixtures/r-first-revision-edits.json"
# Provisional snapshot pin; refresh after metadata/source-group assets are final.
FIXTURE_SHA256 = "b762ad95ae28d504e5a79ffc89d0602027a34645a029d026a7ed6b7f1602306e"
EXPECTED_NAVIGATION_PAGE_COUNT = 58
EXPECTED_CONTENT_PAGE_COUNT = 27
START_HERE_PATH = "start-here.html"

# Actual changed-article scope supplied by the date/content review. InferCNV is
# intentionally not included because its article content did not change.
AUTHORIZED_ARTICLE_PATHS = frozenset({
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/biological-data-formats.html",
    "tutorials/data-visualization-fundamentals.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/evolutionary-phylogeny-analysis.html",
    "tutorials/experimental-design-batch-effects.html",
    "tutorials/git-github-bioinformatics.html",
    "tutorials/hpc-basic-commands.html",
    "tutorials/hpc-submission-part1.html",
    "tutorials/introduction-to-bioinformatics.html",
    "tutorials/mcp-zotero.html",
    "tutorials/protein-structure-design-alphafold.html",
    "tutorials/python-fundamentals-bioinformatics.html",
    "tutorials/quality-control-fundamentals.html",
    "tutorials/reproducible-project-structure.html",
    "tutorials/reproducible-workflows-snakemake-nextflow.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/scrna-seq-basics.html",
    "tutorials/scrna-seq-quality-control.html",
    "tutorials/scrna-seq-trajectory-inference.html",
    "tutorials/single-cell-foundation-models.html",
    "tutorials/spatial-transcriptomics-r-python.html",
    "tutorials/statistics-for-bioinformatics.html",
})

# Only these exact public assets are in this layer. New R/source/fixture assets
# are listed individually; no directory-wide allowlist is used.
AUTHORIZED_R_FIRST_ASSET_PATHS = frozenset({
    "tutorial-navigation.css",
    "code-tabs.js",
    "copy-code.js",
    "tutorial-code-data.js",
    "tools/tutorial-code-languages.json",
    "tools/generate_learning_paths.py",
    "tools/generate_tutorial_ui.py",
    "tools/tutorial-code-groups.json",
    "tools/learning-paths.json",
    "tools/catalogue-learning.json",
    "docs/tutorial-quality-standard.md",
    "sitemap.xml",
    "files/tutorial-examples/data-visualization-fundamentals/data-visualization-fundamentals.Rmd",
    "files/coding-assistant-lesson/inspect_counts.R",
    "files/coding-assistant-lesson/test_inspect_counts.R",
    "files/github-copilot-lesson/sort_counts.R",
    "files/github-copilot-lesson/test_sort_counts.R",
    "files/orchestrator_workflow.R",
    "files/test_orchestrator_workflow.R",
    "files/tutorial-examples/foundation-model-evaluation/evaluate_embeddings.R",
    "files/tutorial-examples/foundation-model-evaluation/foundation_embedding_evaluation.Rmd",
    "files/tutorial-examples/foundation-model-evaluation/synthetic_embeddings.csv",
    "files/tutorial-examples/foundation-model-evaluation/synthetic_metadata.csv",
    "files/tutorial-examples/protein-structure-review/inspect_alphafold.R",
    "files/tutorial-examples/protein-structure-review/protein_structure_review.Rmd",
    "files/tutorial-examples/protein-structure-review/synthetic_ca_fixture.pdb",
    "files/tutorial-examples/python-fundamentals-bioinformatics/compute_fasta_stats.R",
    "files/tutorial-examples/research-reporting-interpretation/data/synthetic_qc.csv",
    "files/tutorial-examples/research-reporting-interpretation/references.bib",
    "files/tutorial-examples/research-reporting-interpretation/research-reporting-workflow.Rmd",
})
R_FIRST_ASSET_PATHS = AUTHORIZED_R_FIRST_ASSET_PATHS


def pre_r_first_bytes(relative_path):
    """Read one safe path from the immutable task baseline, if it existed there."""
    if (not isinstance(relative_path, str) or relative_path.startswith("/")
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"invalid R-first baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{PRE_R_FIRST_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _validate_three_line_context(before, after, label):
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    if min(len(old_lines), len(new_lines)) < 6:
        raise AssertionError(f"{label} needs three unchanged context lines on each side")
    if old_lines[:3] != new_lines[:3] or old_lines[-3:] != new_lines[-3:]:
        raise AssertionError(f"{label} does not preserve literal three-line context")


@lru_cache(maxsize=1)
def _fixture():
    """Load and validate every explicit scope and patch against 2ad7731."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("R-first fixture pin is not frozen yet")
    raw = FIXTURE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"R-first fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid R-first fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("pre_r_first_commit") != PRE_R_FIRST_COMMIT):
        raise AssertionError("invalid R-first fixture header")

    nav = fixture.get("navigation_paths")
    content = fixture.get("content_paths")
    files = fixture.get("files")
    nonnav = fixture.get("non_navigation_files")
    asset_hashes = fixture.get("asset_sha256")
    if (not isinstance(nav, list) or len(nav) != EXPECTED_NAVIGATION_PAGE_COUNT
            or len(set(nav)) != len(nav)
            or any(not isinstance(p, str) or not p.startswith("tutorials/") or not p.endswith(".html") for p in nav)
            or not isinstance(content, list) or len(content) != EXPECTED_CONTENT_PAGE_COUNT
            or len(set(content)) != len(content)
            or set(content) != AUTHORIZED_ARTICLE_PATHS or not set(content).issubset(nav)
            or not isinstance(files, dict) or set(files) != set(nav)
            or not isinstance(nonnav, dict) or set(nonnav) != {START_HERE_PATH}
            or not isinstance(asset_hashes, dict) or set(asset_hashes) != AUTHORIZED_R_FIRST_ASSET_PATHS):
        raise AssertionError("invalid R-first page, non-navigation, or asset scope")
    for path, digest in asset_hashes.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AssertionError(f"invalid R-first SHA-256 pin for {path}")

    def validate_patch_map(patch_map, label, required_paths):
        validated = {}
        if set(patch_map) != set(required_paths):
            raise AssertionError(f"invalid {label} path allowlist")
        for relative_path, patches in patch_map.items():
            if not isinstance(patches, list) or not patches:
                raise AssertionError(f"{label} requires literal chunks for {relative_path}")
            original = pre_r_first_bytes(relative_path)
            if original is None:
                raise AssertionError(f"pinned R-first source unavailable: {relative_path}")
            source = original.decode("utf-8")
            for index, patch in enumerate(patches):
                name = f"{relative_path} chunk {index}"
                if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                        or not isinstance(patch["before"], str) or not isinstance(patch["after"], str)
                        or not patch["before"] or not patch["after"] or patch["before"] == patch["after"]):
                    raise AssertionError(f"invalid {name}")
                _validate_three_line_context(patch["before"], patch["after"], name)
                if source.count(patch["before"]) != 1:
                    raise AssertionError(f"{name} must occur exactly once in 2ad7731")
                source = source.replace(patch["before"], patch["after"], 1)
            validated[relative_path] = patches
        return validated

    fixture["files"] = validate_patch_map(files, "R-first navigation", nav)
    fixture["non_navigation_files"] = validate_patch_map(
        nonnav, "R-first non-navigation", {START_HERE_PATH}
    )
    return fixture


def page_patches():
    """Return literal patches for precisely the frozen 58-page navigation set."""
    return _fixture()["files"]


def non_navigation_patches():
    """Return the separately scoped exact Start Here copy/date chunks."""
    return _fixture()["non_navigation_files"]


def navigation_paths():
    """Return the frozen 58-page navigation allowlist."""
    return tuple(_fixture()["navigation_paths"])


def content_paths():
    """Return only the exact 27 reviewed article-content paths."""
    return frozenset(_fixture()["content_paths"])


# Kept as a module-level immutable map for the historical adapters that compose
# asset restoration. Its contents are fixture-pinned and key-checked above.
R_FIRST_ASSET_SHA256 = dict(_fixture()["asset_sha256"])


def normalize_r_first_revision(relative_path, text):
    """Reverse matching literal chunks; every unmatched edit remains visible."""
    if not isinstance(text, str):
        raise TypeError("R-first normalization requires decoded text")
    text = normalize_latest_review(relative_path, text)
    text = normalize_start_here_desktop_html(relative_path, text)
    # The execution-review layer is a separate exact-digest/context adapter.
    # Once it returns the immutable 122bd bytes, the historical R-first patches
    # below remain unchanged and naturally become an idempotent no-op.
    from tutorial_execution_baseline import normalize_execution_delta
    text = normalize_execution_delta(relative_path, text)
    if relative_path in page_patches():
        patches = page_patches()[relative_path]
    elif relative_path in non_navigation_patches():
        patches = non_navigation_patches()[relative_path]
    else:
        return text
    for index, patch in reversed(list(enumerate(patches))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(f"duplicate exact R-first patch chunk {index} in {relative_path}")
        if count == 1:
            text = text.replace(after, before, 1)
    return text


def verify_r_first_asset(relative_path, data):
    """Accept only explicit changed assets with an exact complete-file digest."""
    if relative_path not in R_FIRST_ASSET_SHA256:
        raise AssertionError(f"not an authorized R-first asset: {relative_path}")
    original_data = data
    from startup_performance_baseline import restore_startup_performance_asset
    data = restore_startup_performance_asset(relative_path, data)
    data = restore_latest_review_asset(relative_path, data)
    observed = hashlib.sha256(data).hexdigest()
    expected = R_FIRST_ASSET_SHA256[relative_path]
    if observed != expected:
        raise AssertionError(f"R-first asset fingerprint mismatch for {relative_path}: {observed}")
    return original_data


def restore_r_first_asset(relative_path, data):
    """Verify a changed asset, then restore exact 2ad7731 bytes when tracked."""
    from startup_performance_baseline import restore_startup_performance_asset
    data = restore_startup_performance_asset(relative_path, data)
    data = restore_latest_review_asset(relative_path, data)
    # Compose the separately pinned execution-review asset layer first. Its
    # exact 122bd bytes then pass through the original R-first restoration path.
    from tutorial_execution_baseline import restore_overlapping_execution_asset
    data = restore_overlapping_execution_asset(relative_path, data)
    original = pre_r_first_bytes(relative_path)
    # A second layer may receive an asset already restored to the pinned source.
    # Accept only exact historical bytes; an arbitrary mutation still has to
    # pass the current full-file SHA-256 gate below.
    if original is not None and data == original:
        return data
    verify_r_first_asset(relative_path, data)
    return original if original is not None else data
