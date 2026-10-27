"""Narrow baseline adapter for the full-width Tutorials catalogue banner."""
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BANNER_BASELINE_COMMIT = "3a3b90bd0515930af00ae56a7a0c6c75814ef27a"
CATALOGUE_CSS_SHA256 = "bb5d49b07212f011917b4fa7498c8b8e1fdf05a3081dded7b07e0e142cfb1c4e"


def _show_bytes(spec):
    result = subprocess.run(
        ["git", "show", spec], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"immutable catalogue banner source unavailable: {spec}")
    return result.stdout


def restore_home_catalogue_banner_asset(relative_path, data):
    """Verify the full-width catalogue banner stylesheet and return exact 3a3b90b bytes."""
    if relative_path != "home-catalogue.css":
        raise AssertionError(f"not an authorized catalogue stylesheet: {relative_path}")
    baseline = _show_bytes(f"{BANNER_BASELINE_COMMIT}:home-catalogue.css")
    if data == baseline:
        return baseline
    observed = hashlib.sha256(data).hexdigest()
    if observed != CATALOGUE_CSS_SHA256:
        raise AssertionError(f"catalogue banner restoration CSS fingerprint mismatch: {observed}")
    return baseline
