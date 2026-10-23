"""Exact, reversible normalization for owner-approved reader typography edits.

The manifest deliberately contains literal source strings rather than punctuation
rules. This keeps historical comparisons strict everywhere outside the explicitly
reviewed copy and stylesheet href values.
"""
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path(__file__).resolve().parent / "fixtures" / "reader-copy-edits.json"
_PROTECTED_CODE_BLOCK = re.compile(
    r"<(pre|code)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_SCRIPT_BLOCK = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
_JSONLD_TYPE = re.compile(r"\btype\s*=\s*([\"'])application/ld\+json\1", re.IGNORECASE)


def _load_manifest():
    """Load the parent-owned edits manifest; allow it to be absent during setup."""
    if not MANIFEST_PATH.exists():
        return {"schema_version": 1, "files": {}, "stylesheet_versions": []}
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError(f"cannot read reader typography manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise AssertionError("reader typography manifest must use schema_version 1")
    files = manifest.get("files")
    versions = manifest.get("stylesheet_versions")
    if not isinstance(files, dict) or not isinstance(versions, list):
        raise AssertionError("reader typography manifest requires files and stylesheet_versions")
    for relative_path, entry in files.items():
        if not isinstance(relative_path, str) or relative_path.startswith("/") or ".." in Path(relative_path).parts:
            raise AssertionError(f"invalid reader typography path: {relative_path!r}")
        if not isinstance(entry, dict) or not isinstance(entry.get("replacements"), list):
            raise AssertionError(f"invalid reader typography entries for {relative_path}")
        for replacement in entry["replacements"]:
            _validate_pair(replacement, f"{relative_path} replacement")
    for version in versions:
        _validate_pair(version, "stylesheet version")
    return manifest


def _validate_pair(pair, label):
    if not isinstance(pair, dict):
        raise AssertionError(f"{label} must be an object")
    before, after = pair.get("before"), pair.get("after")
    if not isinstance(before, str) or not isinstance(after, str) or not before or not after or before == after:
        raise AssertionError(f"{label} requires distinct, non-empty before and after strings")
    if _protected_signature(before) != _protected_signature(after):
        raise AssertionError(f"{label} must preserve all pre, code, and script blocks exactly")


def _protected_signature(text):
    """Capture code and executable scripts; JSON-LD is metadata, not executable logic."""
    blocks = list(_PROTECTED_CODE_BLOCK.finditer(text))
    for match in _SCRIPT_BLOCK.finditer(text):
        opening_tag = match.group(0).split(">", 1)[0] + ">"
        if not _JSONLD_TYPE.search(opening_tag):
            blocks.append(match)
    return [match.group(0) for match in sorted(blocks, key=lambda item: item.start())]


def _swap_exact(text, source, destination, label):
    """Swap a single exact occurrence, or leave text untouched if it is absent."""
    count = text.count(source)
    if count > 1:
        raise AssertionError(f"ambiguous {label}: exact source occurs {count} times")
    if count == 0:
        return text
    start = text.index(source)
    updated = text[:start] + destination + text[start + len(source):]
    if _protected_signature(text) != _protected_signature(updated):
        raise AssertionError(f"{label} would modify protected pre, code, or script content")
    return updated


def _swap_stylesheet_href(text, source, destination, label):
    """Change one exact manifest URL substring inside an href value only."""
    pattern = re.compile(r"(?P<prefix>\bhref\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)", re.IGNORECASE)
    matches = [match for match in pattern.finditer(text) if source in match.group("value")]
    occurrences = sum(match.group("value").count(source) for match in matches)
    if occurrences > 1:
        raise AssertionError(f"ambiguous {label}: exact URL substring occurs {occurrences} times in href values")
    if not matches:
        return text
    match = matches[0]
    quote = match.group("quote")
    value = match.group("value").replace(source, destination, 1)
    updated = text[:match.start()] + match.group("prefix") + quote + value + quote + text[match.end():]
    if _protected_signature(text) != _protected_signature(updated):
        raise AssertionError(f"{label} would modify protected pre, code, or script content")
    return updated


def _apply(relative_path, text, manifest, inverse=False):
    entry = manifest["files"].get(relative_path, {"replacements": []})
    replacements = entry["replacements"]
    versions = manifest["stylesheet_versions"]
    if inverse:
        for pair in versions:
            text = _swap_stylesheet_href(text, pair["after"], pair["before"], "stylesheet version normalization")
        for pair in reversed(replacements):
            text = _swap_exact(text, pair["after"], pair["before"], f"reader copy normalization in {relative_path}")
    else:
        for pair in replacements:
            text = _swap_exact(text, pair["before"], pair["after"], f"reader copy restore in {relative_path}")
        for pair in versions:
            text = _swap_stylesheet_href(text, pair["before"], pair["after"], "stylesheet version restore")
    return text


def normalize_reader_typography(relative_path, text):
    """Restore exact published copy and stylesheet hrefs for historical comparisons."""
    return _apply(relative_path, text, _load_manifest(), inverse=True)


def restore_reader_typography(relative_path, text):
    """Reapply only exact manifest typography edits after a baseline comparison."""
    return _apply(relative_path, text, _load_manifest(), inverse=False)
