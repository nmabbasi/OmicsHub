"""Exact PR8 restoration for the six owner-authorized lesson revisions.

This helper restores each approved lesson's article body, JSON-LD dateModified,
and (where present) one uniquely selected execution-disclosure paragraph from
PR8. Revised disclosures must be registered by exact full-paragraph text in the
current-note hook; arbitrary surrounding text is never masked.
"""
from functools import lru_cache
from pathlib import Path
import re
import subprocess

from tutorial_ui_baseline import normalize_tutorial_ui

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_PR8 = "5ba874b7bc4d415aaa65efef8502d8be6aa2d169"
SIX_LESSON_ARTICLES = frozenset({
    "tutorials/command-line-part2.html",
    "tutorials/conda-mamba-part1.html",
    "tutorials/hpc-basic-commands.html",
    "tutorials/scrna-seq-trajectory-inference.html",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/ai-coding-cursor-aider.html",
})

_ARTICLE = re.compile(
    r"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article>)", re.S | re.I
)
_DATE = re.compile(r'("dateModified"\s*:\s*")([^"]+)(")')
_DISCLOSURE = re.compile(
    r'<p\s+class="text-sm text-gray-600 mb-2"[^>]*>.*?</p>', re.S | re.I
)
SIX_LESSON_DISCLOSURE_PAGES = frozenset({
    "tutorials/command-line-part2.html",
    "tutorials/conda-mamba-part1.html",
    "tutorials/hpc-basic-commands.html",
    "tutorials/ai-coding-cursor-aider.html",
})
# Parent fills these exact full-paragraph values once the final copy is settled.
# Until then, the published paragraph remains the only accepted current text.
SIX_LESSON_CURRENT_EXECUTION_NOTES = {}
_ALLOWED_REVISED_DATE = "2026-10-23"


@lru_cache(maxsize=None)
def _published_page(relative_path):
    if relative_path not in SIX_LESSON_ARTICLES:
        raise AssertionError(f"not an approved six-lesson path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_PR8}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError(f"published PR8 page unavailable: {relative_path}")
    return result.stdout.decode("utf-8")


def normalize_six_lesson_revision(relative_path, text):
    """Restore only PR8 article/date and explicitly registered note deltas.

    Non-target paths are returned verbatim. A fragment without a full article or
    metadata is supported: only the complete structures present in that
    fragment can be normalized.
    """
    text = normalize_tutorial_ui(relative_path, text)
    if relative_path not in SIX_LESSON_ARTICLES:
        return text

    published = normalize_tutorial_ui(relative_path, _published_page(relative_path))
    published_articles = list(_ARTICLE.finditer(published))
    if len(published_articles) != 1:
        raise AssertionError(f"expected one PR8 article in {relative_path}")
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
    if len(published_dates) != 1 or published_dates[0].group(2) != "2026-10-21":
        raise AssertionError(f"unexpected PR8 dateModified in {relative_path}")
    current_dates = list(_DATE.finditer(text))
    if current_dates:
        if len(current_dates) != 1:
            raise AssertionError(f"expected one current dateModified in {relative_path}")
        match = current_dates[0]
        if match.group(2) not in {"2026-10-21", _ALLOWED_REVISED_DATE}:
            raise AssertionError(f"unexpected dateModified in {relative_path}: {match.group(2)}")
        text = text[:match.start(2)] + published_dates[0].group(2) + text[match.end(2):]

    if relative_path in SIX_LESSON_DISCLOSURE_PAGES:
        old_notes = list(_DISCLOSURE.finditer(published))
        current_notes = list(_DISCLOSURE.finditer(text))
        if len(old_notes) != 1:
            raise AssertionError(f"expected one PR8 execution disclosure in {relative_path}")
        if current_notes:
            if len(current_notes) != 1:
                raise AssertionError(f"expected one current execution disclosure in {relative_path}")
            match = current_notes[0]
            expected_note = SIX_LESSON_CURRENT_EXECUTION_NOTES.get(
                relative_path, old_notes[0].group(0)
            )
            if match.group(0) != expected_note:
                raise AssertionError(
                    f"unregistered exact execution disclosure in {relative_path}; "
                    "update SIX_LESSON_CURRENT_EXECUTION_NOTES with the approved paragraph"
                )
            text = text[:match.start()] + old_notes[0].group(0) + text[match.end():]

    return text
