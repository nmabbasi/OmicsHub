"""Narrow restoration helpers for the remaining tutorial validation edits.

Only an exact article-body SHA-256 recorded in the reviewed manifest may be
restored to the pinned pre-task source. Wrappers and every surrounding byte
remain visible to historical scope guards.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from advanced_validation_baseline import normalize_advanced_validation_if_allowed
from start_here_baseline import normalize_start_here_sitemap
from tutorial_ui_baseline import normalize_tutorial_ui

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests/fixtures/remaining-validation-edits.json"
PUBLISHED_BASELINE = "f218d1b6c711a5a50fff8c8af67f2b3d9bf7201c"
ARTICLE = re.compile(
    rb"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.S | re.I,
)
DATE_MODIFIED = re.compile(rb'("dateModified"\s*:\s*")([^"]+)(")')
UPDATED = re.compile(rb"Updated (\d{1,2} [A-Za-z]+ \d{4})")
SITEMAP_ROW = re.compile(rb"<url>\s*<loc>([^<]+)</loc>.*?</url>", re.S)
LASTMOD = re.compile(rb"<lastmod>([^<]+)</lastmod>")


def load_manifest():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise AssertionError("unsupported remaining-validation manifest schema")
    if manifest.get("baseline_commit") != PUBLISHED_BASELINE:
        raise AssertionError("remaining-validation baseline SHA pin changed")
    if set(manifest.get("files", {})) != set(manifest.get("allowed_paths", [])):
        raise AssertionError("manifest file entries must exactly match its explicit allowlist")
    return manifest


def allowed_paths():
    return frozenset(load_manifest()["allowed_paths"])


def published_bytes(relative_path):
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_BASELINE}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned pre-task source missing: {relative_path}")
    return result.stdout


def _entry(relative_path):
    manifest = load_manifest()
    if relative_path not in manifest["files"]:
        raise AssertionError(f"path is not explicitly allowlisted: {relative_path}")
    return manifest["files"][relative_path]


def restore_page_to_published(relative_path, data):
    """Restore only exact approved body/date deltas; leave wrappers byte-visible."""
    data = normalize_tutorial_ui(relative_path, data.decode("utf-8")).encode("utf-8")
    entry = _entry(relative_path)
    original = normalize_tutorial_ui(
        relative_path, published_bytes(relative_path).decode("utf-8")
    ).encode("utf-8")
    original_articles = list(ARTICLE.finditer(original))
    current_articles = list(ARTICLE.finditer(data))
    if len(original_articles) != 1 or len(current_articles) != 1:
        raise AssertionError(f"expected one article in {relative_path}")
    current_match = current_articles[0]
    digest = hashlib.sha256(current_match.group("body")).hexdigest()
    if digest != entry["article_body_sha256"]:
        raise AssertionError(
            f"unregistered or stale article-body edit in {relative_path}: {digest}"
        )

    old_modified = entry["date_modified_original"].encode("ascii")
    approved_modified = entry["date_modified_approved"].encode("ascii")
    date_matches = list(DATE_MODIFIED.finditer(data))
    if len(date_matches) != 1:
        raise AssertionError(f"expected exactly one dateModified in {relative_path}")
    match = date_matches[0]
    if match.group(2) not in {old_modified, approved_modified}:
        raise AssertionError(f"unapproved dateModified in {relative_path}")
    data = data[:match.start(2)] + old_modified + data[match.end(2):]

    old_label = entry["visible_updated_original"]
    approved_label = entry["visible_updated_approved"]
    update_matches = list(UPDATED.finditer(data))
    if old_label is None or approved_label is None:
        if old_label is not None or approved_label is not None or update_matches:
            raise AssertionError(f"unapproved visible Updated label added/removed in {relative_path}")
    else:
        old_updated = old_label.encode("utf-8")
        approved_updated = approved_label.encode("utf-8")
        if len(update_matches) != 1:
            raise AssertionError(f"expected exactly one visible Updated label in {relative_path}")
        update_match = update_matches[0]
        if update_match.group(1) not in {old_updated, approved_updated}:
            raise AssertionError(f"unapproved visible Updated date in {relative_path}")
        data = data[:update_match.start(1)] + old_updated + data[update_match.end(1):]

    # Replace only the body after verifying its exact complete approved digest.
    current_match = list(ARTICLE.finditer(data))[0]
    original_article = original_articles[0]
    return (
        data[:current_match.start("body")]
        + original[original_article.start("body"):original_article.end("body")]
        + data[current_match.end("body"):]
    )


def normalize_remaining_validation_edit(relative_path, text):
    """Restore PR14 first, then the older remaining-validation snapshot."""
    text = normalize_advanced_validation_if_allowed(relative_path, text)
    return restore_page_to_published(relative_path, text.encode("utf-8")).decode("utf-8")


def restore_sitemap_to_published(data):
    """Restore only manifest-allowlisted lastmod values in exact URL rows."""
    manifest = load_manifest()
    for relative_path in manifest["allowed_paths"]:
        entry = manifest["files"][relative_path]
        target = ("https://theomicshub.com/" + relative_path).encode("ascii")
        rows = [match for match in SITEMAP_ROW.finditer(data)
                if match.group(1) == target]
        if len(rows) != 1:
            raise AssertionError(f"expected one sitemap row for {relative_path}")
        row_match = rows[0]
        row = row_match.group(0)
        lastmods = list(LASTMOD.finditer(row))
        if len(lastmods) != 1:
            raise AssertionError(f"expected one sitemap lastmod for {relative_path}")
        lastmod = lastmods[0]
        old_date = entry["sitemap_lastmod_original"].encode("ascii")
        approved_date = entry["sitemap_lastmod_approved"].encode("ascii")
        if lastmod.group(1) not in {old_date, approved_date}:
            raise AssertionError(f"unapproved sitemap lastmod for {relative_path}")
        restored_row = row[:lastmod.start(1)] + old_date + row[lastmod.end(1):]
        data = data[:row_match.start()] + restored_row + data[row_match.end():]
    return data


def normalize_remaining_validation_sitemap(data):
    from advanced_validation_baseline import normalize_advanced_validation_sitemap
    restored = restore_sitemap_to_published(normalize_advanced_validation_sitemap(data))
    return normalize_start_here_sitemap(restored)
