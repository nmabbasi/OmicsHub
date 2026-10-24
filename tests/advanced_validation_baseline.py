"""Narrow scope helpers for advanced tutorial validation infrastructure.

The only currently authorized public change is the exact new workflow path,
whose complete bytes must match the SHA-256 in the companion manifest. Future
article corrections require explicit manifest entries and are restored only
from their exact approved article-body digest and exact date values; wrappers
and all other bytes remain visible to the historical scope guards.
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
    if set(files) != set(article_paths):
        raise AssertionError("article entries must exactly match the explicit allowlist")
    if article_paths and any(not p.startswith("tutorials/") or not p.endswith(".html")
                             for p in article_paths):
        raise AssertionError("advanced-validation article allowlist may contain tutorial HTML only")
    return manifest


def allowed_article_paths():
    return frozenset(load_manifest()["allowed_article_paths"])


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


def normalize_advanced_validation_edit(relative_path, data):
    """Restore only an explicitly registered exact article body/date delta.

    The initial manifest intentionally has no article paths. For a later
    authorized correction, add its path and exact approved body digest/date
    pairs to the manifest, then call this before the older PR7-13 normalizers
    in the aggregate scope checks. Every historical normalizer must still run.
    """
    manifest = load_manifest()
    if relative_path not in manifest["articles"]:
        raise AssertionError(f"path is not explicitly article-allowlisted: {relative_path}")
    entry = manifest["articles"][relative_path]
    original = published_bytes(relative_path)
    old_articles = list(ARTICLE.finditer(original))
    current_articles = list(ARTICLE.finditer(data))
    if len(old_articles) != 1 or len(current_articles) != 1:
        raise AssertionError(f"expected one article in {relative_path}")
    current_article = current_articles[0]
    if hashlib.sha256(current_article.group("body")).hexdigest() != entry["article_body_sha256"]:
        raise AssertionError(f"unregistered or stale article-body edit in {relative_path}")

    old_date = entry["date_modified_original"].encode("ascii")
    approved_date = entry["date_modified_approved"].encode("ascii")
    date_matches = list(DATE_MODIFIED.finditer(data))
    if len(date_matches) != 1 or date_matches[0].group(2) not in {old_date, approved_date}:
        raise AssertionError(f"unapproved dateModified in {relative_path}")
    match = date_matches[0]
    data = data[:match.start(2)] + old_date + data[match.end(2):]

    original_label = entry.get("visible_updated_original")
    approved_label = entry.get("visible_updated_approved")
    update_matches = list(UPDATED.finditer(data))
    if original_label is None or approved_label is None:
        if original_label is not None or approved_label is not None or update_matches:
            raise AssertionError(f"unapproved visible Updated label in {relative_path}")
    else:
        if len(update_matches) != 1 or update_matches[0].group(1) not in {
            original_label.encode("utf-8"), approved_label.encode("utf-8")
        }:
            raise AssertionError(f"unapproved visible Updated date in {relative_path}")
        match = update_matches[0]
        data = data[:match.start(1)] + original_label.encode("utf-8") + data[match.end(1):]

    current_article = list(ARTICLE.finditer(data))[0]
    old_article = old_articles[0]
    return (data[:current_article.start("body")]
            + original[old_article.start("body"):old_article.end("body")]
            + data[current_article.end("body"):])


def normalize_advanced_validation_sitemap(data):
    """Restore only explicitly registered article lastmod values, if any."""
    manifest = load_manifest()
    for relative_path in manifest["allowed_article_paths"]:
        entry = manifest["articles"][relative_path]
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
