"""Narrow adapter for the Start Here desktop-readability revision.

The adapter accepts only the complete owner-authored stylesheet hash and one
literal stylesheet cache href. It restores CSS to immutable e846ce3 bytes and
normalizes only that cache token before older historical restorations run.
"""
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_BASELINE_COMMIT = "e846ce3fb6053ed611dc87fc62748865499913d0"
DESKTOP_CSS_VERSION = "20261026-editorial-route-index-v1"
DESKTOP_CSS_SHA256 = "4c4451ad3c5f60cd5d1fbee924e422dcdb964cf40d8621f0fdccb2b8d0a15d31"
DESKTOP_CSS_HREF = f"start-here.css?v={DESKTOP_CSS_VERSION}"


def _baseline_bytes(relative_path):
    if relative_path not in {"start-here.html", "start-here.css"}:
        raise AssertionError(f"not an authorized desktop-readability baseline path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{DESKTOP_BASELINE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"immutable desktop-readability source unavailable: {relative_path}")
    return result.stdout


def normalize_start_here_desktop_html(relative_path, text):
    """Reverse only the exact new href, leaving every other HTML byte visible."""
    if not isinstance(text, str):
        raise TypeError("desktop-readability HTML normalization requires decoded text")
    if relative_path != "start-here.html":
        return text
    baseline = _baseline_bytes("start-here.html").decode("utf-8")
    matches = re.findall(r'<link\b[^>]*href="([^"]+)"[^>]*>', baseline)
    expected_hrefs = [href for href in matches if href.startswith("start-here.css?v=")]
    if len(expected_hrefs) != 1:
        raise AssertionError("e846ce3 must contain exactly one Start Here CSS href")
    baseline_href = expected_hrefs[0]
    count = text.count(DESKTOP_CSS_HREF)
    if count > 1:
        raise AssertionError("duplicate exact Start Here desktop CSS href")
    if count == 1:
        text = text.replace(DESKTOP_CSS_HREF, baseline_href, 1)
    return text


def restore_start_here_desktop_asset(relative_path, data):
    """Verify the complete desktop CSS hash and return the exact e846ce3 bytes."""
    if relative_path != "start-here.css":
        raise AssertionError(f"not an authorized desktop-readability asset: {relative_path}")
    baseline = _baseline_bytes("start-here.css")
    if data == baseline:
        return baseline
    observed = hashlib.sha256(data).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", DESKTOP_CSS_SHA256):
        raise AssertionError(
            "parent must refresh tests/start_here_desktop_baseline.py: "
            f"DESKTOP_CSS_SHA256 with the finalized start-here.css SHA-256 ({observed})"
        )
    if observed != DESKTOP_CSS_SHA256:
        raise AssertionError(f"Start Here desktop CSS fingerprint mismatch: {observed}")
    return baseline
