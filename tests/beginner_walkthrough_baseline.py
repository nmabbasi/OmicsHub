"""Exact PR9 restoration for the six approved beginner walkthrough articles.

Only the inner article body and the explicitly allowed dateModified values are
restored. Article wrappers and all surrounding page markup remain visible to
historical comparisons.
"""
from functools import lru_cache
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_PR9 = "d7f9bd559c0b7d326edaa9b94d3c461ad50d0f0d"
BEGINNER_WALKTHROUGH_ARTICLES = frozenset({
    "tutorials/computer-data-fundamentals.html",
    "tutorials/statistics-for-bioinformatics.html",
    "tutorials/experimental-design-batch-effects.html",
    "tutorials/command-line-part2.html",
    "tutorials/command-line-part3.html",
    "tutorials/conda-mamba-part1.html",
})

# The first three pages receive a fresh date in this revision. The command-line
# pages were already dated 2026-10-23 in PR9 and must remain so.
_ALLOWED_CURRENT_DATES = {
    "tutorials/computer-data-fundamentals.html": frozenset({"2026-10-21", "2026-10-23"}),
    "tutorials/statistics-for-bioinformatics.html": frozenset({"2026-10-21", "2026-10-23"}),
    "tutorials/experimental-design-batch-effects.html": frozenset({"2026-10-21", "2026-10-23"}),
    "tutorials/command-line-part2.html": frozenset({"2026-10-21", "2026-10-23"}),
    "tutorials/command-line-part3.html": frozenset({"2026-10-21", "2026-10-23"}),
    "tutorials/conda-mamba-part1.html": frozenset({"2026-10-21", "2026-10-23"}),
}
_ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
_DATE = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')


@lru_cache(maxsize=None)
def _published_page(relative_path):
    if relative_path not in BEGINNER_WALKTHROUGH_ARTICLES:
        raise AssertionError(f"not an approved beginner walkthrough path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR9}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError(f"published PR9 page unavailable: {relative_path}")
    return result.stdout.decode("utf-8")


def normalize_beginner_walkthrough_revision(relative_path, text):
    """Restore PR9's article body/date, leaving all other bytes in ``text`` intact.

    Target article wrappers are deliberately retained from the supplied text so
    attribute or wrapper changes are not hidden. Fragments are supported: only
    complete article/date structures present in the fragment are normalized.
    """
    if relative_path not in BEGINNER_WALKTHROUGH_ARTICLES:
        return text

    published = _published_page(relative_path)
    published_articles = list(_ARTICLE.finditer(published))
    if len(published_articles) != 1:
        raise AssertionError(f"expected one PR9 article in {relative_path}")
    current_articles = list(_ARTICLE.finditer(text))
    if current_articles:
        if len(current_articles) != 1:
            raise AssertionError(f"expected one current article in {relative_path}")
        match = current_articles[0]
        text = (
            text[:match.start()]
            + match.group("open")
            + published_articles[0].group("body")
            + match.group("close")
            + text[match.end():]
        )

    published_dates = list(_DATE.finditer(published))
    if len(published_dates) != 1:
        raise AssertionError(f"expected one PR9 dateModified in {relative_path}")
    current_dates = list(_DATE.finditer(text))
    if current_dates:
        if len(current_dates) != 1:
            raise AssertionError(f"expected one current dateModified in {relative_path}")
        match = current_dates[0]
        if match.group(2) not in _ALLOWED_CURRENT_DATES[relative_path]:
            raise AssertionError(
                f"unexpected dateModified in {relative_path}: {match.group(2)}"
            )
        text = (
            text[:match.start(2)]
            + published_dates[0].group(2)
            + text[match.end(2):]
        )

    return text
