"""Exact normalization layer for the Option 1A homepage laptop redesign and site-wide icon footer sync.

Peels only the exact pinned homepage/footer files (`index.html`, `404.html`,
`style.css`, `script.js`, and regenerated `home-page.min.css`) back to parent
commit 8cfe69916e01724bdcb85d717a9e6af4d646c289 so older historical fixtures
keep validating their pinned revisions unchanged. Any unknown mutation is
returned untouched so historical scope checks continue to detect unexpected edits.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "8cfe69916e01724bdcb85d717a9e6af4d646c289"

PINNED_FILES = {
    "index.html": {
        "base_sha256": "e0e0505fab71546fd27c7aea3be9f2bbf8399c6fec3ded42c8be30f8fa6f7e3d",
        "current_sha256": "865f2a7428694706e08ae6fba535f56cf0203e1128f34ded52c5d805613e8a02",
    },
    "404.html": {
        "base_sha256": "51dcbd37197875cda5980e293d3f2eb5b3f21bcd37acd7a52755673ed7b70a3f",
        "current_sha256": "2068fab613bc81d71a92b9d83da21d232e84d1382cf1f5b1756399c3b82bf431",
    },
    "start-here.html": {
        "base_sha256": "db639b9af40bd2d8793142db57d47d251b3bb3310505bf1d39390332cf51933c",
        "current_sha256": "c616875985d820f4a7124b46ad560bbfc9e7ea5ef9dcbdfaf7f7944f513dca04",
    },
    "tutorials.html": {
        "base_sha256": "169a31770f4ff89568c7088ad97c7b61bdb576abed561e50067dae4f6c1bf887",
        "current_sha256": "549120377a12103606d87e0d01d6a0972a08249438097e0b6f4e565eb1811380",
    },
    "style.css": {
        "base_sha256": "8f79a8a4ab7980d7fd04f2f135b9d8d559fb7c7e8f9cdf70f384dceab06289b6",
        "current_sha256": "4a8e94d6159c0d1e8469f2994887feb7372d5f2a4ca6e9213c5ad08eb68499f3",
    },
    "script.js": {
        "base_sha256": "4fa68baa23f4597e83327dc02e25b646b908aba116ed90764670039019aaa40c",
        "current_sha256": "8ad4988ea589ae7bdaa44bfe6bf7d2de326c94f7a93e9951222a04c668ccb596",
    },
    "home-page.min.css": {
        "base_sha256": "588d5286a85d9d23357f9c06d647d9c3c9ba0c65ab238975d5c13e7877cc1e6a",
        "current_sha256": "d1df1f4dd7508cf1f75ce01e25a430b7f3ecefc9be88e7653124cc21e2c7ae91",
    },
    "cookie-consent.js": {
        "base_sha256": "c9b21ce57c609be336dfe869928349cd8c536281f807621d54b3ed3df19ec972",
        "current_sha256": "dba0aa40f6ce0081301d1d8d3b658da744bdde3a4ff2ecc34a8363693b0174a4",
    },
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=None)
def _base_bytes(relative_path: str) -> bytes | None:
    if relative_path not in PINNED_FILES:
        return None
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode != 0:
        return None
    data = result.stdout
    if _sha(data) != PINNED_FILES[relative_path]["base_sha256"]:
        raise AssertionError(f"homepage-redesign base digest mismatch: {relative_path}")
    return data


def normalize_homepage_redesign_bytes(relative_path: str, data: bytes) -> bytes:
    """Restore only an exact pinned homepage-redesign file to its 8cfe6991 bytes."""
    if not isinstance(data, bytes):
        raise TypeError("homepage-redesign byte normalization requires bytes")
    entry = PINNED_FILES.get(relative_path)
    if entry is None:
        return data
    observed = _sha(data)
    if observed == entry["base_sha256"]:
        return data
    if observed != entry["current_sha256"]:
        return data
    original = _base_bytes(relative_path)
    if original is None:
        return data
    return original


def normalize_homepage_redesign(relative_path: str, text: str) -> str:
    """UTF-8 text wrapper around the exact homepage-redesign normalizer."""
    if not isinstance(text, str):
        raise TypeError("homepage-redesign normalization requires decoded text")
    if relative_path not in PINNED_FILES:
        return text
    return normalize_homepage_redesign_bytes(relative_path, text.encode("utf-8")).decode("utf-8")
