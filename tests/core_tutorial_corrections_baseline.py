"""Exact adapter for the eight public source files changed by PR #37.

Historical scope tests compare the working tree with earlier published states.
For the five corrected lesson pages and three generated code-tab files, map only
bytes that exactly match the pinned PR #37 source commit to its exact main-parent
bytes. Unknown edits and unlisted paths pass through unchanged so existing
strict assertions continue to reject them.
"""
from functools import lru_cache
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PR37_BASE_COMMIT = "17b51f57b4eb9bded381ba9a469776dcc654e782"
PR37_SOURCE_COMMIT = "f4d4fa6a59a9f9f50d66a7bf2e1860744f0b9e0f"
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
        raise AssertionError(f"not an authorized PR #37 path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned PR #37 baseline is unavailable: {commit}:{relative_path}")
    return result.stdout


def normalize_core_tutorial_corrections(relative_path, content):
    """Map only exact PR #37 bytes back to exact current-main bytes."""
    if relative_path not in CORE_TUTORIAL_CORRECTION_PATHS:
        return content
    if isinstance(content, str):
        raw = content.encode("utf-8")
        as_text = True
    elif isinstance(content, bytes):
        raw = content
        as_text = False
    else:
        raise TypeError("PR #37 baseline normalization requires text or bytes")

    if raw != _git_blob(PR37_SOURCE_COMMIT, relative_path):
        return content
    baseline = _git_blob(PR37_BASE_COMMIT, relative_path)
    return baseline.decode("utf-8") if as_text else baseline
