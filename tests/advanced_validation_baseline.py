"""Narrow scope helpers for advanced tutorial validation corrections.

The workflow and one input-preparation asset require exact complete-byte hashes.
Listed article corrections are restored to the exact PR14 source first; the
established PR7–14 scope restorers still run on that restored content. Only the
OrthoFinder and spatial testing-disclosure paragraphs may change outside bodies.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests/fixtures/advanced-validation-edits.json"
PUBLISHED_BASELINE = "d581217c96a8100d42ab919e1e26816cdcf1a7bb"
WORKFLOW_PATH = ".github/workflows/tutorial-platforms.yml"
WORKFLOW_SHA256_PLACEHOLDER = "REFRESH_REQUIRED_AFTER_WORKFLOW_CREATION"
ASSET_PATH = "files/visium-example/prepare_inputs.py"
DISCLOSURE_PATHS = frozenset({
    "tutorials/phylogenomics-orthofinder.html",
    "tutorials/spatial-transcriptomics-r-python.html",
})
DISCLOSURE = re.compile(rb'<p class="text-sm text-gray-600 mb-2">.*?</p>', re.S)
ARTICLE = re.compile(
    rb"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
DATE_MODIFIED = re.compile(rb'("dateModified"\s*:\s*")([^"]+)(")')
UPDATED = re.compile(rb"Updated (\d{1,2} [A-Za-z]+ \d{4})")
SITEMAP_ROW = re.compile(rb"<url>\s*<loc>([^<]+)</loc>.*?</url>", re.S)
LASTMOD = re.compile(rb"<lastmod>([^<]+)</lastmod>")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_manifest():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise AssertionError("unsupported advanced-validation manifest schema")
    if manifest.get("baseline_commit") != PUBLISHED_BASELINE:
        raise AssertionError("advanced-validation baseline SHA pin changed")
    workflow = manifest.get("workflow", {})
    if workflow.get("path") != WORKFLOW_PATH:
        raise AssertionError("advanced-validation workflow path must remain exact")
    if not isinstance(workflow.get("sha256"), str):
        raise AssertionError("advanced-validation workflow fingerprint is missing")
    article_paths = manifest.get("allowed_article_paths", [])
    files = manifest.get("articles", {})
    if (not isinstance(article_paths, list) or len(article_paths) != len(set(article_paths))
            or set(files) != set(article_paths)):
        raise AssertionError("article entries must exactly match the explicit allowlist")
    if article_paths and any(not p.startswith("tutorials/") or not p.endswith(".html")
                             for p in article_paths):
        raise AssertionError("advanced-validation article allowlist may contain tutorial HTML only")
    asset_paths = manifest.get("allowed_asset_paths", [])
    assets = manifest.get("assets", {})
    if (asset_paths not in ([], [ASSET_PATH]) or set(assets) != set(asset_paths)):
        raise AssertionError("only the exact Visium helper asset may be explicitly allowlisted")
    return manifest


def allowed_article_paths():
    return frozenset(load_manifest()["allowed_article_paths"])


def allowed_asset_paths():
    return frozenset(load_manifest().get("allowed_asset_paths", []))


def published_bytes(relative_path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_BASELINE}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned PR14 source missing: {relative_path}")
    return result.stdout


def workflow_bytes_match(relative_path, data, expected_sha256):
    """Pure exact-path/hash predicate, also usable for mutation tests."""
    return (
        relative_path == WORKFLOW_PATH
        and isinstance(expected_sha256, str)
        and _SHA256.fullmatch(expected_sha256) is not None
        and hashlib.sha256(data).hexdigest() == expected_sha256
    )


def is_approved_workflow(relative_path, data):
    """True only for the one workflow path with its reviewed full-file hash."""
    if relative_path != WORKFLOW_PATH:
        return False
    expected = load_manifest()["workflow"]["sha256"]
    if not _SHA256.fullmatch(expected):
        raise AssertionError(
            "tutorial-platforms.yml fingerprint not finalized; after review run "
            "sha256sum .github/workflows/tutorial-platforms.yml and replace the "
            "workflow.sha256 placeholder in tests/fixtures/advanced-validation-edits.json"
        )
    return workflow_bytes_match(relative_path, data, expected)


def _restore_registered_page(relative_path, data, entry, original):
    """Restore one manifest-pinned PR14 body/date and optional exact disclosure."""
    old_articles = list(ARTICLE.finditer(original))
    current_articles = list(ARTICLE.finditer(data))
    if len(old_articles) != 1 or len(current_articles) != 1:
        raise AssertionError(f"expected one article in {relative_path}")
    current_article = current_articles[0]
    current_digest = hashlib.sha256(current_article.group("body")).hexdigest()
    original_digest = hashlib.sha256(old_articles[0].group("body")).hexdigest()
    if current_digest not in {entry["article_body_sha256"], original_digest}:
        raise AssertionError(f"unregistered or stale article-body edit in {relative_path}")

    old_date = entry["date_modified_original"].encode("ascii")
    approved_date = entry["date_modified_approved"].encode("ascii")
    date_matches = list(DATE_MODIFIED.finditer(data))
    if len(date_matches) != 1 or date_matches[0].group(2) not in {old_date, approved_date}:
        raise AssertionError(f"unapproved dateModified in {relative_path}")
    match = date_matches[0]
    data = data[:match.start(2)] + old_date + data[match.end(2):]

    old_label = entry.get("visible_updated_original")
    approved_label = entry.get("visible_updated_approved")
    update_matches = list(UPDATED.finditer(data))
    if old_label is None or approved_label is None:
        if old_label is not None or approved_label is not None or update_matches:
            raise AssertionError(f"unapproved visible Updated label in {relative_path}")
    else:
        old_bytes, approved_bytes = old_label.encode("utf-8"), approved_label.encode("utf-8")
        if len(update_matches) != 1 or update_matches[0].group(1) not in {old_bytes, approved_bytes}:
            raise AssertionError(f"unapproved visible Updated date in {relative_path}")
        match = update_matches[0]
        data = data[:match.start(1)] + old_bytes + data[match.end(1):]

    disclosure = entry.get("outside_disclosure")
    if disclosure is not None:
        if relative_path not in DISCLOSURE_PATHS or not isinstance(disclosure, dict):
            raise AssertionError(f"invalid outside-article disclosure entry in {relative_path}")
        old_text, approved_text = disclosure.get("original"), disclosure.get("approved")
        if (not isinstance(old_text, str) or not old_text or not isinstance(approved_text, str)
                or not approved_text or old_text == approved_text):
            raise AssertionError(f"invalid exact disclosure pair in {relative_path}")
        old_bytes, approved_bytes = old_text.encode("utf-8"), approved_text.encode("utf-8")
        if (not DISCLOSURE.fullmatch(old_bytes) or not DISCLOSURE.fullmatch(approved_bytes)
                or original.count(old_bytes) != 1):
            raise AssertionError(f"unapproved disclosure paragraph boundary in {relative_path}")
        old_count, approved_count = data.count(old_bytes), data.count(approved_bytes)
        if (old_count, approved_count) not in {(1, 0), (0, 1)}:
            raise AssertionError(f"unapproved outside-article disclosure in {relative_path}")
        if approved_count:
            data = data.replace(approved_bytes, old_bytes, 1)

    # Restoring the article body only preserves every wrapper/surrounding byte.
    current_article = list(ARTICLE.finditer(data))[0]
    old_article = old_articles[0]
    return (data[:current_article.start("body")]
            + original[old_article.start("body"):old_article.end("body")]
            + data[current_article.end("body"):])


def normalize_advanced_validation_edit(relative_path, data):
    """Restore only an explicitly registered exact article body/date delta."""
    manifest = load_manifest()
    if relative_path not in manifest["articles"]:
        raise AssertionError(f"path is not explicitly article-allowlisted: {relative_path}")
    return _restore_registered_page(
        relative_path, data, manifest["articles"][relative_path], published_bytes(relative_path)
    )


def normalize_advanced_validation_if_allowed(relative_path, text):
    """Apply PR14 restoration when registered; otherwise preserve input unchanged."""
    if relative_path not in allowed_article_paths():
        return text
    if isinstance(text, str):
        return normalize_advanced_validation_edit(relative_path, text.encode("utf-8")).decode("utf-8")
    return normalize_advanced_validation_edit(relative_path, text)


def normalize_advanced_then_historical(relative_path, text):
    """Restore PR14 first, then run the unchanged historical PR8–14 helpers."""
    text = normalize_advanced_validation_if_allowed(relative_path, text)
    # Lazy imports avoid coupling legacy helpers to the new manifest at import time.
    from beginner_walkthrough_baseline import normalize_beginner_walkthrough_revision
    from six_lesson_revision_baseline import normalize_six_lesson_revision
    from tidyverse_setup_baseline import normalize_tidyverse_setup_revision
    from ubuntu_tidyverse_baseline import normalize_ubuntu_tidyverse_revision
    from remaining_validation_baseline import (
        allowed_paths as remaining_paths,
        normalize_remaining_validation_edit,
    )
    text = normalize_beginner_walkthrough_revision(relative_path, text)
    text = normalize_six_lesson_revision(relative_path, text)
    text = normalize_tidyverse_setup_revision(relative_path, text)
    text = normalize_ubuntu_tidyverse_revision(relative_path, text)
    if relative_path in remaining_paths():
        text = normalize_remaining_validation_edit(relative_path, text)
    return text


def normalize_advanced_validation_sitemap(data):
    """Restore only explicitly registered article lastmod values to PR14."""
    manifest = load_manifest()
    return _restore_registered_sitemap(data, manifest["allowed_article_paths"], manifest["articles"])


def advanced_asset_bytes_match(relative_path, data, original_sha256, approved_sha256):
    """True only for the one exact asset path and its complete reviewed bytes."""
    return (
        relative_path == ASSET_PATH
        and _SHA256.fullmatch(original_sha256 or "") is not None
        and _SHA256.fullmatch(approved_sha256 or "") is not None
        and hashlib.sha256(data).hexdigest() == approved_sha256
    )


def normalize_advanced_validation_asset(relative_path, data):
    """Restore the exact manifest-pinned Visium helper bytes to PR14."""
    manifest = load_manifest()
    if relative_path not in manifest.get("assets", {}):
        raise AssertionError(f"path is not explicitly asset-allowlisted: {relative_path}")
    entry = manifest["assets"][relative_path]
    original = published_bytes(relative_path)
    original_sha = hashlib.sha256(original).hexdigest()
    if entry.get("original_sha256") != original_sha:
        raise AssertionError(f"pinned PR14 asset hash changed: {relative_path}")
    if not advanced_asset_bytes_match(
            relative_path, data, entry.get("original_sha256"), entry.get("approved_sha256")):
        if hashlib.sha256(data).hexdigest() != original_sha:
            raise AssertionError(f"unapproved or stale full-file asset bytes: {relative_path}")
    return original


def normalize_advanced_validation_asset_if_allowed(relative_path, data):
    """Restore the exact asset when allowlisted; otherwise leave bytes unchanged."""
    if relative_path not in allowed_asset_paths():
        return data
    return normalize_advanced_validation_asset(relative_path, data)


def _restore_registered_sitemap(data, article_paths, entries):
    """Pure sitemap operation shared with mutation regressions."""
    for relative_path in article_paths:
        entry = entries[relative_path]
        target = ("https://theomicshub.com/" + relative_path).encode("ascii")
        rows = [match for match in SITEMAP_ROW.finditer(data) if match.group(1) == target]
        if len(rows) != 1:
            raise AssertionError(f"expected one sitemap row for {relative_path}")
        row_match = rows[0]
        row = row_match.group(0)
        matches = list(LASTMOD.finditer(row))
        if len(matches) != 1:
            raise AssertionError(f"expected one sitemap lastmod for {relative_path}")
        match = matches[0]
        old_date = entry["sitemap_lastmod_original"].encode("ascii")
        approved_date = entry["sitemap_lastmod_approved"].encode("ascii")
        if match.group(1) not in {old_date, approved_date}:
            raise AssertionError(f"unapproved sitemap lastmod for {relative_path}")
        restored = row[:match.start(1)] + old_date + row[match.end(1):]
        data = data[:row_match.start()] + restored + data[row_match.end():]
    return data
