"""Focused invariants for the remaining bounded reference-support edits.

All comparisons use immutable published main d42231e, never a moving branch or
external site. These checks intentionally verify the cited links and local
wording only; they do not infer that a reference is valid merely because it
returns an HTTP response.
"""
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

from latest_review_baseline import normalize_latest_review
from navigation_performance_baseline import (
    APPROVED_PATHS as NAVIGATION_PERFORMANCE_PATHS,
    normalize_navigation_performance,
)
from startup_performance_baseline import (
    ASSET_PATHS as STARTUP_ASSET_PATHS,
    TUTORIAL_PATHS as STARTUP_TUTORIAL_PATHS,
    restore_startup_performance_asset,
)
from startup_generated_asset_baseline import restore_startup_generated_asset

from editorial_review_baseline import (
    PUBLIC_PATHS as EDITORIAL_PUBLIC_PATHS,
    normalize_editorial_review,
)
from start_here_desktop_baseline import (
    normalize_start_here_desktop_html,
    restore_start_here_desktop_asset,
)
from coffee_removal_baseline import coffee_removal_fixture, restore_coffee_removal_bytes
from optional_report_baseline import (
    OPTIONAL_REPORT_PATHS,
    verify_optional_report_file,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "d42231e"
SITE = "https://theomicshub.com/"
EXPECTED_PUBLIC_PATHS = {
    "tutorials/scrna-seq-basics.html",
    "tutorials/wes-variant-calling-pipeline.html",
    "tutorials/notebooklm-research-brain.html",
    "sitemap.xml",
    "start-here.html",
    "start-here.css",
    "tutorial-library.css",
}
NOTEBOOKLM = "tutorials/notebooklm-research-brain.html"
NOTEBOOKLM_URL = SITE + NOTEBOOKLM
SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# These are already-existing review/test infrastructure files, not public
# website sources. Keep this list explicit so the public-change scope check
# cannot silently exempt a broad directory.
TEST_INFRASTRUCTURE_PATHS = {
    'tests/coffee_removal_baseline.py',
    'tests/optional_report_baseline.py',
    'tests/fixtures/coffee-removal-review.json',
    'tests/test_coffee_removal_baseline.py',
    'tests/fixtures/gget-mobile-baseline.json',
    'tests/gget_mobile_baseline.py',
    'tests/test_gget_mobile_baseline.py',
    '.github/workflows/tutorial-review.yml',
    'tests/browser_navigation_performance.py',
    'tests/browser_sitewide_reference_fixes.py',
    'tests/browser_start_here_ui.py',
    'tests/browser_startup_performance.py',
    'tests/browser_startup_preservation.py',
    'tests/browser_tutorial_reader_ui.py',
    'tests/editorial_review_baseline.py',
    'tests/fixtures/editorial-review-edits.json',
    'tests/fixtures/latest-review-edits.json',
    'tests/fixtures/navigation-performance-edits.json',
    'tests/fixtures/startup-performance-edits.json',
    'tests/generate_latest_review_fixture.py',
    'tests/generate_startup_performance_fixture.py',
    'tests/home_catalogue_baseline.py',
    'tests/latest_review_baseline.py',
    'tests/navigation_performance_baseline.py',
    'tests/r_first_revision_baseline.py',
    'tests/reader_text_colour_baseline.py',
    'tests/remaining_validation_baseline.py',
    'tests/resource_content_baseline.py',
    'tests/start_here_baseline.py',
    'tests/start_here_desktop_baseline.py',
    'tests/startup_generated_asset_baseline.py',
    'tests/startup_performance_baseline.py',
    'tests/test_code_tabs_digest_memoization.js',
    'tests/test_editorial_review_baseline.py',
    'tests/test_editorial_scope_fixes.py',
    'tests/test_home_catalogue_scope.py',
    'tests/test_home_catalogue_ui.py',
    'tests/test_latest_review_baseline.py',
    'tests/test_latest_sitemap_composition_negative.py',
    'tests/test_learning_promises.py',
    'tests/test_navigation_performance_baseline.py',
    'tests/test_r_first_revision_baseline.py',
    'tests/test_reader_layout_batching.js',
    'tests/test_reader_punctuation.py',
    'tests/test_reader_text_colours.py',
    'tests/test_remaining_reference_support.py',
    'tests/test_remaining_validation_scope.py',
    'tests/test_revision_trajectory.py',
    'tests/test_beginner_walkthrough_scope.py',
    'tests/test_six_lesson_revision_scope.py',
    'tests/test_tidyverse_setup_scope.py',
    'tests/test_ubuntu_tidyverse_scope.py',
    'tests/test_search_reference_aliases.js',
    'tests/test_sitewide_reference_fixes.py',
    'tests/test_start_here_blue_learning.py',
    'tests/test_start_here_desktop_baseline.py',
    'tests/test_start_here_hover.py',
    'tests/test_start_here_ui.py',
    'tests/test_start_here_visual_polish.py',
    'tests/test_startup_performance_baseline.py',
    'tests/test_text_alignment.py',
    'tests/test_tutorial_execution_baseline.py',
    'tests/test_tutorial_reader_ui.py',
    'tests/test_tutorial_startup.py',
    'tests/test_verified_analysis_figures.py',
    'tests/tutorial_execution_baseline.py',
    'tests/tutorial_ui_baseline.py',
    'tools/generate_latest_review_fixture.py',
}


PROTECTED_UI_FILES = (
    "index.html",
    "start-here.html",
    "start-here.css",
    "start-here.js",
    "tutorials.html",
    "home-page.min.css",
    "home-catalogue.css",
    "catalogue-browser.js",
    "script.js",
    "style.css",
)
ASSET_SUFFIXES = {
    ".avif", ".css", ".gif", ".ico", ".jpeg", ".jpg", ".js", ".png",
    ".svg", ".ttf", ".webp", ".woff", ".woff2",
}


class InlineScriptParser(HTMLParser):
    """Collect inline executable script attributes and exact source bodies."""

    EXECUTABLE_TYPES = {
        "", "application/ecmascript", "application/javascript", "module",
        "text/ecmascript", "text/javascript",
    }

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self._script = None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self._script = {"attrs": dict(attrs), "body": []}

    def handle_data(self, data):
        if self._script is not None:
            self._script["body"].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script is not None:
            attrs = self._script["attrs"]
            script_type = attrs.get("type", "").strip().lower()
            if "src" not in attrs and script_type in self.EXECUTABLE_TYPES:
                self.scripts.append((attrs, "".join(self._script["body"])))
            self._script = None


def baseline_bytes(path):
    return subprocess.check_output(
        ["git", "show", f"{BASE_COMMIT}:{path}"], cwd=ROOT
    )


def baseline_text(path):
    return baseline_bytes(path).decode("utf-8")


def current_text(path):
    current = (ROOT / path).read_text(encoding="utf-8")
    current = normalize_editorial_review(path, current)
    current = normalize_start_here_desktop_html(path, current)
    return normalize_navigation_performance(path, current)


def tutorial_paths_at_base():
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT, "tutorials"],
        cwd=ROOT, text=True,
    )
    return sorted(
        path for path in output.splitlines()
        if re.fullmatch(r"tutorials/[^/]+\.html", path)
    )


def strip_one(text, pattern, label):
    updated, count = re.subn(pattern, "", text, count=1, flags=re.S)
    if count != 1:
        raise AssertionError(f"expected exactly one {label}; found {count}")
    if re.search(pattern, updated, re.S):
        raise AssertionError(f"more than one {label} remains")
    return updated


def jsonld_article(html):
    blocks = re.findall(
        r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.S | re.I,
    )
    if len(blocks) != 1:
        raise AssertionError(f"expected one JSON-LD article block, found {len(blocks)}")
    return json.loads(blocks[0])


def sitemap_lastmods(xml_text):
    root = ET.fromstring(xml_text)
    return {
        item.findtext("s:loc", namespaces=SITEMAP_NS):
        item.findtext("s:lastmod", namespaces=SITEMAP_NS)
        for item in root.findall("s:url", SITEMAP_NS)
    }


class RemainingReferenceSupportTests(unittest.TestCase):
    def test_only_the_four_authorized_public_paths_changed_since_published_main(self):
        changed = set(subprocess.check_output(
            ["git", "diff", "--name-only", BASE_COMMIT, "--"],
            cwd=ROOT, text=True,
        ).splitlines())
        # A tutorial path is excluded only if strict whole-file restoration
        # produces the exact d42231e bytes; otherwise it remains visible here.
        performance_only = set()
        coffee = coffee_removal_fixture()
        for path, entry in coffee.items():
            self.assertEqual(
                restore_coffee_removal_bytes(path, (ROOT / path).read_bytes()),
                entry['base_bytes'],
            )
        verified_report_paths = changed & OPTIONAL_REPORT_PATHS
        for path in sorted(verified_report_paths):
            verify_optional_report_file(path, (ROOT / path).read_bytes())
        for path in changed & (
            NAVIGATION_PERFORMANCE_PATHS | STARTUP_TUTORIAL_PATHS
            | STARTUP_ASSET_PATHS | EDITORIAL_PUBLIC_PATHS
            | (set(coffee) - EXPECTED_PUBLIC_PATHS) | {"home-page.min.css"}
        ):
            if path in STARTUP_ASSET_PATHS:
                restored = restore_startup_performance_asset(path, (ROOT / path).read_bytes())
            elif path == "home-page.min.css":
                restored = restore_startup_generated_asset(
                    path, (ROOT / path).read_bytes(), "main"
                )
            else:
                restored = current_text(path).encode("utf-8")
            if restored == baseline_bytes(path):
                performance_only.add(path)
        public_changed = changed - TEST_INFRASTRUCTURE_PATHS - performance_only - verified_report_paths
        self.assertEqual(public_changed, EXPECTED_PUBLIC_PATHS)

    def test_all_58_tutorials_preserve_pre_code_and_executable_inline_javascript(self):
        paths = tutorial_paths_at_base()
        self.assertEqual(len(paths), 58)
        current_paths = sorted(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / "tutorials").glob("*.html")
        )
        self.assertEqual(current_paths, paths)
        for path in paths:
            with self.subTest(tutorial=path):
                before = baseline_text(path)
                after = current_text(path)
                for tag in ("pre", "code"):
                    pattern = rf"<{tag}\b[^>]*>.*?</{tag}\s*>"
                    self.assertEqual(
                        re.findall(pattern, after, re.S | re.I),
                        re.findall(pattern, before, re.S | re.I),
                        f"{tag} markup/content changed",
                    )
                self.assertEqual(
                    InlineScriptParser(after).scripts,
                    InlineScriptParser(before).scripts,
                    "executable inline JavaScript changed",
                )

    def test_homepage_start_here_catalogue_and_site_assets_are_byte_preserved(self):
        protected = set(PROTECTED_UI_FILES)
        tracked = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT],
            cwd=ROOT, text=True,
        ).splitlines()
        protected.update(
            path for path in tracked
            if path.startswith(("assets/", "images/"))
            or ("/" not in path and Path(path).suffix.lower() in ASSET_SUFFIXES)
        )
        for path in sorted(protected):
            with self.subTest(path=path):
                data = (ROOT / path).read_bytes()
                if path == "start-here.css":
                    data = restore_start_here_desktop_asset(path, data)
                elif path == "start-here.html":
                    data = normalize_start_here_desktop_html(
                        path, data.decode("utf-8")
                    ).encode("utf-8")
                data = restore_startup_performance_asset(path, data)
                data = restore_startup_generated_asset(path, data, "main")
                self.assertEqual(data, baseline_bytes(path))

    def test_scrna_reference_changes_are_exactly_the_support_link_and_bibliographic_label(self):
        path = "tutorials/scrna-seq-basics.html"
        before, after = baseline_text(path), current_text(path)
        old_link = (
            r'<li><a href="https://support\.10xgenomics\.com/single-cell-gene-expression">'
            r'10x Genomics Single Cell Gene Expression support and dataset descriptions</a></li>'
        )
        new_link = (
            r'<li><a href="https://www\.10xgenomics\.com/support/single-cell-gene-expression">'
            r'10x Universal 3′ Gene Expression support and dataset links</a></li>'
        )
        old_citation = re.escape(
            '<li><a href="https://www.nature.com/articles/nbt.4096">'
            'Stuart et al., 2019. Comprehensive Integration of Single-Cell Data (Seurat v3 paper)</a>'
        )
        new_citation = re.escape(
            '<li><a href="https://www.nature.com/articles/nbt.4096">'
            'Butler et al., 2018. Integrating single-cell transcriptomic data across different conditions, technologies, and species (Seurat integration)</a>'
        )
        self.assertRegex(before, old_link)
        self.assertRegex(after, new_link)
        self.assertRegex(before, old_citation)
        self.assertRegex(after, new_citation)
        self.assertNotIn("https://support.10xgenomics.com/single-cell-gene-expression", after)
        before_remainder = strip_one(before, old_link, "legacy 10x support link")
        after_remainder = strip_one(after, new_link, "narrow Universal 3′ support link")
        self.assertEqual(
            strip_one(before_remainder, old_citation, "old mismatched Nature citation"),
            strip_one(after_remainder, new_citation, "correct Butler 2018 citation"),
            "the scRNA edit must not change unrelated page content",
        )

    def test_wes_igsr_advice_uses_collection_filters_and_stops_on_unverified_inputs(self):
        path = "tutorials/wes-variant-calling-pipeline.html"
        before, after = baseline_text(path), current_text(path)
        paragraph = r'<p>To source public teaching data, begin at the .*?</p>'
        before_match = re.search(paragraph, before, re.S)
        after_match = re.search(paragraph, after, re.S)
        self.assertIsNotNone(before_match)
        self.assertIsNotNone(after_match)
        updated = after_match.group(0)
        self.assertIn("which links data collections", updated)
        self.assertIn("technology and data-type filters", updated)
        self.assertIn("not a preassembled compatible bundle", updated)
        self.assertIn(
            "If a suitable exome FASTQ pair or its matching capture BED cannot be verified, stop",
            updated,
        )
        self.assertIn("Do not substitute a GIAB truth-region BED", updated)
        self.assertEqual(
            before[:before_match.start()] + before[before_match.end():],
            after[:after_match.start()] + after[after_match.end():],
            "the WES change must stay within the IGSR sourcing paragraph",
        )

    def test_notebooklm_faq_and_usage_link_are_scoped_and_date_metadata_agrees(self):
        before, after = baseline_text(NOTEBOOKLM), current_text(NOTEBOOKLM)
        old_faq = (
            r'<li><a href="https://support\.google\.com/gemininotebook/answer/16269187\?hl=en">'
            r'Google Gemini Notebook frequently asked questions and current limits</a></li>'
        )
        new_faq = (
            r'<li><a href="https://support\.google\.com/gemininotebook/answer/16269187\?hl=en">'
            r'Google Gemini Notebook FAQs, citation limitations, and source-import troubleshooting</a></li>'
        )
        usage_paragraph = r'<p>Google changes product limits and availability\..*?</p>'
        before_article, after_article = jsonld_article(before), jsonld_article(after)
        self.assertRegex(before, old_faq)
        self.assertRegex(after, new_faq)
        self.assertRegex(after, r'href="https://support\.google\.com/gemininotebook/answer/17670842\?hl=en"')
        self.assertIn("current usage-limit guidance", after)
        self.assertNotIn("answer/17670842", before)
        self.assertEqual(before_article["datePublished"], after_article["datePublished"])
        self.assertEqual(after_article["datePublished"], "2026-09-08")
        self.assertEqual(after_article["dateModified"], "2026-10-25")

        before_remainder = strip_one(before, old_faq, "old NotebookLM FAQ label")
        after_remainder = strip_one(after, new_faq, "narrow NotebookLM FAQ label")
        before_remainder = strip_one(before_remainder, usage_paragraph, "old usage-limit paragraph")
        after_remainder = strip_one(after_remainder, usage_paragraph, "new usage-limit paragraph")
        before_remainder, before_count = re.subn(
            r'("dateModified"\s*:\s*)"2026-10-24"',
            r'\1"2026-10-25"', before_remainder, count=1,
        )
        self.assertEqual(before_count, 1)
        self.assertEqual(before_remainder, after_remainder)

        old_dates = sitemap_lastmods(baseline_text("sitemap.xml"))
        current_dates = sitemap_lastmods(current_text("sitemap.xml"))
        self.assertEqual(set(old_dates), set(current_dates))
        changed_dates = {
            url for url in old_dates if old_dates[url] != current_dates[url]
        }
        self.assertEqual(changed_dates, {NOTEBOOKLM_URL})
        self.assertEqual(current_dates[NOTEBOOKLM_URL], "2026-10-25")
        for page in (
            "tutorials/scrna-seq-basics.html",
            "tutorials/wes-variant-calling-pipeline.html",
            NOTEBOOKLM,
        ):
            with self.subTest(date_metadata=page):
                article = jsonld_article(current_text(page))
                self.assertEqual(
                    current_dates[SITE + page], article["dateModified"]
                )

    def test_unknown_text_and_executable_code_mutations_survive_literal_normalization(self):
        path = "tutorials/scrna-seq-basics.html"
        current = current_text(path)
        baseline_normalized = normalize_latest_review(path, current)
        for marker, mutation in (
            (
                "UNREVIEWED_TEXT_MUTATION",
                '<!-- UNREVIEWED_TEXT_MUTATION -->',
            ),
            (
                "UNREVIEWED_CODE_MUTATION",
                '<script>window.__UNREVIEWED_CODE_MUTATION__ = true;</script>',
            ),
        ):
            with self.subTest(mutation=marker):
                self.assertEqual(current.count("</body>"), 1)
                changed = current.replace("</body>", mutation + "</body>", 1)
                normalized = normalize_latest_review(path, changed)
                self.assertIn(marker, normalized)
                self.assertNotEqual(normalized, baseline_normalized)


if __name__ == "__main__":
    unittest.main()
