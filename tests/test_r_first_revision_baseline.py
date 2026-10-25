"""Safety tests for the R-first historical baseline adapter."""
import hashlib
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from r_first_revision_baseline import (
    AUTHORIZED_ARTICLE_PATHS, EXPECTED_CONTENT_PAGE_COUNT, EXPECTED_NAVIGATION_PAGE_COUNT,
    PRE_R_FIRST_COMMIT, R_FIRST_ASSET_PATHS, content_paths, navigation_paths,
    non_navigation_patches, normalize_r_first_revision, page_patches,
    pre_r_first_bytes, restore_r_first_asset, verify_r_first_asset,
)
from tutorial_ui_baseline import TUTORIAL_UI_PATHS
from tutorial_execution_baseline import (
    execution_date_paths, overlapping_execution_asset_paths,
    verify_execution_asset_or_overlapping,
)

ROOT = Path(__file__).resolve().parents[1]
TARGET_DATE = "2026-10-25"


def _jsonld(text):
    match = re.search(r'<script\s+type="application/ld\+json">([\s\S]*?)</script>', text)
    if not match:
        raise AssertionError("JSON-LD WebPage data not found")
    return json.loads(match.group(1))


def _sitemap_dates(data):
    root = ET.fromstring(data)
    return {
        element.findtext("loc"): element.findtext("lastmod")
        for element in root.findall("url")
    }


class RFirstRevisionBaselineTests(unittest.TestCase):
    def test_exact_chunks_restore_navigation_and_separate_start_here_to_merge_baseline(self):
        self.assertEqual(len(navigation_paths()), EXPECTED_NAVIGATION_PAGE_COUNT)
        self.assertEqual(set(page_patches()), set(navigation_paths()))
        self.assertEqual(len(content_paths()), EXPECTED_CONTENT_PAGE_COUNT)
        self.assertEqual(content_paths(), AUTHORIZED_ARTICLE_PATHS)
        self.assertTrue({
            "tutorials/introduction-to-bioinformatics.html",
            "tutorials/scrna-seq-basics.html",
            "tutorials/reproducible-workflows-snakemake-nextflow.html",
        }.issubset(content_paths()))
        self.assertEqual(set(non_navigation_patches()), {"start-here.html"})

        for relative in navigation_paths():
            with self.subTest(page=relative):
                published = pre_r_first_bytes(relative).decode("utf-8")
                current = (ROOT / relative).read_text(encoding="utf-8")
                restored = normalize_r_first_revision(relative, current)
                self.assertEqual(restored, published)
                self.assertEqual(normalize_r_first_revision(relative, published), published)
                self.assertEqual(normalize_r_first_revision(relative, restored), restored)

        original_start = pre_r_first_bytes("start-here.html").decode("utf-8")
        current_start = (ROOT / "start-here.html").read_text(encoding="utf-8")
        self.assertEqual(normalize_r_first_revision("start-here.html", current_start), original_start)
        self.assertEqual(normalize_r_first_revision("start-here.html", original_start), original_start)

    def test_only_actual_changed_articles_receive_dates_and_publication_dates_stay_fixed(self):
        self.assertEqual(len(content_paths()), EXPECTED_CONTENT_PAGE_COUNT)
        for relative in navigation_paths():
            with self.subTest(page=relative):
                current_text = (ROOT / relative).read_text(encoding="utf-8")
                baseline_text = pre_r_first_bytes(relative).decode("utf-8")
                current_meta = _jsonld(current_text)
                baseline_meta = _jsonld(baseline_text)
                self.assertEqual(current_meta.get("datePublished"), baseline_meta.get("datePublished"))
                if relative in content_paths() | execution_date_paths():
                    self.assertEqual(current_meta.get("dateModified"), TARGET_DATE)
                    visible = re.findall(r"Updated\s+([^<\n]+)", current_text)
                    if relative in execution_date_paths() - content_paths():
                        prior_visible = re.findall(r"Updated\s+([^<\n]+)", baseline_text)
                        self.assertEqual(visible, prior_visible)
                    else:
                        for label in visible:
                            self.assertRegex(label, r"^(?:2026-10-25|25 October 2026)$")
                else:
                    self.assertEqual(current_meta.get("dateModified"), baseline_meta.get("dateModified"))

        start_text = (ROOT / "start-here.html").read_text(encoding="utf-8")
        start_meta = _jsonld(start_text)
        baseline_start_meta = _jsonld(pre_r_first_bytes("start-here.html").decode("utf-8"))
        self.assertEqual(start_meta.get("dateModified"), TARGET_DATE)
        self.assertEqual(start_meta.get("datePublished"), baseline_start_meta.get("datePublished"))

        current_dates = _sitemap_dates((ROOT / "sitemap.xml").read_bytes())
        baseline_dates = _sitemap_dates(pre_r_first_bytes("sitemap.xml"))
        self.assertEqual(set(current_dates), set(baseline_dates))
        changed_urls = {
            f"https://theomicshub.com/{path}"
            for path in content_paths() | execution_date_paths()
        }
        changed_urls.add("https://theomicshub.com/start-here.html")
        for url, date in current_dates.items():
            expected = TARGET_DATE if url in changed_urls else baseline_dates[url]
            with self.subTest(sitemap_url=url):
                self.assertEqual(date, expected)

    def test_unrelated_prose_navigation_date_and_script_mutations_remain_visible(self):
        relative = "tutorials/statistics-for-bioinformatics.html"
        published = pre_r_first_bytes(relative).decode("utf-8")
        current = (ROOT / relative).read_text(encoding="utf-8")
        unrelated = current.replace("<title>", "<title>Unapproved edit — ", 1)
        self.assertNotEqual(normalize_r_first_revision(relative, unrelated), published)
        self.assertIn("Unapproved edit", normalize_r_first_revision(relative, unrelated))

        changed_nav = current.replace("Learning path", "Unapproved path label", 1)
        self.assertNotEqual(normalize_r_first_revision(relative, changed_nav), published)
        self.assertIn("Unapproved path label", normalize_r_first_revision(relative, changed_nav))

        src_match = re.search(r'<script src="[^\"]*copy-code\.js[^\"]*"', current)
        self.assertIsNotNone(src_match, "source mutation probe must find the page's copy-code script")
        source_mutation = current[:src_match.start()] + src_match.group(0).replace(
            "copy-code.js", "unapproved.js"
        ) + current[src_match.end():]
        source_result = normalize_r_first_revision(relative, source_mutation)
        self.assertNotEqual(source_result, published)
        self.assertIn("unapproved.js", source_result)

        article = "tutorials/data-visualization-fundamentals.html"
        article_current = (ROOT / article).read_text(encoding="utf-8")
        body_mutation = article_current.replace("R Markdown report", "unauthorized R report", 1)
        self.assertNotEqual(normalize_r_first_revision(article, body_mutation),
                            pre_r_first_bytes(article).decode("utf-8"))
        date_mutation = article_current.replace(
            '"dateModified": "2026-10-25"', '"dateModified": "2099-01-01"', 1
        )
        normalized_date_mutation = normalize_r_first_revision(article, date_mutation)
        self.assertNotEqual(normalized_date_mutation, pre_r_first_bytes(article).decode("utf-8"))
        self.assertIn('"dateModified": "2099-01-01"', normalized_date_mutation)

        start_current = (ROOT / "start-here.html").read_text(encoding="utf-8")
        start_mutation = start_current.replace("Start with R.", "Unapproved language.", 1)
        self.assertIn("Unapproved language.", normalize_r_first_revision("start-here.html", start_mutation))

    def test_only_explicit_full_hash_assets_are_accepted(self):
        self.assertTrue(R_FIRST_ASSET_PATHS)
        self.assertTrue(R_FIRST_ASSET_PATHS.issubset(TUTORIAL_UI_PATHS))
        self.assertIn("tools/catalogue-learning.json", R_FIRST_ASSET_PATHS)
        for relative in sorted(R_FIRST_ASSET_PATHS):
            with self.subTest(asset=relative):
                data = (ROOT / relative).read_bytes()
                if relative in overlapping_execution_asset_paths():
                    self.assertEqual(verify_execution_asset_or_overlapping(relative, data), data)
                    baseline = pre_r_first_bytes(relative)
                    self.assertEqual(restore_r_first_asset(relative, data), baseline)
                    with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                        restore_r_first_asset(relative, data + b"\n")
                    continue
                self.assertEqual(verify_r_first_asset(relative, data), data)
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 __import__("r_first_revision_baseline").R_FIRST_ASSET_SHA256[relative])
                with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                    verify_r_first_asset(relative, data + b"\n")
                baseline = pre_r_first_bytes(relative)
                restored = restore_r_first_asset(relative, data)
                self.assertEqual(restored, baseline if baseline is not None else data)
                if baseline is not None:
                    self.assertEqual(restore_r_first_asset(relative, restored), baseline)
                    with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                        restore_r_first_asset(relative, baseline + b"\n")

    def test_unknown_paths_are_never_implicitly_authorized(self):
        sample = "<p>Unrelated</p>"
        self.assertEqual(normalize_r_first_revision("files/unrelated.csv", sample), sample)
        self.assertEqual(normalize_r_first_revision("start-here.css", sample), sample)
        with self.assertRaisesRegex(AssertionError, "not an authorized R-first asset"):
            verify_r_first_asset("files/unrelated.csv", b"anything")


if __name__ == "__main__":
    unittest.main()
