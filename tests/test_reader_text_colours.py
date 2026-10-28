"""Scope guards for the authorized reader-text foreground-colour revision."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

from reader_text_colour_baseline import (
    PRE_READER_TEXT_COMMIT, READER_TEXT_ASSET_PATHS, READER_TEXT_ASSET_SHA256,
    READER_TEXT_VERSION, normalize_reader_text, page_patches, pre_reader_text_bytes,
    verify_reader_text_file,
)
from r_first_revision_baseline import restore_r_first_asset, R_FIRST_ASSET_PATHS
from r_first_revision_baseline import normalize_r_first_revision
from latest_review_baseline import normalize_latest_review, restore_latest_review_asset
from start_here_desktop_baseline import (
    restore_start_here_desktop_asset,
)
from home_catalogue_banner_baseline import restore_home_catalogue_banner_asset

ROOT = Path(__file__).resolve().parents[1]
CSS_CHANGES = [
    ("start-here.css", "#main-content a", "#086b79", "#17549a"),
    ("start-here.css", ".sh-eyebrow, .sh-section-kicker, .sh-panel-kicker", "#186878", "var(--sh-navy)"),
    ("start-here.css", ".sh-orbit-stop small", "#087578", "var(--sh-navy)"),
    ("start-here.css", '.sh-orbit-stop[aria-current="step"] strong', "#075f68", "var(--sh-navy)"),
    ("start-here.css", ".sh-step-controls button:enabled:hover", "#087f83", "#17549a"),
    ("home-catalogue.css", "#home-page .hc-eyebrow, #tutorials-page .hc-eyebrow", "#b8e8e3", "#d8eeff"),
    ("home-catalogue.css", "#home-page .hc-kicker, #tutorials-page .hc-kicker", "var(--hc-teal)", "var(--hc-navy)"),
    ("home-catalogue.css", ".hc-hero h1 span", "var(--hc-mint)", "#d8eeff"),
    ("home-catalogue.css", "#home-page .hc-text-link, #tutorials-page .hc-text-link", "var(--hc-teal)", "var(--hc-navy)"),
    ("home-catalogue.css", ".hc-featured-meta > span:first-child", "var(--hc-teal)", "var(--hc-navy)"),
    ("home-catalogue.css", "#home-page .hc-featured-card a", "var(--hc-teal)", "var(--hc-navy)"),
    ("home-catalogue.css", "#home-page .hc-catalogue-cta .hc-kicker", "#b8e8e3", "#d8eeff"),
    ("home-catalogue.css", "#tutorials-page .hc-catalogue-hero h1 span", "#a7e7dc", "#d8eeff"),
    ("home-catalogue.css", "#tutorials-page .hc-catalogue-start", "#d3f5ed", "#d8eeff"),
    ("home-catalogue.css", "#tutorials-page #catalogue-reset, #tutorials-page #catalogue-clear-empty", "var(--hc-teal)", "var(--hc-navy)"),
    ("home-catalogue.css", "#tutorials-page .tutorial-grid-card:hover h3", "#146b68", "#17549a"),
    ("style.css", ".cookie-always-on", "#047857", "#123b5d"),
    ("style.css", ".telegram-community-button:hover", "#052E16 !important", "#123B5D !important"),
    ("tutorial-navigation.css", ".reader-toolbar.reader-toolbar a.reader-toolbar__next", "#124e48 !important", "#123b5d !important"),
    ("tutorial-navigation.css", ".reader-sequence-route-label", "#087c78", "#123b5d"),
    ("tutorial-navigation.css", ".reader-sequence .reader-sequence-grid a.reader-path-card .reader-path-card__eyebrow", "#6fe0cc", "#d8eeff"),
    ("tutorial-navigation.css", ".reader-sequence .reader-sequence-utilities a.reader-path-card:hover", "#087c78", "#17549a"),
    ("tutorial-navigation.css", ".reader-sequence .reader-sequence-utilities .reader-path-card__title", "#234354", "#102f47"),
]
CLASS_CHANGES = {
    "index.html": [
        ('<h3 class="text-lg font-bold text-slate-900 mb-2 group-hover:text-emerald-700 transition-colors">Linux, HPC and Workflows', '<h3 class="text-lg font-bold text-slate-900 mb-2 group-hover:text-blue-800 transition-colors">Linux, HPC and Workflows'),
        ('<span class="inline-block mt-3 text-xs font-bold text-emerald-600 uppercase tracking-wider">10 tutorials', '<span class="inline-block mt-3 text-xs font-bold text-blue-700 uppercase tracking-wider">10 tutorials'),
        ('<span class="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">Package Management', '<span class="bg-emerald-100 text-blue-900 text-xs font-semibold px-2.5 py-0.5 rounded-full">Package Management'),
        ('<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-emerald-700 transition-colors">Micromamba Environments for Bioinformatics', '<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-800 transition-colors">Micromamba Environments for Bioinformatics'),
        ('<span class="bg-cyan-100 text-cyan-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">HPC', '<span class="bg-cyan-100 text-blue-900 text-xs font-semibold px-2.5 py-0.5 rounded-full">HPC'),
        ('<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-cyan-700 transition-colors">Connecting to HPC', '<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-800 transition-colors">Connecting to HPC'),
        ('<span class="bg-teal-100 text-teal-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">Metagenomics', '<span class="bg-teal-100 text-blue-900 text-xs font-semibold px-2.5 py-0.5 rounded-full">Metagenomics'),
        ('<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-teal-700 transition-colors">Kraken2 and Bracken: Shotgun Metagenomics', '<h3 class="text-lg font-bold text-gray-900 mb-2 group-hover:text-blue-800 transition-colors">Kraken2 and Bracken: Shotgun Metagenomics'),
    ],
    "services.html": [
        ("bg-emerald-50 text-emerald-600 font-semibold rounded-lg", "bg-emerald-50 text-blue-800 font-semibold rounded-lg"),
    ],
}
CSS_PATHS = frozenset(path for path, *_ in CSS_CHANGES)
CHANGED_STYLESHEETS = {"style.css", "home-page.min.css", "home-catalogue.css", "start-here.css", "tutorial-navigation.css"}


def _rule_block(source, selector):
    matches = list(re.finditer(re.escape(selector) + r"\s*\{", source))
    blocks = []
    for match in matches:
        opening = source.find("{", match.start())
        depth = 1
        for index in range(opening + 1, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append((match.start(), opening, index + 1))
                    break
        else:
            raise AssertionError(f"unterminated CSS rule {selector!r}")
    if not blocks:
        raise AssertionError(f"expected selector rule {selector!r}")
    return blocks


def _replace_color(source, selector, old, new):
    candidates = []
    for start, opening, end in _rule_block(source, selector):
        block = source[start:end]
        declarations = list(re.finditer(r"(?<![-\w])color\s*:\s*([^;]+);", block))
        hits = [m for m in declarations if m.group(1).strip() == old]
        if len(hits) == 1:
            candidates.append((start, end, block, hits[0]))
    if len(candidates) != 1:
        raise AssertionError(f"{selector}: expected one exact color:{old} rule, found {len(candidates)}")
    start, end, block, match = candidates[0]
    updated = block[:match.start(1)] + new + block[match.end(1):]
    return source[:start] + updated + source[end:]


def _expected_html_after_allowed_changes(relative, before):
    expected = before
    # Only stylesheet hrefs for the named changed assets may be cache-busted.
    pattern = re.compile(r'(?P<prefix>\bhref\s*=\s*["\'])(?P<url>[^"\']+\.css\?v=[^"\']+)(?P<suffix>["\'])')
    def cache_update(match):
        url = match.group("url")
        basename = url.rsplit("/", 1)[-1].split("?", 1)[0]
        if basename not in CHANGED_STYLESHEETS:
            return match.group(0)
        return match.group("prefix") + url.rsplit("?v=", 1)[0] + "?v=" + READER_TEXT_VERSION + match.group("suffix")
    expected = pattern.sub(cache_update, expected)
    for old, new in CLASS_CHANGES.get(relative, []):
        if expected.count(old) != 1:
            raise AssertionError(f"expected one authorized utility fragment in {relative}: {old[:70]}")
        expected = expected.replace(old, new, 1)
    return expected


@unittest.skip("Historical PR baseline superseded by site-wide back-to-top overhaul")
class ReaderTextColourTests(unittest.TestCase):
    def test_css_rule_and_declaration_structure_is_identical_after_only_23_color_value_masks(self):
        self.assertEqual(len(CSS_CHANGES), 23)
        normalized = {}
        for path in CSS_PATHS:
            normalized[path] = pre_reader_text_bytes(path).decode("utf-8")
        for path, selector, old, new in CSS_CHANGES:
            with self.subTest(path=path, selector=selector):
                normalized[path] = _replace_color(normalized[path], selector, old, new)
        for path in CSS_PATHS:
            with self.subTest(path=path, structure="all non-color bytes"):
                current = restore_latest_review_asset(path, (ROOT / path).read_bytes())
                if path == "start-here.css":
                    current = restore_start_here_desktop_asset(path, current)
                elif path == "home-catalogue.css":
                    current = restore_home_catalogue_banner_asset(path, current)
                if path in R_FIRST_ASSET_PATHS:
                    current = restore_r_first_asset(path, current)
                self.assertEqual(normalized[path].encode(), current)

    def test_all_70_html_files_have_only_approved_cache_href_and_utility_class_changes(self):
        patches = page_patches()
        self.assertEqual(len(patches), 70)
        for relative in sorted(patches):
            with self.subTest(page=relative):
                before = pre_reader_text_bytes(relative).decode("utf-8")
                current = (ROOT / relative).read_text(encoding="utf-8")
                expected = _expected_html_after_allowed_changes(relative, before)
                # R-first article/navigation chunks are an independent, exact
                # reviewed layer. Reverse only those pinned chunks before
                # checking that this reader-colour pass changed only its own
                # cache tokens and utility classes.
                r_first_normalized = normalize_r_first_revision(relative, current)
                self.assertEqual(r_first_normalized, expected)
                self.assertEqual(normalize_reader_text(relative, current), before)

    def test_code_script_image_and_non_utility_content_are_unchanged(self):
        tags = (r"<pre\b[^>]*>.*?</pre\s*>", r"<code\b[^>]*>.*?</code\s*>",
                r"<script\b[^>]*>.*?</script\s*>", r"<img\b[^>]*>")
        for relative in sorted(page_patches()):
            before = pre_reader_text_bytes(relative).decode("utf-8")
            current = (ROOT / relative).read_text(encoding="utf-8")
            current = normalize_r_first_revision(relative, current)
            with self.subTest(page=relative):
                for pattern in tags:
                    self.assertEqual(re.findall(pattern, before, re.I | re.S),
                                     re.findall(pattern, current, re.I | re.S), pattern)

    def test_unknown_changes_remain_visible_and_duplicate_exact_fragments_are_rejected(self):
        relative = "tutorials/statistics-for-bioinformatics.html"
        current = (ROOT / relative).read_text(encoding="utf-8")
        baseline = pre_reader_text_bytes(relative).decode("utf-8")
        unapproved = current.replace("<title>", "<title>Unapproved ", 1)
        self.assertNotEqual(normalize_reader_text(relative, unapproved), baseline)
        target_patch = page_patches()[relative][0]["after"]
        with self.assertRaisesRegex(AssertionError, "duplicate exact reader-text patch"):
            normalize_reader_text(relative, current + target_patch)
        # A changed cache token embedded within an authorized chunk is not guessed or stripped.
        patch = page_patches()[relative][0]
        mutated = current.replace(patch["after"], patch["after"].replace(READER_TEXT_VERSION, "unapproved-version", 1), 1)
        self.assertNotEqual(normalize_reader_text(relative, mutated), baseline)

    def test_every_changed_asset_has_a_complete_sha256_pin_and_mutation_is_rejected(self):
        self.assertEqual(set(READER_TEXT_ASSET_SHA256), set(READER_TEXT_ASSET_PATHS))
        for relative in sorted(READER_TEXT_ASSET_PATHS):
            with self.subTest(asset=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(verify_reader_text_file(relative, data), data)
                with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                    verify_reader_text_file(relative, data + b"\n")

    def test_ci_workflow_fixes_change_only_dependency_setup_and_cleanup_order(self):
        review_path = ".github/workflows/tutorial-review.yml"
        previous = pre_reader_text_bytes(review_path).decode("utf-8")
        anchor = "      - name: Verify generated legacy redirects\n"
        setup = ("      - name: Install existing CSS build dependencies\n"
                 "        run: npm ci --prefix tools --no-audit --no-fund\n")
        self.assertEqual(previous.count(anchor), 1)
        self.assertEqual(normalize_latest_review(review_path, (ROOT / review_path).read_text()), previous.replace(anchor, setup + anchor, 1))
        deploy_path = ".github/workflows/static.yml"
        previous = pre_reader_text_bytes(deploy_path).decode("utf-8")
        cleanup = "          rm -rf tools/node_modules\n"
        tests = "          python3 -m unittest discover -s tests -v\n"
        self.assertEqual(previous.count(cleanup), 1)
        self.assertEqual(previous.count(tests), 1)
        expected = previous.replace(cleanup, "", 1).replace(tests, tests + cleanup, 1)
        current = (ROOT / deploy_path).read_text()
        self.assertEqual(current, expected)
        self.assertLess(current.index(tests), current.index(cleanup))
        self.assertLess(current.index(cleanup), current.index("      - name: Upload artifact"))

    def test_generated_home_bundle_and_navigation_ui_checks_are_reproducible(self):
        before = (ROOT / "home-page.min.css").read_bytes()
        result = subprocess.run(["node", "tools/build-home-css.cjs"], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((ROOT / "home-page.min.css").read_bytes(), before)
        result = subprocess.run([sys.executable, "tools/generate_tutorial_ui.py", "--check"],
                                cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
