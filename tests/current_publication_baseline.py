"""Exact restoration for the three latest published mainline revisions.

Only complete file bytes from the pinned commits are normalized. For the
homepage stylesheet, the one deterministic generated output is also accepted
when its non-comment CSS rules are byte-identical to the parent asset. Any
unknown mutation remains visible to older scope guards.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/current-publication-revisions.json"
FIXTURE_SHA256 = "07ad1bdebc6e046beed6133767923827fa24556ca6b056fa4852f0c9727bc473"


def _git_bytes(revision, relative_path):
    if (not isinstance(relative_path, str) or not relative_path
            or relative_path.startswith("/") or "\\" in relative_path
            or ".." in Path(relative_path).parts):
        raise AssertionError(f"unsafe publication baseline path: {relative_path!r}")
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode:
        raise AssertionError(f"pinned publication source unavailable: {revision}:{relative_path}")
    return result.stdout


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _css_rules(data):
    lines = data.splitlines(keepends=True)
    if len(lines) != 2 or not lines[0].startswith(
        b"/* Homepage-only subset of style.css; generated with PurgeCSS. Original retained. Source SHA256: "
    ) or not lines[0].endswith(b" */\n"):
        raise AssertionError("homepage CSS must contain its exact generated source-hash header")
    if not re.search(rb"Source SHA256: [0-9a-f]{64} \*/\n$", lines[0]):
        raise AssertionError("homepage CSS source-hash header is malformed")
    return lines[1]


@lru_cache(maxsize=1)
def publication_layers():
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"current-publication fixture unavailable: {exc}") from exc
    observed = _sha(raw)
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"current-publication fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid current-publication fixture JSON") from exc
    if not isinstance(fixture, dict) or fixture.get("schema") != 1:
        raise AssertionError("current-publication fixture must use schema 1")
    layers = fixture.get("layers")
    if not isinstance(layers, list) or len(layers) != 3:
        raise AssertionError("fixture must pin the latest publication and two parent mainline revisions")

    validated = []
    for layer in layers:
        if (not isinstance(layer, dict)
                or set(layer) != {"name", "base_commit", "head_commit", "files"}
                or not isinstance(layer["files"], dict)):
            raise AssertionError("invalid current-publication layer record")
        base_commit, head_commit = layer["base_commit"], layer["head_commit"]
        if not re.fullmatch(r"[0-9a-f]{40}", base_commit) or not re.fullmatch(r"[0-9a-f]{40}", head_commit):
            raise AssertionError("publication layer commits must be full pinned SHAs")
        changed = subprocess.run(
            ["git", "diff", "--name-only", base_commit, head_commit], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if changed.returncode:
            raise AssertionError(f"cannot inspect publication layer {layer['name']}: {changed.stderr}")
        paths = set(changed.stdout.splitlines())
        if paths != set(layer["files"]):
            raise AssertionError(f"publication layer path set is not exact: {layer['name']}")

        records = {}
        for relative_path, item in layer["files"].items():
            if (not isinstance(item, dict)
                    or set(item) - {"base_sha256", "head_sha256", "generated_head_sha256"}
                    or not {"base_sha256", "head_sha256"}.issubset(item)):
                raise AssertionError(f"invalid publication path record: {relative_path}")
            base = _git_bytes(base_commit, relative_path)
            head = _git_bytes(head_commit, relative_path)
            if _sha(base) != item["base_sha256"] or _sha(head) != item["head_sha256"]:
                raise AssertionError(f"publication blob hash pin mismatch: {relative_path}")
            generated_hash = item.get("generated_head_sha256")
            if generated_hash is not None:
                if relative_path != "home-page.min.css" or not re.fullmatch(r"[0-9a-f]{64}", generated_hash):
                    raise AssertionError(f"invalid generated stylesheet pin: {relative_path}")
                generated = (ROOT / relative_path).read_bytes()
                if _sha(generated) != generated_hash and _css_rules(generated) != _css_rules(base):
                    raise AssertionError("generated homepage stylesheet fingerprint mismatch")
                if _css_rules(generated) != _css_rules(base):
                    raise AssertionError("generated homepage CSS rules differ from the exact parent asset")
                generated_hash = _sha(generated) if _css_rules(generated) == _css_rules(base) else generated_hash
            records[relative_path] = {
                "base": base,
                "head": head,
                "head_sha256": item["head_sha256"],
                "generated_head_sha256": generated_hash,
            }
        validated.append({"name": layer["name"], "files": records})
    if [layer["name"] for layer in validated] != [
        "deployment-css-sitemap", "approved-navigation", "parent-sitewide"
    ]:
        raise AssertionError("publication layers are out of the required newest-to-oldest order")
    return tuple(validated)


def current_published_bytes(relative_path):
    """Return the newest exactly pinned published bytes for one changed path."""
    for layer in publication_layers():
        entry = layer["files"].get(relative_path)
        if entry is not None:
            return entry["head"]
    raise AssertionError(f"path is not pinned by current-publication fixture: {relative_path}")


def normalize_latest_publication(relative_path, data):
    """Restore only the newest exact publication layer; preserve unknown bytes."""
    if not isinstance(data, bytes):
        raise TypeError("current-publication normalization requires bytes")
    entry = publication_layers()[0]["files"].get(relative_path)
    if entry is None:
        return data
    digest = _sha(data)
    accepted = {entry["head_sha256"]}
    if entry["generated_head_sha256"]:
        accepted.add(entry["generated_head_sha256"])
    if digest not in accepted:
        return data
    if digest == entry["generated_head_sha256"]:
        _css_rules(data)
    return entry["base"]


def normalize_current_publication(relative_path, data):
    """Restore exact known mainline snapshots; preserve every other byte sequence."""
    if not isinstance(data, bytes):
        raise TypeError("current-publication normalization requires bytes")
    for layer in publication_layers():
        entry = layer["files"].get(relative_path)
        if entry is None:
            continue
        digest = _sha(data)
        accepted = {entry["head_sha256"]}
        if entry["generated_head_sha256"]:
            accepted.add(entry["generated_head_sha256"])
        if digest in accepted:
            if entry["generated_head_sha256"] == digest:
                _css_rules(data)
            data = entry["base"]
    return data


def normalize_approved_navigation(relative_path, data):
    """Restore only the approved 775 navigation revision to its d88 parent."""
    if not isinstance(data, bytes):
        raise TypeError("approved-navigation normalization requires bytes")
    layer = next(layer for layer in publication_layers() if layer["name"] == "approved-navigation")
    entry = layer["files"].get(relative_path)
    if entry is None:
        return data
    digest = _sha(data)
    accepted = {entry["head_sha256"]}
    if entry["generated_head_sha256"]:
        accepted.add(entry["generated_head_sha256"])
    if digest not in accepted:
        return data
    if digest == entry["generated_head_sha256"]:
        _css_rules(data)
    return entry["base"]
