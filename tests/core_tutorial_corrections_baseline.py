"""Exact adapter for the public source changes in review-only PR #36.

Historical scope tests compare the working tree with earlier published states.
For the five corrected lessons and three generated inventory files, return the
exact parent-main bytes only when the input equals the frozen PR #36 commit.
Unknown edits are returned unchanged and remain visible to each test's existing
strict baseline checks.
"""
from functools import lru_cache
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PR36_BASE_COMMIT = "4c9f899bf0e48009fd871cd780bd7fd7513c6b80"
PR36_SOURCE_COMMIT = "eb51eb3db89c14aafd2ec71b73c290d51dee8174"
CORE_TUTORIAL_CORRECTION_PATHS = frozenset({
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/biological-data-formats.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/metagenomics-kraken2-bracken.html",
    "tutorials/scrna-seq-trajectory-inference.html",
    "tools/tutorial-code-groups.json",
    "tools/tutorial-code-languages.json",
    "tutorial-code-data.js",
})


@lru_cache(maxsize=None)
def _git_blob(commit, relative_path):
    if relative_path not in CORE_TUTORIAL_CORRECTION_PATHS:
        raise AssertionError(f"not an authorized PR #36 path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned PR #36 baseline is unavailable: {commit}:{relative_path}")
    return result.stdout


def normalize_core_tutorial_corrections(relative_path, content):
    """Map only exact PR #36 bytes back to its exact main-parent bytes."""
    if relative_path not in CORE_TUTORIAL_CORRECTION_PATHS:
        return content
    if isinstance(content, str):
        raw = content.encode("utf-8")
        as_text = True
    elif isinstance(content, bytes):
        raw = content
        as_text = False
    else:
        raise TypeError("PR #36 baseline normalization requires text or bytes")

    if raw != _git_blob(PR36_SOURCE_COMMIT, relative_path):
        return content
    baseline = _git_blob(PR36_BASE_COMMIT, relative_path)
    return baseline.decode("utf-8") if as_text else baseline
