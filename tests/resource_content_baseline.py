"""Exact-source restoration for the resource-dependent tutorial review batch.

Each manifest entry fingerprints the complete approved article body. It may also
restore the page's exact dateModified/visible Updated values, that page's exact
sitemap lastmod, and exact snippets for the fixed outside-article metadata
whitelist below. All wrappers and every other byte stay visible to historic
source guards.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import re
import subprocess

from tutorial_ui_baseline import normalize_tutorial_ui
from r_first_revision_baseline import R_FIRST_ASSET_SHA256, restore_r_first_asset
from route_migration_baseline import normalize_route_migration

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests/fixtures/resource-content-edits.json"
PUBLISHED_BASELINE = "5846304f76551252b97ca674f6020d2983901fca"
ARTICLE = re.compile(
    rb"(?P<open><article\b[^>]*>)(?P<body>.*?)(?P<close></article\s*>)",
    re.IGNORECASE | re.DOTALL,
)
DATE_MODIFIED = re.compile(rb'("dateModified"\s*:\s*")([^"]+)(")')
UPDATED = re.compile(rb"Updated (\d{1,2} [A-Za-z]+ \d{4})")
SITEMAP_ROW = re.compile(rb"<url>\s*<loc>([^<]+)</loc>.*?</url>", re.DOTALL)
LASTMOD = re.compile(rb"<lastmod>([^<]+)</lastmod>")
PRE_CODE = re.compile(
    rb"<pre\b[^>]*>.*?<code\b[^>]*>.*?</code>.*?</pre\s*>",
    re.IGNORECASE | re.DOTALL,
)
META_TAG = re.compile(rb"<meta\b[^>]*>", re.IGNORECASE | re.DOTALL)
IMG_TAG = re.compile(rb"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
SCRIPT_TAG = re.compile(rb"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
JSONLD_TYPE = re.compile(rb"\btype\s*=\s*([\"'])application/ld\+json\1", re.IGNORECASE)
ATTRIBUTE = re.compile(
    rb"(?P<full>\b(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?P<quote>[\"'])(?P<value>.*?)(?P=quote))",
    re.DOTALL,
)
JSONLD_DESCRIPTION = re.compile(rb'"description"\s*:\s*"(?:\\.|[^"\\])*"')

# Only these four pages may carry outside-article metadata deltas. The field
# selectors below identify only the relevant attribute/property, not whole tags.
METADATA_FIELD_WHITELIST = {
    "tutorials/ai-prompt-engineering-seurat.html": frozenset({
        "description_meta", "og_description", "twitter_description", "jsonld_description",
    }),
    "tutorials/ai-coding-cursor-aider.html": frozenset({
        "description_meta", "og_description", "twitter_description", "jsonld_description",
    }),
    "tutorials/docker-singularity-bioinformatics.html": frozenset({
        "description_meta", "og_description", "twitter_description", "jsonld_description",
    }),
    "tutorials/protein-structure-design-alphafold.html": frozenset({
        "hero_banner", "og_image", "twitter_image", "jsonld_image",
        "twitter_card", "keywords_meta",
    }),
}
_META_FIELD_SELECTORS = {
    "description_meta": ("name", "description", "content"),
    "og_description": ("property", "og:description", "content"),
    "twitter_description": ("name", "twitter:description", "content"),
    "keywords_meta": ("name", "keywords", "content"),
    "twitter_card": ("name", "twitter:card", "content"),
}
_ALPHAFOLD_IMAGE_SRC = {
    "tutorials/protein-structure-design-alphafold.html": b"../images/alphafold-esmfold.webp",
}
_IMAGE_URL = b"https://theomicshub.com/images/alphafold-esmfold.webp"


def _valid_path(path):
    return (
        isinstance(path, str)
        and path.startswith("tutorials/")
        and path.endswith(".html")
        and not path.startswith("/")
        and ".." not in Path(path).parts
        and "\\" not in path
    )


def _validate_date_pair(entry, old_key, approved_key, label, nullable=False):
    old, approved = entry.get(old_key), entry.get(approved_key)
    if nullable and old is None and approved is None:
        return
    if not isinstance(old, str) or not isinstance(approved, str):
        raise AssertionError(f"invalid {label} pair")
    if label.startswith("visible updated"):
        try:
            datetime.strptime(old, "%d %B %Y")
            datetime.strptime(approved, "%d %B %Y")
        except ValueError as exc:
            raise AssertionError(f"invalid {label} pair") from exc
        return
    if (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", old)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved)):
        raise AssertionError(f"invalid {label} pair")


def _attribute_values(tag, name):
    return [match for match in ATTRIBUTE.finditer(tag)
            if match.group("name").lower() == name.encode("ascii").lower()]


def _field_matches(data, relative_path, field):
    """Return absolute spans and exact snippets for one whitelisted field."""
    allowed = METADATA_FIELD_WHITELIST.get(relative_path, frozenset())
    if field not in allowed:
        raise AssertionError(f"metadata field {field!r} is not authorized for {relative_path}")
    found = []
    if field in _META_FIELD_SELECTORS:
        identity_name, identity_value, value_name = _META_FIELD_SELECTORS[field]
        for tag_match in META_TAG.finditer(data):
            tag = tag_match.group(0)
            identity = _attribute_values(tag, identity_name)
            if len(identity) != 1 or identity[0].group("value").lower() != identity_value.encode("ascii"):
                continue
            values = _attribute_values(tag, value_name)
            if len(values) != 1:
                raise AssertionError(f"expected one {field} attribute in {relative_path}")
            attr = values[0]
            start = tag_match.start() + attr.start("full")
            end = tag_match.start() + attr.end("full")
            found.append((start, end, data[start:end]))
    elif field in {"og_image", "twitter_image"}:
        identity_name, identity_value = (
            ("property", "og:image") if field == "og_image"
            else ("name", "twitter:image")
        )
        tags = []
        for tag_match in META_TAG.finditer(data):
            values = _attribute_values(tag_match.group(0), identity_name)
            if len(values) == 1 and values[0].group("value").lower() == identity_value.encode("ascii"):
                tags.append(tag_match)
        # Fixed neighboring metadata tags delimit the original position even
        # when the approved snippet removes the target image tag.
        if field == "og_image":
            before = _find_meta_tag(data, "property", "og:type")
            after = _find_meta_tag(data, "name", "twitter:card")
        else:
            before = _find_meta_tag(data, "name", "twitter:description")
            after = _literal_span(data, b"<title>")
        if len(tags) > 1 or before is None or after is None or before[1] > after[0]:
            raise AssertionError(f"cannot locate exact {field} region in {relative_path}")
        found.append((before[1], after[0], data[before[1]:after[0]]))
    elif field == "jsonld_image":
        before_matches = list(re.finditer(
            rb'"mainEntityOfPage"\s*:\s*\{.*?\n\s*\},', data, re.DOTALL
        ))
        after_matches = list(re.finditer(rb'"author"\s*:', data))
        if len(before_matches) != 1 or len(after_matches) != 1 or before_matches[0].end() > after_matches[0].start():
            raise AssertionError(f"cannot locate exact JSON-LD image region in {relative_path}")
        found.append((before_matches[0].end(), after_matches[0].start(),
                      data[before_matches[0].end():after_matches[0].start()]))
    elif field == "hero_image_alt":
        expected_src = _ALPHAFOLD_IMAGE_SRC.get(relative_path)
        if expected_src is None:
            raise AssertionError(f"hero image selector is not authorized for {relative_path}")
        for tag_match in IMG_TAG.finditer(data):
            tag = tag_match.group(0)
            src = _attribute_values(tag, "src")
            if len(src) != 1 or src[0].group("value") != expected_src:
                continue
            alts = _attribute_values(tag, "alt")
            if len(alts) != 1:
                raise AssertionError(f"expected one hero image alt attribute in {relative_path}")
            attr = alts[0]
            start = tag_match.start() + attr.start("full")
            end = tag_match.start() + attr.end("full")
            found.append((start, end, data[start:end]))
    elif field == "hero_banner":
        expected_src = _ALPHAFOLD_IMAGE_SRC.get(relative_path)
        if expected_src is None:
            raise AssertionError(f"hero banner selector is not authorized for {relative_path}")
        pattern = re.compile(
            rb"(?P<full>[ \t]*<div\b[^>]*>\s*<img\b(?=[^>]*\bsrc\s*=\s*([\"'])"
            + re.escape(expected_src) + rb"\2)[^>]*>\s*</div\s*>[ \t]*(?:\r?\n)?)",
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(data):
            found.append((match.start("full"), match.end("full"), match.group("full")))
    elif field == "jsonld_description":
        for script_match in SCRIPT_TAG.finditer(data):
            script = script_match.group(0)
            opening_end = script.find(b">") + 1
            opening = script[:opening_end]
            if not JSONLD_TYPE.search(opening):
                continue
            for value in JSONLD_DESCRIPTION.finditer(script):
                start = script_match.start() + value.start()
                end = script_match.start() + value.end()
                found.append((start, end, data[start:end]))
    else:
        raise AssertionError(f"unknown metadata field: {field!r}")
    return found


def _find_meta_tag(data, attribute, value):
    found = []
    for match in META_TAG.finditer(data):
        values = _attribute_values(match.group(0), attribute)
        if len(values) == 1 and values[0].group("value").lower() == value.encode("ascii"):
            found.append(match)
    return (found[0].start(), found[0].end()) if len(found) == 1 else None


def _literal_span(data, literal):
    positions = [match.start() for match in re.finditer(re.escape(literal), data)]
    return (positions[0], positions[0] + len(literal)) if len(positions) == 1 else None


def restore_whitelisted_metadata(relative_path, data, entry, original):
    """Restore only exact manifest-listed metadata snippets on fixed paths."""
    fields = entry.get("outside_metadata", {})
    if not isinstance(fields, dict):
        raise AssertionError(f"invalid outside metadata map in {relative_path}")
    if fields and relative_path not in METADATA_FIELD_WHITELIST:
        raise AssertionError(f"outside metadata is not authorized for {relative_path}")
    for field, pair in fields.items():
        if field not in METADATA_FIELD_WHITELIST.get(relative_path, frozenset()):
            raise AssertionError(f"metadata field {field!r} is not authorized for {relative_path}")
        if (not isinstance(pair, dict) or set(pair) != {"original", "approved"}
                or not isinstance(pair["original"], str)
                or not isinstance(pair["approved"], str)
                or pair["original"] == pair["approved"]):
            raise AssertionError(f"invalid exact metadata snippet pair for {field} in {relative_path}")
        old, approved = pair["original"].encode("utf-8"), pair["approved"].encode("utf-8")
        old_matches = _field_matches(original, relative_path, field)
        current_matches = _field_matches(data, relative_path, field)
        if len(old_matches) != 1 or old_matches[0][2] != old:
            raise AssertionError(f"original metadata snippet mismatch for {field} in {relative_path}")
        if field == "hero_banner" and approved == b"" and not current_matches:
            # The banner is outside the article. Reinsert it only immediately
            # before its exact, unchanged following navigation line.
            anchor = original[old_matches[0][1]:].split(b"\n", 1)[0]
            if not anchor.startswith(b'<nav aria-label="Learning path navigation"') or data.count(anchor) != 1:
                raise AssertionError(f"unapproved hero-banner anchor in {relative_path}")
            start = data.index(anchor)
            data = data[:start] + old + data[start:]
            continue
        if len(current_matches) != 1 or current_matches[0][2] not in {old, approved}:
            raise AssertionError(f"unapproved metadata snippet for {field} in {relative_path}")
        start, end, snippet = current_matches[0]
        if snippet == approved:
            data = data[:start] + old + data[end:]
    return data


def load_manifest():
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"cannot read resource-content manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise AssertionError("resource-content manifest must use schema_version 1")
    if manifest.get("baseline_commit") != PUBLISHED_BASELINE:
        raise AssertionError("resource-content baseline SHA pin changed")
    articles, paths = manifest.get("articles"), manifest.get("allowed_paths")
    if not isinstance(articles, dict) or not isinstance(paths, list):
        raise AssertionError("resource-content manifest requires articles and allowed_paths")
    if len(paths) != len(set(paths)) or set(paths) != set(articles):
        raise AssertionError("resource-content entries must exactly match the explicit allowlist")
    for relative, entry in articles.items():
        if not _valid_path(relative):
            raise AssertionError(f"invalid resource-content path: {relative!r}")
        if not isinstance(entry, dict):
            raise AssertionError(f"invalid resource-content entry for {relative}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("article_body_sha256", ""))):
            raise AssertionError(f"invalid approved article body fingerprint for {relative}")
        _validate_date_pair(
            entry, "date_modified_original", "date_modified_approved",
            f"dateModified in {relative}",
        )
        for prefix, nullable in (("visible_updated", True), ("sitemap_lastmod", False)):
            _validate_date_pair(
                entry, prefix + "_original", prefix + "_approved",
                f"{prefix.replace('_', ' ')} in {relative}", nullable=nullable,
            )
        metadata = entry.get("outside_metadata", {})
        if not isinstance(metadata, dict):
            raise AssertionError(f"invalid outside metadata map in {relative}")
        if metadata and relative not in METADATA_FIELD_WHITELIST:
            raise AssertionError(f"outside metadata is not authorized for {relative}")
        if not set(metadata).issubset(METADATA_FIELD_WHITELIST.get(relative, frozenset())):
            raise AssertionError(f"outside metadata field is not authorized for {relative}")
        for field, pair in metadata.items():
            if (not isinstance(pair, dict) or set(pair) != {"original", "approved"}
                    or not all(isinstance(pair.get(key), str) for key in ("original", "approved"))
                    or pair["original"] == pair["approved"]):
                raise AssertionError(f"invalid exact metadata snippet pair for {field} in {relative}")
    return manifest


def allowed_paths():
    return frozenset(load_manifest()["allowed_paths"])


def published_bytes(relative_path):
    if not _valid_path(relative_path):
        raise AssertionError(f"not a tutorial article path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{PUBLISHED_BASELINE}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned PR15 source missing: {relative_path}")
    return result.stdout


def restore_page_to_pr15(relative_path, data, entry, original):
    """Restore only exact approved body/date/metadata fields; wrappers remain visible."""
    data = normalize_tutorial_ui(relative_path, data.decode("utf-8")).encode("utf-8")
    original = normalize_tutorial_ui(relative_path, original.decode("utf-8")).encode("utf-8")
    if PRE_CODE.findall(data) != PRE_CODE.findall(original):
        raise AssertionError(f"<pre><code> mutation in {relative_path}")
    def executable_scripts(source):
        return [block for block in SCRIPT_TAG.findall(source)
                if not JSONLD_TYPE.search(block.split(b">", 1)[0] + b">")]
    if executable_scripts(data) != executable_scripts(original):
        raise AssertionError(f"executable-script mutation in {relative_path}")
    old_articles = list(ARTICLE.finditer(original))
    current_articles = list(ARTICLE.finditer(data))
    if len(old_articles) != 1 or len(current_articles) != 1:
        raise AssertionError(f"expected exactly one article in {relative_path}")
    old_article, current_article = old_articles[0], current_articles[0]
    if current_article.group("open") != old_article.group("open"):
        raise AssertionError(f"article wrapper mutation in {relative_path}")
    if current_article.group("close") != old_article.group("close"):
        raise AssertionError(f"article wrapper mutation in {relative_path}")

    original_digest = hashlib.sha256(old_article.group("body")).hexdigest()
    current_digest = hashlib.sha256(current_article.group("body")).hexdigest()
    if current_digest not in {entry["article_body_sha256"], original_digest}:
        raise AssertionError(f"unregistered article-body edit in {relative_path}: {current_digest}")

    # Restore the fingerprinted body before narrowly restoring outside fields.
    data = (
        data[:current_article.start("body")]
        + original[old_article.start("body"):old_article.end("body")]
        + data[current_article.end("body"):]
    )
    data = restore_whitelisted_metadata(relative_path, data, entry, original)

    old_date = entry["date_modified_original"].encode("ascii")
    approved_date = entry["date_modified_approved"].encode("ascii")
    matches = list(DATE_MODIFIED.finditer(data))
    if len(matches) != 1 or matches[0].group(2) not in {old_date, approved_date}:
        raise AssertionError(f"unapproved dateModified in {relative_path}")
    match = matches[0]
    data = data[:match.start(2)] + old_date + data[match.end(2):]

    old_label = entry["visible_updated_original"]
    approved_label = entry["visible_updated_approved"]
    if old_label is not None or approved_label is not None:
        if not isinstance(old_label, str) or not isinstance(approved_label, str):
            raise AssertionError(f"invalid visible Updated date pair in {relative_path}")
        old_bytes, approved_bytes = old_label.encode("utf-8"), approved_label.encode("utf-8")
        visible_matches = list(UPDATED.finditer(data))
        if len(visible_matches) != 1 or visible_matches[0].group(1) not in {old_bytes, approved_bytes}:
            raise AssertionError(f"unapproved visible Updated date in {relative_path}")
        match = visible_matches[0]
        data = data[:match.start(1)] + old_bytes + data[match.end(1):]

    return data


def normalize_resource_content(relative_path, data):
    """Return non-allowlisted bytes unchanged; restore a listed page to exact PR15."""
    relative_path, data = normalize_route_migration(relative_path, data)
    if relative_path.startswith("tutorials/") and relative_path.endswith(".html"):
        data = normalize_tutorial_ui(relative_path, data.decode("utf-8")).encode("utf-8")
    manifest = load_manifest()
    entry = manifest["articles"].get(relative_path)
    if entry is None:
        return data
    original = published_bytes(relative_path)
    return restore_page_to_pr15(relative_path, data, entry, original)


def restore_sitemap_to_pr15(data, paths=None, entries=None):
    """Restore only exact allowlisted URL-row lastmods and no other sitemap bytes."""
    if entries is None:
        manifest = load_manifest()
        entries = manifest["articles"]
        paths = manifest["allowed_paths"]
    if paths is None or set(paths) != set(entries):
        raise AssertionError("sitemap paths must exactly match resource-content entries")
    for relative in paths:
        if not _valid_path(relative):
            raise AssertionError(f"invalid resource-content sitemap path: {relative!r}")
        entry = entries[relative]
        target = ("https://theomicshub.com/" + relative).encode("ascii")
        rows = [match for match in SITEMAP_ROW.finditer(data) if match.group(1) == target]
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one sitemap row for {relative}")
        row_match = rows[0]
        row = row_match.group(0)
        lastmods = list(LASTMOD.finditer(row))
        old_date = entry["sitemap_lastmod_original"].encode("ascii")
        approved_date = entry["sitemap_lastmod_approved"].encode("ascii")
        if len(lastmods) != 1 or lastmods[0].group(1) not in {old_date, approved_date}:
            raise AssertionError(f"unapproved sitemap lastmod for {relative}")
        lastmod = lastmods[0]
        restored = row[:lastmod.start(1)] + old_date + row[lastmod.end(1):]
        data = data[:row_match.start()] + restored + data[row_match.end():]
    return data


def normalize_resource_sitemap(data):
    # Reverse only the newest literal date chunks before testing historical
    # whole-asset pins. Unknown edits stay visible for the existing row guards.
    from latest_review_baseline import normalize_latest_review
    data = normalize_latest_review("sitemap.xml", data.decode("utf-8")).encode("utf-8")
    from tutorial_execution_baseline import restore_overlapping_execution_asset
    data = restore_overlapping_execution_asset("sitemap.xml", data)
    if hashlib.sha256(data).hexdigest() == R_FIRST_ASSET_SHA256.get("sitemap.xml"):
        data = restore_r_first_asset("sitemap.xml", data)
    return restore_sitemap_to_pr15(data)
