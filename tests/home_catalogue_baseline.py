"""Exact, reversible baseline adapter for the homepage and tutorial catalogue.

Only ``index.html`` and ``tutorials.html`` may use literal fixture chunks from
HOME_CATALOGUE_BASELINE. All related assets are independently SHA-256 pinned.
The fixture/hash placeholders are deliberately refreshed only after the page
owners freeze their work with refresh-home-catalogue-baselines.py.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess
from sitewide_top_baseline import normalize_sitewide_top

ROOT = Path(__file__).resolve().parents[1]
HOME_CATALOGUE_BASELINE = "fa26faa8d20a31de1211652e8ebffcf99534b9a6"
FIXTURE_PATH = ROOT / "tests/fixtures/home-catalogue-review-edits.json"
FIXTURE_SHA256 = "d23a7cb721a175a27607fc3a0725fd19e3c062ea69d5f897ee5c37a4f0a5856f"
PAGE_PATHS = frozenset({"index.html", "tutorials.html"})

# These four files are local to the homepage/catalogue feature. The generated
# CSS bundle is an asset as well, but keeps its long-standing tutorial-UI path.
HOME_CATALOGUE_ASSET_SHA256 = {
    "home-catalogue.css": "e54a7c94925e42885c1e19ed6b7647dc47354a4bd6df2168a08e1ead8b4287bf",
    "catalogue-browser.js": "f40825f685a9addd80d60b3674638c6ac4e0a316c7382930499f90f11d7a37ea",
    "subscribe-fab.js": "9721d06bac9fa3f1de8a3a57e06868e39f98f08c1e09dfbaaab13df5e4bcc8c1",
    "404.html": "5c9259a20ffd2c03859e206e51c1f04f4bd0a123254eea8d03dacec25081f042",
    ".github/workflows/static.yml": "9bd92a2ccf3a0fdd65a48952366933f2a5857f8abac18e90f68313a0a964ee0c",
    ".github/workflows/tutorial-review.yml": "8b4c3df2dc07719fb3a00776c62035443bacb8e5fde97db9c4321409d561572f",
    "tools/catalogue-learning.json": "a96141ebe48caea57f89d01b05d42b6ce29b30e0ef7671d1c9a761d0027d8569",
    "tools/generate_catalogue_learning.py": "e4c2f2668a93079dc26321045b04d2c5812b5df6aeceb459d3b6288cf7a42fa5",
    "home-page.min.css": "31c20c852a226d2969acab21fc8a0ac87c5d7391b7d12d6441bdc3571e60cbbf",
}
HOME_CATALOGUE_ASSET_PATHS = frozenset(HOME_CATALOGUE_ASSET_SHA256)

SUBSCRIBE_FAB_SELECTOR_BEFORE = '      if (existing.matches(\'a[href="#tutorial-title"], a[href="#sh-hero-title"]\')) {\n'
SUBSCRIBE_FAB_SELECTOR_AFTER = '      if (existing.matches(\'a[href="#tutorial-title"], a[href="#sh-hero-title"], a[href="#home-hero-title"], a[href="#catalogue-hero-title"]\')) {\n'
SUBSCRIBE_FAB_CATEGORY_GUARD_BEFORE = "    if (!strip || typeof window.filterTutorialsOnly !== 'function') return;\n"
SUBSCRIBE_FAB_CATEGORY_GUARD_AFTER = "    if (!strip || document.getElementById('catalogue-category') || typeof window.filterTutorialsOnly !== 'function') return;\n"


def _git_show(relative_path):
    if relative_path not in PAGE_PATHS | HOME_CATALOGUE_ASSET_PATHS | {"home-page.min.css"}:
        raise AssertionError(f"not an authorized home-catalogue historical path: {relative_path}")
    result = subprocess.run(
        ["git", "show", f"{HOME_CATALOGUE_BASELINE}:{relative_path}"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def pre_home_catalogue_bytes(relative_path):
    """Return the pinned source bytes for one explicitly authorized path."""
    return _git_show(relative_path)


def _validate_context(before, after, label):
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    if min(len(old_lines), len(new_lines)) < 6:
        raise AssertionError(f"{label} needs three unchanged context lines on each side")
    if old_lines[:3] != new_lines[:3] or old_lines[-3:] != new_lines[-3:]:
        raise AssertionError(f"{label} does not preserve its literal three-line context")


@lru_cache(maxsize=1)
def page_patches():
    """Load the frozen fixture and prove each old chunk belongs to fa26faa."""
    if not re.fullmatch(r"[0-9a-f]{64}", FIXTURE_SHA256):
        raise AssertionError("Home-catalogue fixture pin not refreshed; run refresh-home-catalogue-baselines.py after freeze")
    try:
        raw = FIXTURE_PATH.read_bytes()
    except OSError as exc:
        raise AssertionError(f"home-catalogue fixture is not frozen yet: {exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != FIXTURE_SHA256:
        raise AssertionError(f"home-catalogue fixture fingerprint mismatch: {observed}")
    try:
        fixture = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError("invalid home-catalogue fixture JSON") from exc
    if (not isinstance(fixture, dict) or fixture.get("schema") != 1
            or fixture.get("pre_home_catalogue_commit") != HOME_CATALOGUE_BASELINE
            or set(fixture.get("files", {})) != PAGE_PATHS):
        raise AssertionError("invalid exact home-catalogue fixture header or scope")

    validated = {}
    for relative_path, patches in fixture["files"].items():
        if not isinstance(patches, list) or not patches:
            raise AssertionError(f"fixture requires literal changed chunks for {relative_path}")
        original = _git_show(relative_path)
        if original is None:
            raise AssertionError(f"pinned home-catalogue source unavailable for {relative_path}")
        source = original.decode("utf-8")
        for index, patch in enumerate(patches):
            label = f"{relative_path} fixture chunk {index}"
            if (not isinstance(patch, dict) or set(patch) != {"before", "after"}
                    or not isinstance(patch.get("before"), str)
                    or not isinstance(patch.get("after"), str)
                    or not patch["before"] or not patch["after"]
                    or patch["before"] == patch["after"]):
                raise AssertionError(f"invalid {label}")
            before, after = patch["before"], patch["after"]
            _validate_context(before, after, label)
            if source.count(before) != 1:
                raise AssertionError(f"{label} must occur exactly once in fa26faa")
            source = source.replace(before, after, 1)
        validated[relative_path] = patches
    return validated


def normalize_home_catalogue(relative_path, text):
    """Reverse only exact frozen chunks; unknown page edits remain visible."""
    if not isinstance(text, str):
        raise TypeError("home-catalogue normalization requires decoded text")
    text = normalize_sitewide_top(relative_path, text)
    if relative_path == "subscribe-fab.js":
        for after, before, label in (
            (SUBSCRIBE_FAB_SELECTOR_AFTER, SUBSCRIBE_FAB_SELECTOR_BEFORE, "selector"),
            (SUBSCRIBE_FAB_CATEGORY_GUARD_AFTER, SUBSCRIBE_FAB_CATEGORY_GUARD_BEFORE, "category guard"),
        ):
            count = text.count(after)
            if count > 1:
                raise AssertionError(f"duplicate exact home-catalogue subscribe-fab {label} patch")
            if count:
                text = text.replace(after, before, 1)
        return text
    if relative_path in {".github/workflows/static.yml", ".github/workflows/tutorial-review.yml"}:
        expected = HOME_CATALOGUE_ASSET_SHA256[relative_path]
        observed = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if re.fullmatch(r"[0-9a-f]{64}", expected) and observed == expected:
            original = _git_show(relative_path)
            if original is None:
                raise AssertionError(f"pinned fa26faa workflow is unavailable: {relative_path}")
            return original.decode("utf-8")
        return text
    if relative_path == "home-page.min.css":
        observed = hashlib.sha256(text.encode("utf-8")).hexdigest()
        expected = HOME_CATALOGUE_ASSET_SHA256[relative_path]
        if re.fullmatch(r"[0-9a-f]{64}", expected) and observed == expected:
            original = _git_show(relative_path)
            if original is None:
                raise AssertionError("pinned fa26faa home-page.min.css is unavailable")
            return original.decode("utf-8")
        return text
    if relative_path not in PAGE_PATHS:
        return text
    for index, patch in reversed(list(enumerate(page_patches()[relative_path]))):
        after, before = patch["after"], patch["before"]
        count = text.count(after)
        if count > 1:
            raise AssertionError(f"duplicate exact home-catalogue patch chunk {index} in {relative_path}")
        if count == 1:
            text = text.replace(after, before, 1)
    return text


def verify_home_catalogue_file(relative_path, data):
    """Verify a feature asset only when its exact path has a complete hash pin."""
    if relative_path not in HOME_CATALOGUE_ASSET_PATHS:
        raise AssertionError(f"not an authorized home-catalogue asset: {relative_path}")
    expected = HOME_CATALOGUE_ASSET_SHA256[relative_path]
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise AssertionError(f"home-catalogue asset pin not refreshed for {relative_path}")
    observed = hashlib.sha256(data).hexdigest()
    if observed != expected:
        raise AssertionError(f"home-catalogue asset fingerprint mismatch for {relative_path}: {observed}")
    return data
