"""Exact PR11 restoration for the authorized Ubuntu Tidyverse article revision.

This layer restores only the target article body and its two approved date
labels to PR11, before older PR10 historical guards are applied.
"""
from functools import lru_cache
from pathlib import Path
import re
import subprocess

from tutorial_ui_baseline import normalize_tutorial_ui

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_PR11 = "85937d5d76d42602c67b50003d959ff81a7c1ab1"
TIDYVERSE_SETUP_ARTICLE = "tutorials/r-tidyverse-fundamentals.html"
PR11_DATE = "2026-10-23"
CURRENT_DATE = "2026-10-24"
_ALLOWED_DATES = frozenset({PR11_DATE, CURRENT_DATE})
_ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
_DATE = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')
_UPDATED = re.compile(r"Updated (2026-10-\d{2})")


@lru_cache(maxsize=1)
def published_pr11_tidyverse_page():
    """Return the exact target article as published in PR11."""
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR11}:{TIDYVERSE_SETUP_ARTICLE}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError("published PR11 tidyverse page is unavailable")
    return result.stdout.decode("utf-8")


def normalize_ubuntu_tidyverse_revision(relative_path, text):
    """Restore only the permitted target article and date changes to PR11."""
    text = normalize_tutorial_ui(relative_path, text)
    if relative_path != TIDYVERSE_SETUP_ARTICLE:
        return text

    published = normalize_tutorial_ui(relative_path, published_pr11_tidyverse_page())
    published_articles = list(_ARTICLE.finditer(published))
    current_articles = list(_ARTICLE.finditer(text))
    if len(published_articles) != 1 or len(current_articles) != 1:
        raise AssertionError("expected exactly one PR11 and current tidyverse article")
    if published_articles[0].group("open") != current_articles[0].group("open"):
        raise AssertionError("the tidyverse article wrapper is not authorized to change")
    if published_articles[0].group("close") != current_articles[0].group("close"):
        raise AssertionError("the tidyverse article closing wrapper is not authorized to change")
    match = current_articles[0]
    text = (
        text[:match.start()]
        + match.group("open")
        + published_articles[0].group("body")
        + match.group("close")
        + text[match.end():]
    )

    published_dates = list(_DATE.finditer(published))
    current_dates = list(_DATE.finditer(text))
    if len(published_dates) != 1 or published_dates[0].group(2) != PR11_DATE:
        raise AssertionError("unexpected PR11 tidyverse dateModified")
    if len(current_dates) != 1 or current_dates[0].group(2) not in _ALLOWED_DATES:
        raise AssertionError("expected exactly one approved tidyverse dateModified")
    match = current_dates[0]
    text = text[:match.start(2)] + PR11_DATE + text[match.end(2):]

    published_updated = list(_UPDATED.finditer(published))
    current_updated = list(_UPDATED.finditer(text))
    if len(published_updated) != 1 or published_updated[0].group(1) != PR11_DATE:
        raise AssertionError("expected one PR11 visible Updated date")
    if len(current_updated) != 1 or current_updated[0].group(1) not in _ALLOWED_DATES:
        raise AssertionError("expected exactly one approved visible Updated date")
    match = current_updated[0]
    text = text[:match.start(1)] + PR11_DATE + text[match.end(1):]
    return text
