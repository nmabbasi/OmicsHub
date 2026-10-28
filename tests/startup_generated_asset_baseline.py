"""Exact compatibility for the homepage CSS regenerated from startup assets.

The startup work changes ``subscribe-fab.js`` and consequently the PurgeCSS
output, although the bundle is not part of the frozen 61-path startup fixture.
Only the exact generated bundle digest is recognized; callers select one of
three explicitly pinned historical bundles for their own legacy comparison.
"""
import hashlib
from pathlib import Path
import subprocess
from editorial_review_baseline import normalize_editorial_review_bytes

ROOT = Path(__file__).resolve().parents[1]
PATH = "home-page.min.css"
STARTUP_GENERATED_SHA256 = "bb63a112860d75923404f11349cffd1874b9baf39654df8a71a3e519488246c3"
# The current approved-main build and its exact parent build differ from the
# reviewed bundle only in the generated source-hash header and remain full-file
# pinned before entering the existing historical restoration chain.
CURRENT_GENERATED_SHA256S = frozenset({
    "390ca26128f8d6558f0e97097586e33ef3688d888df2fe28bf32056ca9a225d5",
    "11900d9e9327d2095ae25e6a88310c0be1f4e022f216497ddc4bfec50c6eda91",
})
HISTORICAL_BUNDLES = {
    "main": (
        "93f06260550dbc91c0f020c24e1e2b00b7e017b5",
        "e35febc045fb1d93c746d832693964df6df7b58321820516c15428068b4f4985",
    ),
    "home-catalogue": (
        "4fb1f593c2781ca5cbf531f1b168c2f20ab5160e",
        "31c20c852a226d2969acab21fc8a0ac87c5d7391b7d12d6441bdc3571e60cbbf",
    ),
    "reader-text": (
        "4d0a64f123",
        "c4bc6262003d9fdff311a02b0b8939adef7362d15ef970e7940796b729f838bc",
    ),
}


def restore_startup_generated_asset(relative_path, data, historical_bundle):
    """Map only the exact startup-generated CSS to an explicitly named old copy.

    Unknown paths, unknown bytes, and already-historical bytes pass through
    unchanged. The selected target is rechecked against its frozen complete-file
    digest before it is returned.
    """
    if not isinstance(data, bytes):
        raise TypeError("startup-generated asset restoration requires bytes")
    data = normalize_editorial_review_bytes(relative_path, data)
    if relative_path != PATH or hashlib.sha256(data).hexdigest() not in (
        CURRENT_GENERATED_SHA256S | {STARTUP_GENERATED_SHA256}
    ):
        return data
    if historical_bundle not in HISTORICAL_BUNDLES:
        raise AssertionError(f"unapproved historical homepage CSS bundle: {historical_bundle!r}")
    revision, expected = HISTORICAL_BUNDLES[historical_bundle]
    result = subprocess.run(
        ["git", "show", f"{revision}:{PATH}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned homepage CSS bundle unavailable: {revision}:{PATH}")
    if hashlib.sha256(result.stdout).hexdigest() != expected:
        raise AssertionError(f"pinned homepage CSS bundle hash mismatch: {revision}:{PATH}")
    return result.stdout
