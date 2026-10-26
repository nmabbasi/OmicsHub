"""Exact, hash-pinned route-migration normalization for older regression layers.

The old route remains a zero-second redirect in the current tree. Historical
source tests still compare the active lesson with its pre-migration filename;
this adapter maps only the exact reviewed current bytes back to the parent
commit, leaving every unmatched edit visible.
"""
from pathlib import Path
import hashlib
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRE_MIGRATION_COMMIT = "3a3b90bd0515930af00ae56a7a0c6c75814ef27a"
OLD_ROUTE = "tutorials/autonomous-research-orchestrator.html"
NEW_ROUTE = "tutorials/rna-seq-count-matrix-qc-cpm.html"

# Complete current-file digests: edits beyond this exact migration are never
# normalized away. Test files and unrelated site assets are intentionally absent.
ROUTE_MIGRATION_SHA256 = {
    "autonomous-research-orchestrator.html": "b66bbe22e4c6c88d1c8a4525c4914f85d85b036573feac63f5c0df3301e53f84",
    "sitemap.xml": "ea4f4bdd5dc33677bc473f3712f747be466d073dccc0c8a7575a96ccf3a111c1",
    "tools/catalogue-learning.json": "19e263b70abfdfa8b05593d7ab7e1539267d262a814ba0756eb7b3e8f7bcc3cc",
    "tools/generate_catalogue_learning.py": "90569f792347580bcbd90d4affafaed9ec6cc03e4fe06f97b5d76c3fb1b6836f",
    "tools/generate_learning_paths.py": "5ed9baa9afa08dfbfe4c5f098d49bc771616cbc8f710a216efd02021829515c9",
    "tools/generate_legacy_redirects.py": "9370cfe73d30644c6e1a0757d121e92af26da0234e3c753a63fff71416a628a1",
    "tools/generate_tutorial_ui.py": "1749c49d2fa3fbf3689288af069b14ad5713154c5b784696ed183ad2a3457c6a",
    "tools/learning-paths.json": "d7238374d7e95a3359227c7d6d76a6fd76aafdaca2f6f70580b1a43291f87f56",
    "tools/legacy-redirects.json": "b0b8874508af464e3fb7ba4bd020aaf59307ea447e679b3f235392d3cbe10066",
    "tools/tutorial-code-groups.json": "694f34b1f1c61d02c94665bcf1e8ca7bb922bb33a06f9d45c0c43cb0e23cdad4",
    "tools/tutorial-code-languages.json": "f83cfaec0eac5f47c7a5f337e81565340cd12880c3ccb23ee27cbdfd34097e18",
    "tutorial-code-data.js": "473dde8451979bb07c30d7f1944c4d8554eddc9acf2e3b6707509015d51f0e51",
    "tutorials.html": "6626c4b0d4e5499dadd962af08e146edacea2e7fa4d760d8aca395909dfee434",
    "tutorials/advanced-ai-orchestration-bioinformatics.html": "959bee924a97b58c921265ba4be78918414ee93a9893506a7bf2be4efb66d411",
    "tutorials/ai-prompt-engineering-seurat.html": "83c02f81dbb390aff7fb3f5cc6b1de9fe6692d9b5f9b670ba6b582924d802995",
    OLD_ROUTE: "6fdd801d6a6f391cee84ab232ac4f7e7651fc5b2bc6aaa6f8bf5e5e92ecd0dd0",
    NEW_ROUTE: "6b42350cc458633f528d1ee92a8b7177cd87ac87ed8cad8e858336bcb6a46927",
}


def historical_route_path(relative_path):
    """Return the pre-move lesson filename for either current nested route."""
    return OLD_ROUTE if relative_path in {OLD_ROUTE, NEW_ROUTE} else relative_path


def current_route_path(relative_path):
    """Return the current lesson filename for the pre-move route key."""
    return NEW_ROUTE if relative_path == OLD_ROUTE else relative_path


def is_redirect_stub(path):
    """Recognize only pages explicitly marked as route redirect stubs."""
    try:
        return '<meta name="tutorial-route-redirect"' in Path(path).read_text(encoding="utf-8")
    except OSError:
        return False


def published_tutorial_paths(root=ROOT):
    """List lesson pages, excluding explicitly marked nested redirect stubs."""
    pages = []
    for path in (Path(root) / "tutorials").glob("*.html"):
        if not is_redirect_stub(path):
            pages.append(path)
    return sorted(pages)


def exact_route_migration_paths(root=ROOT):
    """Return only public paths whose complete bytes equal the pinned migration."""
    root = Path(root)
    matches = set()
    for relative_path, expected in ROUTE_MIGRATION_SHA256.items():
        path = root / relative_path
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            matches.add(relative_path)
    return matches


def pre_migration_bytes(relative_path):
    """Read one path from the fixed pre-migration commit, mapping the moved URL."""
    relative_path = historical_route_path(relative_path)
    if not isinstance(relative_path, str) or relative_path.startswith("/") or ".." in Path(relative_path).parts:
        raise AssertionError(f"invalid pre-migration path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{PRE_MIGRATION_COMMIT}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def normalize_route_migration(relative_path, data):
    """Restore only an exact route-migration file to its parent-commit bytes.

    Returns a ``(historical_path, bytes)`` pair. A hash mismatch is left intact
    so older guards continue to reveal unrelated or unreviewed edits.
    """
    if not isinstance(data, bytes):
        raise TypeError("route-migration normalization requires bytes")
    mapped_path = historical_route_path(relative_path)
    expected = ROUTE_MIGRATION_SHA256.get(relative_path)
    if expected is None or hashlib.sha256(data).hexdigest() != expected:
        return mapped_path, data
    original = pre_migration_bytes(mapped_path)
    if original is None:
        raise AssertionError(f"pre-migration source unavailable: {mapped_path}")
    return mapped_path, original


def normalize_route_migration_text(relative_path, text):
    """Text convenience wrapper that preserves strict UTF-8 handling."""
    if not isinstance(text, str):
        raise TypeError("route-migration text normalization requires decoded text")
    mapped_path, data = normalize_route_migration(relative_path, text.encode("utf-8"))
    return mapped_path, data.decode("utf-8")
