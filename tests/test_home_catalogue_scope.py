"""Strict scope guards for the homepage and tutorial catalogue review."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

from home_catalogue_baseline import (
    HOME_CATALOGUE_BASELINE,
    HOME_CATALOGUE_ASSET_PATHS,
    normalize_home_catalogue,
    page_patches,
    pre_home_catalogue_bytes,
    verify_home_catalogue_file,
)
from tutorial_ui_baseline import normalize_tutorial_ui, verify_tutorial_ui_file

ROOT = Path(__file__).resolve().parents[1]


def git_bytes(revision, path):
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def pinned_paths():
    return subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", HOME_CATALOGUE_BASELINE],
        cwd=ROOT, text=True,
    ).splitlines()


class _AttributeReader(HTMLParser):
    def __init__(self, tag):
        super().__init__(convert_charrefs=True)
        self.target = tag
        self.attrs = None

    def handle_starttag(self, tag, attrs):
        if tag == self.target and self.attrs is None:
            self.attrs = dict(attrs)


def first_attrs(markup, tag):
    reader = _AttributeReader(tag)
    reader.feed(markup)
    return reader.attrs


def _text(fragment):
    return unescape(re.sub(r"<[^>]*>", "", fragment)).strip()


def catalogue_records(markup):
    records = []
    for match in re.finditer(r"<article\b([^>]*)>(.*?)</article\s*>", markup, re.S | re.I):
        attrs = first_attrs("<article" + match.group(1) + ">", "article") or {}
        card = match.group(2)
        href_match = re.search(r"<a\b[^>]*\bhref=[\"']([^\"']+)[\"'][^>]*>", card, re.I)
        title_match = re.search(r"<h3\b[^>]*>(.*?)</h3\s*>", card, re.S | re.I)
        description_match = re.search(r"<p\b[^>]*>(.*?)</p\s*>", card, re.S | re.I)
        if href_match and href_match.group(1).startswith("tutorials/"):
            records.append((
                href_match.group(1),
                _text(title_match.group(1)) if title_match else "",
                _text(description_match.group(1)) if description_match else "",
                attrs.get("data-category", ""),
            ))
    return records


def _strip_allowed_asset_tags(text):
    # Only these exact local stylesheet hrefs may differ outside <main>.
    allowed_stylesheet_hrefs = {
        "home-page.min.css?v=20261023-reader-typography",
        "home-page.min.css?v=20261024-home-catalogue-v1",
        "home-catalogue.css?v=20261024a",
        "back-to-top.css?v=20261024-home-catalogue-v1",
    }
    stylesheet = re.compile(r"<link\b[^>]*>(?:\r?\n)?", re.I)
    def keep_or_remove(match):
        tag = match.group(0)
        href = re.search(r"\bhref\s*=\s*([\"'])(.*?)\1", tag, re.I)
        rel = re.search(r"\brel\s*=\s*([\"'])(.*?)\1", tag, re.I)
        if (href and rel and "stylesheet" in rel.group(2).lower().split()
                and href.group(2) in allowed_stylesheet_hrefs):
            return ""
        return tag
    text = stylesheet.sub(keep_or_remove, text)
    # Only the empty catalogue-browser tag is removable; the subscribe-fab
    # update is normalized below by its one exact local version string.
    def script_or_keep(match):
        tag = match.group(0)
        attrs = first_attrs(tag, "script") or {}
        source = attrs.get("src", "")
        if (source == "catalogue-browser.js?v=20261024a"
                and not match.group(2).strip()):
            return ""
        if source == "subscribe-fab.js?v=20261024-home-catalogue-v1":
            return tag.replace(
                'src="subscribe-fab.js?v=20261024-home-catalogue-v1"',
                'src="subscribe-fab.js?v=20261022-reader-review"',
                1,
            )
        return tag
    return re.sub(r"<script\b([^>]*)>(.*?)</script\s*>(?:\r?\n)?", script_or_keep,
                  text, flags=re.I | re.S)


def _outside_main(markup):
    starts = list(re.finditer(r"<main\b[^>]*>", markup, re.I))
    ends = list(re.finditer(r"</main\s*>", markup, re.I))
    if len(starts) != 1 or len(ends) != 1 or ends[0].start() < starts[0].end():
        raise AssertionError("expected exactly one balanced main element")
    return markup[:starts[0].start()], markup[ends[0].end():]


def _body_attrs(markup):
    match = re.search(r"<body\b[^>]*>", markup, re.I)
    if not match:
        raise AssertionError("page is missing its body start tag")
    attrs = first_attrs(match.group(0), "body") or {}
    return match, attrs


def _normalize_outer_fragment(fragment):
    fragment = _strip_allowed_asset_tags(fragment)
    match, _attrs = _body_attrs(fragment) if re.search(r"<body\b", fragment, re.I) else (None, None)
    if match:
        fragment = fragment[:match.start()] + "<body>" + fragment[match.end():]
    return fragment


class HomeCatalogueScopeTests(unittest.TestCase):
    def test_frozen_page_fixture_is_exact_and_normalization_is_idempotent(self):
        patches = page_patches()
        self.assertEqual(set(patches), {"index.html", "tutorials.html"})
        for relative in sorted(patches):
            with self.subTest(page=relative):
                original = pre_home_catalogue_bytes(relative).decode("utf-8")
                current = (ROOT / relative).read_text(encoding="utf-8")
                restored = normalize_home_catalogue(relative, current)
                self.assertEqual(restored, original)
                self.assertEqual(normalize_home_catalogue(relative, restored), restored)
                self.assertEqual(normalize_tutorial_ui(relative, current), original)

    def test_unrecognized_main_text_script_and_claim_edits_survive_normalization(self):
        for relative in ("index.html", "tutorials.html"):
            current = (ROOT / relative).read_text(encoding="utf-8")
            baseline = pre_home_catalogue_bytes(relative).decode("utf-8")
            probes = (
                current.replace("</main>", "<p>unapproved surrounding claim</p>\n</main>", 1),
                current.replace("</main>", "<script>window.unapproved = true;</script>\n</main>", 1),
                current.replace("</main>", "<p>unapproved scientific promise</p>\n</main>", 1),
            )
            for mutated in probes:
                with self.subTest(page=relative, probe=mutated[-100:]):
                    self.assertNotEqual(mutated, current)
                    self.assertNotEqual(normalize_home_catalogue(relative, mutated), baseline)

    def test_duplicate_exact_catalogue_patch_is_rejected(self):
        relative = "index.html"
        patch = page_patches()[relative][0]["after"]
        current = (ROOT / relative).read_text(encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "duplicate exact home-catalogue patch"):
            normalize_home_catalogue(relative, current + "\n" + patch)

    def test_shared_subscribe_script_normalizes_only_its_exact_catalogue_guard(self):
        relative = "subscribe-fab.js"
        original = pre_home_catalogue_bytes(relative).decode("utf-8")
        current = (ROOT / relative).read_text(encoding="utf-8")
        restored = normalize_home_catalogue(relative, current)
        self.assertEqual(restored, original)
        self.assertEqual(normalize_home_catalogue(relative, restored), restored)

        changed_guard = current.replace(
            "document.getElementById('catalogue-category')",
            "document.getElementById('unapproved-category')",
            1,
        )
        self.assertNotEqual(normalize_home_catalogue(relative, changed_guard), original)
        guard_patch = (
            "    if (!strip || document.getElementById('catalogue-category') || "
            "typeof window.filterTutorialsOnly !== 'function') return;\n"
        )
        with self.assertRaisesRegex(AssertionError, "duplicate exact home-catalogue subscribe-fab category guard"):
            normalize_home_catalogue(relative, current + guard_patch)

    def test_all_58_tutorial_pages_are_raw_identical_to_the_source_pin(self):
        pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(pages), 58)
        for page in pages:
            relative = page.relative_to(ROOT).as_posix()
            with self.subTest(page=relative):
                self.assertEqual(page.read_bytes(), git_bytes(HOME_CATALOGUE_BASELINE, relative))

    def test_catalogue_retains_all_58_hrefs_titles_descriptions_and_categories(self):
        original = pre_home_catalogue_bytes("tutorials.html").decode("utf-8")
        current = (ROOT / "tutorials.html").read_text(encoding="utf-8")
        before, after = catalogue_records(original), catalogue_records(current)
        self.assertEqual(len(before), 58)
        self.assertEqual(len(after), 58)
        self.assertEqual(after, before)
        self.assertTrue(all(href and title and description and category for href, title, description, category in after))

    def test_only_catalogue_stylesheet_version_local_script_and_added_body_attribute_change_outside_main(self):
        for relative in ("index.html", "tutorials.html"):
            original = pre_home_catalogue_bytes(relative).decode("utf-8")
            current = (ROOT / relative).read_text(encoding="utf-8")
            old_prefix, old_suffix = _outside_main(original)
            new_prefix, new_suffix = _outside_main(current)
            old_body_match, old_body = _body_attrs(old_prefix)
            new_body_match, new_body = _body_attrs(new_prefix)
            self.assertTrue(old_body.keys() <= new_body.keys(), f"{relative}: existing body attributes were removed")
            self.assertEqual({key: new_body[key] for key in old_body}, old_body,
                             f"{relative}: an existing body attribute changed")
            added_body_attrs = set(new_body) - set(old_body)
            self.assertIn(added_body_attrs, (set(), {"data-home-catalogue"}),
                          f"{relative}: only the optional catalogue body marker may be added")
            if "data-home-catalogue" in added_body_attrs:
                self.assertIn(new_body["data-home-catalogue"], {"home", "catalogue"},
                              f"{relative}: unexpected catalogue body marker value")
            raw_marker = re.compile(r"\s+data-home-catalogue=([\"'])(?:home|catalogue)\1")
            raw_new_body = new_body_match.group(0)
            self.assertLessEqual(len(raw_marker.findall(raw_new_body)), 1,
                                 f"{relative}: duplicate catalogue body marker")
            self.assertEqual(raw_marker.sub("", raw_new_body, count=1), old_body_match.group(0),
                             f"{relative}: original body attributes must remain byte-identical")
            self.assertEqual(_normalize_outer_fragment(old_prefix), _normalize_outer_fragment(new_prefix),
                             f"{relative}: unapproved changes before main")
            self.assertEqual(_strip_allowed_asset_tags(old_suffix), _strip_allowed_asset_tags(new_suffix),
                             f"{relative}: unapproved changes after main")

    def test_shared_styles_scripts_fonts_and_images_are_source_identical(self):
        paths = pinned_paths()
        protected = [
            path for path in paths
            if path.startswith(("fonts/", "images/"))
            or path.endswith((".js", ".css"))
        ]
        protected = [path for path in protected if path != "home-page.min.css"]
        for relative in protected:
            with self.subTest(path=relative):
                current = (ROOT / relative).read_bytes()
                if relative == "subscribe-fab.js":
                    normalized = normalize_home_catalogue(relative, current.decode("utf-8"))
                    self.assertEqual(normalized.encode("utf-8"), git_bytes(HOME_CATALOGUE_BASELINE, relative))
                    self.assertEqual(verify_home_catalogue_file(relative, current), current)
                    changed_elsewhere = current.replace(b"window.scrollTo", b"window.unapproved", 1)
                    self.assertNotEqual(
                        normalize_home_catalogue(relative, changed_elsewhere.decode("utf-8")),
                        git_bytes(HOME_CATALOGUE_BASELINE, relative).decode("utf-8"),
                    )
                else:
                    self.assertEqual(current, git_bytes(HOME_CATALOGUE_BASELINE, relative))

    def test_workflow_changes_are_full_hash_pinned_and_restore_to_the_source(self):
        for relative in (".github/workflows/static.yml", ".github/workflows/tutorial-review.yml"):
            with self.subTest(path=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(verify_home_catalogue_file(relative, data), data)
                normalized = normalize_home_catalogue(relative, data.decode("utf-8"))
                self.assertEqual(normalized.encode("utf-8"), git_bytes(HOME_CATALOGUE_BASELINE, relative))
                with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                    verify_home_catalogue_file(relative, data + b"\n")

    def test_generated_home_css_is_hash_pinned_and_restores_to_fa26faa(self):
        data = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(verify_home_catalogue_file("home-page.min.css", data), data)
        normalized = normalize_home_catalogue("home-page.min.css", data.decode("utf-8"))
        self.assertEqual(normalized.encode("utf-8"), git_bytes(HOME_CATALOGUE_BASELINE, "home-page.min.css"))
        with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
            verify_home_catalogue_file("home-page.min.css", data + b"\n")

    def test_all_feature_assets_have_individual_full_hash_pins(self):
        self.assertEqual(HOME_CATALOGUE_ASSET_PATHS, {
            "home-catalogue.css", "catalogue-browser.js",
            "subscribe-fab.js", ".github/workflows/static.yml",
            ".github/workflows/tutorial-review.yml",
            "tools/catalogue-learning.json", "tools/generate_catalogue_learning.py",
            "home-page.min.css",
        })
        for relative in sorted(HOME_CATALOGUE_ASSET_PATHS):
            with self.subTest(path=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(verify_home_catalogue_file(relative, data), data)
                with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                    verify_home_catalogue_file(relative, data + b"\n")
        # The generated bundle remains on the established UI asset allowlist.
        data = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(verify_tutorial_ui_file("home-page.min.css", data), data)
        with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
            verify_tutorial_ui_file("home-page.min.css", data + b"\n")

    def test_only_named_feature_assets_are_authorized(self):
        for path in ("tools/unrelated.json", "images/unrelated.png", "index.html"):
            with self.subTest(path=path):
                with self.assertRaises(AssertionError):
                    verify_home_catalogue_file(path, b"unapproved")


if __name__ == "__main__":
    unittest.main()
