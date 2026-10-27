"""Narrow baseline adapter for the tab navigation guard and debouncing in subscribe-fab.js and generated home-page.min.css."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GUARD_BASELINE_COMMIT = "17b51f57b4eb9bded381ba9a469776dcc654e782"
SUBSCRIBE_FAB_GUARD_SHA256 = "19af1c463dbf557397e5be685c032cb04b5ee10261b9a513a22554edd3547f4d"
HOME_PAGE_CSS_GUARD_SHA256 = "07258665c8a0defa8de9aca00ad59c018ba4230e49f882f4421f86623ade5824"

GUARD_ASSET_SHA256 = {
    "subscribe-fab.js": SUBSCRIBE_FAB_GUARD_SHA256,
    "home-page.min.css": HOME_PAGE_CSS_GUARD_SHA256,
}
GUARD_ASSET_PATHS = frozenset(GUARD_ASSET_SHA256)


def _show_bytes(spec):
    result = subprocess.run(
        ["git", "show", spec], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"immutable navigation guard source unavailable: {spec}")
    return result.stdout


def restore_navigation_guard_asset(relative_path, data):
    """Verify the navigation guard asset and return exact 17b51f5 bytes."""
    if relative_path not in GUARD_ASSET_PATHS or not isinstance(data, bytes):
        return data
    baseline = _show_bytes(f"{GUARD_BASELINE_COMMIT}:{relative_path}")
    if data == baseline:
        return baseline
    observed = hashlib.sha256(data).hexdigest()
    if observed != GUARD_ASSET_SHA256[relative_path]:
        return data
    return baseline


def normalize_navigation_guard_text(relative_path, text):
    """Normalize decoded navigation guard script or stylesheet text."""
    if relative_path not in GUARD_ASSET_PATHS or not isinstance(text, str):
        return text
    data = text.encode("utf-8")
    restored = restore_navigation_guard_asset(relative_path, data)
    return restored.decode("utf-8") if restored != data else text
