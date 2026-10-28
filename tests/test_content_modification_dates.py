"""Regression checks for accurate dates on the Oct 23, 2026 content revision."""
import json
from datetime import datetime
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from remaining_validation_baseline import load_manifest, published_bytes
from advanced_validation_baseline import (
    allowed_article_paths as advanced_article_paths,
    load_manifest as load_advanced_manifest,
    published_bytes as advanced_published_bytes,
)
from resource_content_baseline import (
    load_manifest as load_resource_content_manifest,
    published_bytes as resource_published_bytes,
)
from r_first_revision_baseline import content_paths as r_first_content_paths
from r_first_revision_baseline import normalize_r_first_revision, pre_r_first_bytes

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
    "tutorials/hpc-submission-part1.html": "2026-09-06",
    "tutorials/reproducible-workflows-snakemake-nextflow.html": "2026-09-21",
    "tutorials/command-line-part2.html": "2026-09-16",
    "tutorials/conda-mamba-part1.html": "2026-08-30",
    "tutorials/hpc-basic-commands.html": "2026-09-11",
    "tutorials/scrna-seq-trajectory-inference.html": "2026-09-17",
    "tutorials/advanced-ai-single-cell.html": "2026-08-25",
    "tutorials/ai-coding-cursor-aider.html": "2026-09-08",
    "tutorials/computer-data-fundamentals.html": "2026-08-16",
    "tutorials/statistics-for-bioinformatics.html": "2026-08-15",
    "tutorials/experimental-design-batch-effects.html": "2026-09-01",
    "tutorials/r-tidyverse-fundamentals.html": "2026-09-05",
}
TIDYVERSE_TARGET = "tutorials/r-tidyverse-fundamentals.html"
TARGET_MODIFIED_DATE = "2026-10-24"
# These earlier PR changes only propagate adjacent-lesson title updates;
# they remain navigation-only, unlike the six newly revised lessons above.
NAVIGATION_ONLY = (
    "tutorials/notebooklm-research-brain.html",
    "tutorials/protein-structure-design-alphafold.html",
)
SCHEMA = re.compile(r'<script[^>]*type="application/ld\+json">(.*?)</script>', re.S)
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class ContentModificationDateTests(unittest.TestCase):
    def setUp(self):
        # Keep the real current sitemap output visible: its sitewide lastmod
        # date is distinct from each page's content dateModified value.
        current_sitemap = (ROOT / "sitemap.xml").read_bytes()
        root = ET.fromstring(current_sitemap)
        self.sitemap_dates = {
            entry.findtext("s:loc", namespaces=NS): entry.findtext("s:lastmod", namespaces=NS)
            for entry in root.findall("s:url", NS)
        }

    def entity(self, relative_path):
        page = ROOT / relative_path
        text = normalize_r_first_revision(relative_path, page.read_text(encoding="utf-8"))
        blocks = SCHEMA.findall(text)
        self.assertEqual(len(blocks), 1, relative_path)
        return json.loads(blocks[0])

    def test_article_content_dates_remain_approved_and_sitemap_lastmods_are_current(self):
        advanced_dates = load_advanced_manifest()["articles"]
        resource_dates = load_resource_content_manifest()["articles"]
        revised_pages = dict(MODIFIED)
        for relative_path in advanced_article_paths():
            revised_pages.setdefault(relative_path, None)
        for relative_path in resource_dates:
            revised_pages.setdefault(relative_path, None)
        for relative_path, published in revised_pages.items():
            with self.subTest(page=relative_path):
                entity = self.entity(relative_path)
                r_first = relative_path in r_first_content_paths()
                if r_first:
                    original = json.loads(
                        SCHEMA.findall(pre_r_first_bytes(relative_path).decode("utf-8"))[0]
                    )
                    published = original["datePublished"]
                elif relative_path in resource_dates:
                    original = json.loads(
                        SCHEMA.findall(resource_published_bytes(relative_path).decode("utf-8"))[0]
                    )
                    published = original["datePublished"]
                elif published is None:
                    original = json.loads(
                        SCHEMA.findall(advanced_published_bytes(relative_path).decode("utf-8"))[0]
                    )
                    published = original["datePublished"]
                modified = original["dateModified"] if r_first else (
                    resource_dates[relative_path]["date_modified_approved"]
                    if relative_path in resource_dates
                    else TARGET_MODIFIED_DATE if relative_path == TIDYVERSE_TARGET
                    else advanced_dates[relative_path]["date_modified_approved"]
                    if relative_path in advanced_article_paths()
                    else "2026-10-23"
                )
                self.assertEqual(entity["datePublished"], published)
                self.assertEqual(entity["dateModified"], modified)
                page_html = normalize_r_first_revision(
                    relative_path, (ROOT / relative_path).read_text(encoding="utf-8")
                )
                visible_dates = re.findall(
                    r"Updated\s+(\d{1,2} [A-Za-z]+ \d{4})", page_html
                )
                if r_first:
                    old_html = pre_r_first_bytes(relative_path).decode("utf-8")
                    self.assertEqual(
                        visible_dates,
                        re.findall(r"Updated\s+(\d{1,2} [A-Za-z]+ \d{4})", old_html),
                    )
                elif relative_path in resource_dates:
                    approved_visible = resource_dates[relative_path]["visible_updated_approved"]
                    self.assertEqual(
                        visible_dates,
                        [approved_visible] if approved_visible else [],
                    )
                elif relative_path in advanced_article_paths():
                    approved_visible = advanced_dates[relative_path]["visible_updated_approved"]
                    self.assertEqual(
                        visible_dates,
                        [approved_visible] if approved_visible else [],
                    )
                for visible_date in visible_dates:
                    self.assertEqual(
                        datetime.strptime(visible_date, "%d %B %Y").date().isoformat(),
                        modified,
                    )
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-28"
                )

    def test_catalogue_and_beginner_paths_have_current_sitemap_lastmods(self):
        for relative_path in ("about.html", "tutorials.html"):
            with self.subTest(page=relative_path):
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-28"
                )
        self.assertEqual(self.sitemap_dates[SITE + "start-here.html"], "2026-10-28")
        self.assertEqual(self.entity("start-here.html")["dateModified"], TARGET_MODIFIED_DATE)

    def test_consent_policy_content_dates_remain_separate_from_sitemap_lastmods(self):
        for relative_path in ("pages/privacy.html", "pages/cookie.html"):
            with self.subTest(page=relative_path):
                self.assertIn(
                    "Last updated: October 23, 2026",
                    (ROOT / relative_path).read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-28"
                )

    def test_remaining_validation_articles_use_only_manifest_approved_dates(self):
        manifest = load_manifest()
        for relative_path, entry in manifest["files"].items():
            with self.subTest(page=relative_path):
                current = self.entity(relative_path)
                baseline_text = published_bytes(relative_path).decode("utf-8")
                baseline_blocks = SCHEMA.findall(baseline_text)
                self.assertEqual(len(baseline_blocks), 1)
                original = json.loads(baseline_blocks[0])
                self.assertEqual(current["datePublished"], original["datePublished"])
                self.assertEqual(current["dateModified"], entry["date_modified_approved"])
                visible_dates = re.findall(
                    r"Updated\s+(\d{1,2} [A-Za-z]+ \d{4})",
                    normalize_r_first_revision(
                        relative_path,
                        (ROOT / relative_path).read_text(encoding="utf-8"),
                    ),
                )
                expected_visible = entry["visible_updated_approved"]
                self.assertEqual(visible_dates, [expected_visible] if expected_visible else [])
                if expected_visible:
                    self.assertEqual(
                        datetime.strptime(visible_dates[0], "%d %B %Y").date().isoformat(),
                        entry["date_modified_approved"],
                    )
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path],
                    "2026-10-28",
                )

    def test_navigation_only_and_unchanged_lessons_keep_content_dates(self):
        resource_dates = load_resource_content_manifest()["articles"]
        for relative_path in NAVIGATION_ONLY:
            with self.subTest(page=relative_path):
                entity = self.entity(relative_path)
                entry = resource_dates.get(relative_path)
                expected = entry["date_modified_approved"] if entry else "2026-10-21"
                self.assertEqual(entity["dateModified"], expected)
                self.assertEqual(
                    self.sitemap_dates[SITE + relative_path], "2026-10-28"
                )
        unchanged = "tutorials/command-line-part1.html"
        self.assertEqual(self.entity(unchanged)["dateModified"], "2026-10-21")
        self.assertEqual(self.sitemap_dates[SITE + unchanged], "2026-10-28")

    def test_sitemap_stays_at_67_unique_canonical_urls(self):
        urls = list(self.sitemap_dates)
        self.assertEqual(len(urls), 67)
        self.assertEqual(len(set(urls)), 67)
        self.assertTrue(all(url.startswith(SITE) for url in urls))
        self.assertTrue(all("?" not in url for url in urls))
        baseline_root = ET.fromstring(pre_r_first_bytes("sitemap.xml"))
        baseline_dates = {
            entry.findtext("s:loc", namespaces=NS): entry.findtext("s:lastmod", namespaces=NS)
            for entry in baseline_root.findall("s:url", NS)
        }
        self.assertEqual(list(self.sitemap_dates), list(baseline_dates))
        self.assertEqual(set(self.sitemap_dates.values()), {"2026-10-28"})
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
