"""Narrow adapter for the image-led Start Here restoration and roadmap redesign.

The adapter accepts only the pinned reviewed stylesheet and exact reviewed page
state; it normalizes those two authorized assets to immutable e846ce3 bytes for
older repository scope checks. Any other edits remain visible to those checks.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import subprocess
from coffee_removal_baseline import restore_coffee_removal_text

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_BASELINE_COMMIT = "e846ce3fb6053ed611dc87fc62748865499913d0"
IMAGE_LED_COMMIT = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
DESKTOP_CSS_VERSION = "20261029-learner-v1"
DESKTOP_CSS_SHA256 = "a52bbfd3c25f89c94383849a4f866090238d17c0146d668429443f412a6ac898"
DESKTOP_CSS_HREF = f"start-here.css?v={DESKTOP_CSS_VERSION}"
DESKTOP_HTML_SHA256 = "d3d74865a9f79d1ee1fffce3d5c4a93574813fc4ba7de6f7b7a6bfa3320fe435"


def _show_bytes(spec):
    result = subprocess.run(
        ["git", "show", spec], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"immutable Start Here source unavailable: {spec}")
    return result.stdout


def _baseline_bytes(relative_path):
    if relative_path not in {"start-here.html", "start-here.css"}:
        raise AssertionError(f"not an authorized Start Here restoration path: {relative_path}")
    return _show_bytes(f"{DESKTOP_BASELINE_COMMIT}:{relative_path}")


@lru_cache(maxsize=1)
def expected_restored_css():
    """Return historical image-led CSS with only the four approved text colors darkened."""
    source = _show_bytes(f"{IMAGE_LED_COMMIT}:start-here.css").decode("utf-8")
    replacements = (
        (
            "  --sh-gold: #FBBF24;\n",
            "  --sh-gold: #FBBF24;\n"
            "  --sh-violet-ink: #6941C6;\n"
            "  --sh-cyan-ink: #0C667D;\n"
            "  --sh-gold-ink: #8A5900;\n",
        ),
        (".sh-label-violet { color: var(--sh-violet); }", ".sh-label-violet { color: var(--sh-violet-ink); }"),
        (".sh-tag-violet { color: var(--sh-violet); }", ".sh-tag-violet { color: var(--sh-violet-ink); }"),
        (".sh-tag-cyan   { color: var(--sh-cyan); }", ".sh-tag-cyan   { color: var(--sh-cyan-ink); }"),
        (".sh-tag-gold   { color: var(--sh-gold); }", ".sh-tag-gold   { color: var(--sh-gold-ink); }"),
    )
    for original, revised in replacements:
        if source.count(original) != 1:
            raise AssertionError(f"historical stylesheet must contain one approved color target: {original}")
        source = source.replace(original, revised, 1)
    return source.encode("utf-8")


@lru_cache(maxsize=1)
def _exact_restored_page():
    """Build the one approved HTML state from the fixed base and historical main."""
    base = _baseline_bytes("start-here.html").decode("utf-8")
    historical = _show_bytes(f"{IMAGE_LED_COMMIT}:start-here.html").decode("utf-8")
    main_re = re.compile(r"<main\b[^>]*>.*?</main\s*>", re.S | re.I)
    base_mains, historical_mains = main_re.findall(base), main_re.findall(historical)
    if len(base_mains) != 1 or len(historical_mains) != 1:
        raise AssertionError("the pinned base and historical page must each have one main element")
    page = base.replace(base_mains[0], historical_mains[0], 1)
    page, removed = re.subn(
        r'<script\b[^>]*\bsrc="start-here\.js\?v=[^"]+"[^>]*></script>\s*',
        "", page, count=1, flags=re.I,
    )
    if removed != 1:
        raise AssertionError("the pinned base must contain one circle-only Start Here script")
    page, updated = re.subn(
        r'href="start-here\.css\?v=[^"]+"',
        f'href="{DESKTOP_CSS_HREF}"', page, count=1,
    )
    if updated != 1:
        raise AssertionError("the pinned base must contain one Start Here CSS href")
    return page


def normalize_start_here_desktop_html(relative_path, text):
    """Reverse only the exact reviewed page; otherwise normalize only the literal href."""
    if not isinstance(text, str):
        raise TypeError("Start Here HTML normalization requires decoded text")
    text = restore_coffee_removal_text(relative_path, text, strict=False)
    if relative_path != "start-here.html":
        return text
    if text == _exact_restored_page() or hashlib.sha256(text.encode("utf-8")).hexdigest() == DESKTOP_HTML_SHA256:
        return _baseline_bytes("start-here.html").decode("utf-8")
    baseline = _baseline_bytes("start-here.html").decode("utf-8")
    matches = re.findall(r'<link\b[^>]*href="([^"]+)"[^>]*>', baseline)
    expected_hrefs = [href for href in matches if href.startswith("start-here.css?v=")]
    if len(expected_hrefs) != 1:
        raise AssertionError("e846ce3 must contain exactly one Start Here CSS href")
    baseline_href = expected_hrefs[0]
    count = text.count(DESKTOP_CSS_HREF)
    if count > 1:
        raise AssertionError("duplicate exact Start Here restoration CSS href")
    if count == 1:
        text = text.replace(DESKTOP_CSS_HREF, baseline_href, 1)
    return text


def restore_start_here_desktop_asset(relative_path, data):
    """Verify the exact reviewed image-led CSS and return exact e846ce3 bytes."""
    if relative_path != "start-here.css":
        raise AssertionError(f"not an authorized Start Here stylesheet: {relative_path}")
    baseline = _show_bytes(f"{DESKTOP_BASELINE_COMMIT}:start-here.css")
    if data == baseline:
        return baseline
    observed = hashlib.sha256(data).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", DESKTOP_CSS_SHA256):
        raise AssertionError(
            "parent must refresh tests/start_here_desktop_baseline.py: "
            f"DESKTOP_CSS_SHA256 with the finalized stylesheet SHA-256 ({observed})"
        )
    if observed != DESKTOP_CSS_SHA256:
        raise AssertionError(f"Start Here restoration CSS fingerprint mismatch: {observed}")
    return baseline
