"""Narrow normalization for tutorial edits approved on main and this date-only patch."""
import re


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
