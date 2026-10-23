"""Regression checks for accurate dates on the Oct 23, 2026 content revision."""
import json
from datetime import datetime
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://theomicshub.com/"
MODIFIED = {
    "tutorials/cell-type-annotation-methods.html": "2026-08-20",
    "tutorials/scrna-seq-integration-strategies.html": "2026-09-04",
    "tutorials/advanced-visualization-packages.html": "2026-08-26",
    "tutorials/ai-prompt-engineering-seurat.html": "2026-08-27",
    "tutorials/command-line-part3.html": "2026-08-21",
    "tutorials/deterministic-retrieval-gget-ai.html": "2026-08-22",
    "tutorials/mcp-zotero.html": "2026-08-29",
    "tutorials/modern-bioinformatics-methods-2026.html": "2026-09-15",
    "tutorials/single-cell-foundation-models.html": "2026-08-23",
    "tutorials/spatial-transcriptomics-r-python.html": "2026-08-19",
    "tutorials/wes-variant-calling-pipeline.html": "2026-09-04",
}
# These PR changes only propagate adjacent-lesson title updates in navigation;
# they are intentionally not represented as content revisions.
NAVIGATION_ONLY = (
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/notebooklm-research-brain.html",
    "tutorials/protein-structure-design-alphafold.html",
)
SCHEMA = re.compile(r'<script[^>]*type="application/ld\+json">(.*?)</script>', re.S)
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class ContentModificationDateTests(unittest.TestCase):
    def setUp(self):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        self.sitemap_dates = {
            entry.findtext("s:loc", namespaces=NS): entry.findtext("s:lastmod", namespaces=NS)
            for entry in root.findall("s:url", NS)
        }

    def entity(self, relative_path):
        page = ROOT / relative_path
        blocks = SCHEMA.findall(page.read_text(encoding="utf-8"))
        self.assertEqual(len(blocks), 1, relative_path)
        return json.loads(blocks[0])

    def test_substantively_revised_articles_have_matching_dates(self):
        for relative_path, published in MODIFIED.items():
            with self.subTest(page=relative_path):
                entity = self.entity(relative_path)
                self.assertEqual(entity["datePublished"], published)
                self.assertEqual(entity["dateModified"], "2026-10-23")
                page_html = (ROOT / relative_path).read_text(encoding="utf-8")
                visible_dates = re.findall(
                    r"Updated\s+(\d{1,2} [A-Za-z]+ \d{4})", page_html
                )
                for visible_date in visible_dates:
                    self.assertEqual(
                        datetime.strptime(visible_date, "%d %B %Y").date().isoformat(),
                        entity["dateModified"],
                    )
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-23"
                )

    def test_catalogue_and_about_sitemap_dates_reflect_content_revision(self):
        for relative_path in ("about.html", "tutorials.html"):
            with self.subTest(page=relative_path):
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-23"
                )

    def test_consent_policy_revision_dates_match_the_sitemap(self):
        for relative_path in ("pages/privacy.html", "pages/cookie.html"):
            with self.subTest(page=relative_path):
                self.assertIn(
                    "Last updated: October 23, 2026",
                    (ROOT / relative_path).read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-23"
                )

    def test_navigation_only_and_unchanged_lessons_are_not_freshened(self):
        for relative_path in NAVIGATION_ONLY:
            with self.subTest(page=relative_path):
                entity = self.entity(relative_path)
                self.assertEqual(entity["dateModified"], "2026-10-21")
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-21"
                )
        unchanged = "tutorials/command-line-part1.html"
        self.assertEqual(self.entity(unchanged)["dateModified"], "2026-10-21")
        self.assertEqual(self.sitemap_dates[SITE + unchanged], "2026-10-21")

    def test_sitemap_stays_at_67_unique_canonical_urls(self):
        urls = list(self.sitemap_dates)
        self.assertEqual(len(urls), 67)
        self.assertEqual(len(set(urls)), 67)
        self.assertTrue(all(url.startswith(SITE) for url in urls))
        self.assertTrue(all("?" not in url for url in urls))
        expected_updated = {SITE + path for path in MODIFIED}
        expected_updated.update({SITE + "about.html", SITE + "tutorials.html"})
        expected_updated.update({SITE + "pages/privacy.html", SITE + "pages/cookie.html"})
        self.assertEqual(
            {url for url, lastmod in self.sitemap_dates.items() if lastmod == "2026-10-23"},
            expected_updated,
        )
        tutorial_urls = [url for url in urls if "/tutorials/" in url]
        self.assertEqual(len(tutorial_urls), 58)
        self.assertTrue(all(url.endswith(".html") for url in tutorial_urls))
        # Retired tutorial routes stay out; only these current HTML pages live at root.
        root_html = {
            urlsplit(url).path
            for url in urls
            if urlsplit(url).path.endswith(".html")
            and "/tutorials/" not in urlsplit(url).path
            and not urlsplit(url).path.startswith("/pages/")
        }
        self.assertEqual(
            root_html,
            {"/about.html", "/contact.html", "/start-here.html", "/tutorials.html"},
        )


if __name__ == "__main__":
    unittest.main()
