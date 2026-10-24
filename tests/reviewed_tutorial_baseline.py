"""Narrow normalization for tutorial edits approved on main and this date-only patch."""
import re

from tutorial_ui_baseline import normalize_tutorial_ui


APPROVED_MAIN = "994e363be42c4ae6f70e924f7030aad74b9cda5f"

# Exact before/after values from the approved-main comparison and the reviewed
# date revision. Keeping the paths explicit prevents unrelated dates being hidden.
REVIEWED_DATE_MODIFICATIONS = {
    "tutorials/advanced-visualization-packages.html": ("2026-10-21", "2026-10-23"),
    "tutorials/ai-prompt-engineering-seurat.html": ("2026-10-22", "2026-10-23"),
    "tutorials/command-line-part3.html": ("2026-10-21", "2026-10-23"),
    "tutorials/deterministic-retrieval-gget-ai.html": ("2026-10-21", "2026-10-23"),
    "tutorials/mcp-zotero.html": ("2026-10-21", "2026-10-23"),
    "tutorials/modern-bioinformatics-methods-2026.html": ("2026-10-21", "2026-10-23"),
    "tutorials/single-cell-foundation-models.html": ("2026-10-21", "2026-10-23"),
    "tutorials/spatial-transcriptomics-r-python.html": ("2026-10-21", "2026-10-23"),
    "tutorials/wes-variant-calling-pipeline.html": ("2026-10-21", "2026-10-23"),
    "tutorials/hpc-submission-part1.html": ("2026-10-21", "2026-10-23"),
    "tutorials/reproducible-workflows-snakemake-nextflow.html": ("2026-10-21", "2026-10-23"),
}
_VISIBLE_DATE_PATH = "tutorials/ai-prompt-engineering-seurat.html"
_VISIBLE_DATE_VALUES = ("22 October 2026", "23 October 2026")
_COOKIE_BANNER = re.compile(
    r"\n[ \t]*<!-- Cookie Consent Banner -->.*?<!-- /Cookie Consent Banner -->",
    re.S,
)


def normalize_reviewed_content(relative_path, text):
    """Replace only the reviewed date metadata/label delta with stable tokens."""
    dates = REVIEWED_DATE_MODIFICATIONS.get(relative_path)
    if dates:
        matches = list(re.finditer(r'("dateModified"\s*:\s*")([^"]+)(")', text))
        if len(matches) != 1 or matches[0].group(2) not in dates:
            raise AssertionError(f"unexpected dateModified in {relative_path}")
        match = matches[0]
        text = text[:match.start(2)] + "__REVIEWED_DATE_MODIFICATION__" + text[match.end(2):]

    if relative_path == _VISIBLE_DATE_PATH:
        matches = [value for value in _VISIBLE_DATE_VALUES if text.count(value)]
        if len(matches) != 1 or text.count(matches[0]) != 1:
            raise AssertionError(f"unexpected visible Updated label in {relative_path}")
        text = text.replace(matches[0], "__REVIEWED_VISIBLE_UPDATED_DATE__", 1)
    return text


def strip_cookie_banner(text, allow_missing=False):
    """Remove one marked banner block, optionally allowing a pre-banner baseline."""
    text, count = _COOKIE_BANNER.subn("", text, count=1)
    if count != 1 and not (allow_missing and count == 0):
        raise AssertionError("expected exactly one marked cookie-consent banner")
    return text


# Dedicated execution/contract tests cover the four owner-authorized article
# changes below. All other article bodies and all surrounding scripts remain
# protected; only the two existing reader-navigation blocks are excluded.
LEARNER_REVISION_ARTICLES = frozenset({
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/hpc-submission-part1.html",
    "tutorials/reproducible-workflows-snakemake-nextflow.html",
    "tutorials/wes-variant-calling-pipeline.html",
})
_READER_NAVIGATION = (
    re.compile(r'<nav\b(?=[^>]*\bclass="[^"]*\breader-toolbar\b)[^>]*>.*?</nav>', re.S),
    re.compile(r'<nav\b(?=[^>]*\bid="reader-course-navigation")[^>]*>.*?</nav>', re.S),
)


def normalize_learner_revision(relative_path, text):
    """Mask only reviewed article/navigation deltas, never whole page bodies."""
    text = normalize_tutorial_ui(relative_path, text)
    for index, pattern in enumerate(_READER_NAVIGATION):
        text, count = pattern.subn(f"__REVIEWED_READER_NAV_{index}__", text)
        if count != 1:
            raise AssertionError(f"expected one reader nav {index} in {relative_path}")
    if relative_path in LEARNER_REVISION_ARTICLES:
        text, count = re.subn(
            r'<article\b[^>]*>.*?</article>', "__REVIEWED_PRIORITY_ARTICLE__", text, flags=re.S
        )
        if count != 1:
            raise AssertionError(f"expected one reviewed article in {relative_path}")
    if relative_path == "tutorials/reproducible-workflows-snakemake-nextflow.html":
        text, count = re.subn(
            r'<p class="text-sm text-gray-600 mb-2">(?:These examples do not have a recorded test environment|Validation boundary:).*?</p>',
            "__REVIEWED_NEXTFLOW_EXECUTION_NOTE__", text, flags=re.S
        )
        if count != 1:
            raise AssertionError("expected the single reviewed Nextflow validation note")
    return text
