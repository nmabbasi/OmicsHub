"""Exact PR10 restoration for the one authorized tidyverse setup revision.

Only the inner article content, JSON-LD dateModified value, and visible Updated
label are restored. Article wrappers, navigation, and all surrounding markup
remain visible to historical comparisons.
"""
from functools import lru_cache
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_PR10 = "d1748a93e9fb9a59ec20ee3ab7aabece9c0ae1f8"
TIDYVERSE_SETUP_ARTICLE = "tutorials/r-tidyverse-fundamentals.html"
_ALLOWED_DATES = frozenset({"2026-10-21", "2026-10-23"})
_ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
_DATE = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')
_UPDATED = re.compile(r"Updated (2026-10-\d{2})")


@lru_cache(maxsize=1)
def published_tidyverse_page():
    """Return the exact published PR10 page used as the normalization source."""
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR10}:{TIDYVERSE_SETUP_ARTICLE}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError("published PR10 tidyverse page is unavailable")
    return result.stdout.decode("utf-8")


def normalize_tidyverse_setup_revision(relative_path, text):
    """Restore only the approved article/date deltas for historical comparisons."""
    if relative_path != TIDYVERSE_SETUP_ARTICLE:
        return text

    published = published_tidyverse_page()
    published_articles = list(_ARTICLE.finditer(published))
    if len(published_articles) != 1:
        raise AssertionError("expected one PR10 tidyverse article")
    current_articles = list(_ARTICLE.finditer(text))
    if current_articles:
        if len(current_articles) != 1:
            raise AssertionError("expected one current tidyverse article")
        match = current_articles[0]
        text = (
            text[:match.start()]
            + match.group("open")
            + published_articles[0].group("body")
            + match.group("close")
            + text[match.end():]
        )

    published_dates = list(_DATE.finditer(published))
    if len(published_dates) != 1 or published_dates[0].group(2) != "2026-10-21":
        raise AssertionError("unexpected PR10 tidyverse dateModified")
    current_dates = list(_DATE.finditer(text))
    if current_dates:
        if len(current_dates) != 1:
            raise AssertionError("expected one current tidyverse dateModified")
        match = current_dates[0]
        if match.group(2) not in _ALLOWED_DATES:
            raise AssertionError(f"unexpected tidyverse dateModified: {match.group(2)}")
        text = text[:match.start(2)] + published_dates[0].group(2) + text[match.end(2):]

    published_updated = list(_UPDATED.finditer(published))
    if len(published_updated) != 1 or published_updated[0].group(1) != "2026-10-21":
        raise AssertionError("expected one PR10 visible Updated date")
    current_updated = list(_UPDATED.finditer(text))
    if current_updated:
        if len(current_updated) != 1:
            raise AssertionError("expected one current visible Updated date")
        match = current_updated[0]
        if match.group(1) not in _ALLOWED_DATES:
            raise AssertionError(f"unexpected visible tidyverse Updated date: {match.group(1)}")
        text = text[:match.start(1)] + published_updated[0].group(1) + text[match.end(1):]

    return text
