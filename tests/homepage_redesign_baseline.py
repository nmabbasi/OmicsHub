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
        "current_sha256": "7114d7e4dc9a51a8004edc09d6b31e4d5299d641ae89ba6e96d988402229d988",
    },
    "404.html": {
        "base_sha256": "51dcbd37197875cda5980e293d3f2eb5b3f21bcd37acd7a52755673ed7b70a3f",
        "current_sha256": "fa3dbf1b975be09b798c47fabe2cdfb8be8b6e71504facd482256403d1a67628",
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
        "current_sha256": "a8cce2200083265366f4d6b654d466d9106e40dc523b5cd6ae19b7ee39cc1534",
    },
    "script.js": {
        "base_sha256": "4fa68baa23f4597e83327dc02e25b646b908aba116ed90764670039019aaa40c",
        "current_sha256": "97e316dd27b8673f1a31dd9e8888f105acc395ff89d4e13f53fd2eb0524a1ca8",
    },
    "home-page.min.css": {
        "base_sha256": "588d5286a85d9d23357f9c06d647d9c3c9ba0c65ab238975d5c13e7877cc1e6a",
        "current_sha256": "65073b8c3be8e09ba5a5332e1fd12b5bddc92dfaaae4ad88eb4be21fa0dba639",
    },
    "cookie-consent.js": {
        "base_sha256": "c9b21ce57c609be336dfe869928349cd8c536281f807621d54b3ed3df19ec972",
        "current_sha256": "dba0aa40f6ce0081301d1d8d3b658da744bdde3a4ff2ecc34a8363693b0174a4",
    },
    "mobile-navigation.js": {
        "base_sha256": "fce1906ee3ef35e827738c52ca741db9f2178da3d6a7136b9a8a276f3138c4a5",
        "current_sha256": "c9eadaf8b59d9c8ad9dffbd9392429735e101988c85983bd81b4668c9b21efc8",
    },
    "tutorial-library.css": {
        "base_sha256": "a9a0c78eef17c47177886d241643d3f292a28d93049a163f5ec6a693f7dab45d",
        "current_sha256": "3c4bfc28d355a02678ea377d86854e413777cae71a910135c69a25c1e5e9422c",
    },
    "tutorial-reader.css": {
        "base_sha256": "ed840bbf32d42c3a10c46bec36bed1cf49fa2ee3aa753312e6be42a18869ea1b",
        "current_sha256": "eb6ed4e2ac71699d3e042298932c9f732a11fd5c632779508358aaf44f954f48",
    },
    "home-catalogue.css": {
        "base_sha256": "bb5d49b07212f011917b4fa7498c8b8e1fdf05a3081dded7b07e0e142cfb1c4e",
        "current_sha256": "911def5351a015ed126d4c7e039905a476e37af8cc026638c275a9a84aecfae4",
    },
    "start-here.css": {
        "base_sha256": "95e06b81bfae634962e6078874ab0ba0de1e926ac472def734804102f29e1382",
        "current_sha256": "0241cf38279ec67910e0331fa6fd6ee496b5fd670a2d3dff13b32916bd8ee5c7",
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
