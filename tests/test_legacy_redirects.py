"""Regression tests for static recovery of confirmed historical tutorial URLs."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import subprocess
import sys
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "legacy-redirects.json"
GENERATOR = ROOT / "tools" / "generate_legacy_redirects.py"
EXPECTED_HISTORICAL_ALIASES = {
    "/1-Connection.html": "tutorials/hpc-connection.html",
    "/2-HPC_Basic_Commands.html": "tutorials/hpc-basic-commands.html",
    "/4-Support.html": "tutorials/hpc-support.html",
}


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals = []
        self.refreshes = []
        self.links = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        values = {name.lower(): value for name, value in attrs}
        if tag.lower() == "link" and values.get("rel", "").lower() == "canonical":
            self.canonicals.append(values.get("href"))
        elif tag.lower() == "meta":
            key = values.get("http-equiv", "").lower()
            if key == "refresh":
                self.refreshes.append(values.get("content", ""))
            if values.get("name", "").lower() == "robots":
                self.robots.append(values.get("content", ""))
        elif tag.lower() == "a":
            self.links.append(values.get("href"))


def parse_page(path: Path) -> PageMetadata:
    parser = PageMetadata()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


class LegacyRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.migrated = set(cls.manifest["migration_root_urls"])
        cls.aliases = cls.manifest["historical_aliases"]
        cls.redirects = {
            source: "tutorials/" + Path(source).name for source in cls.migrated
        } | cls.aliases

    def test_migration_mapping_is_complete_and_matches_all_58_current_tutorials(self):
        self.assertEqual(self.manifest["migration_commit"], "118e16e4a4ac4dcd4acf132c9019104784787d52")
        self.assertEqual(self.manifest["migration_root_url_count"], 58)
        self.assertEqual(len(self.migrated), 58)
        expected_root_urls = {"/" + path.name for path in (ROOT / "tutorials").glob("*.html")}
        self.assertEqual(self.migrated, expected_root_urls)
        # Each of the six externally identified examples is covered by the exact
        # old-root-name -> same-name /tutorials/ migration recorded in commit 118e16e.
        for name in (
            "advanced-ai-single-cell.html",
            "computer-data-fundamentals.html",
            "metatranscriptomics-functional-pathways.html",
            "transcriptomics-differential-expression.html",
            "scrna-seq-quality-control.html",
            "command-line-part1.html",
            "long-read-pacbio-nanopore.html",
        ):
            with self.subTest(path=name):
                self.assertIn("/" + name, self.migrated)

    def test_confirmed_earlier_hpc_aliases_have_their_historical_destinations(self):
        self.assertEqual(self.aliases, EXPECTED_HISTORICAL_ALIASES)
        self.assertEqual(self.redirects["/hpc-submission-part1.html"], "tutorials/hpc-submission-part1.html")
        # The tracked pre-migration submission page was hpc-submission-part1.html;
        # no numbered "3-..." HTML path is present in the repository history.
        self.assertNotIn("/3-HPC_Submission.html", self.redirects)

    def test_every_stub_exists_and_has_matching_refresh_canonical_and_accessible_link(self):
        for source, target in self.redirects.items():
            with self.subTest(source=source):
                stub_path = ROOT / source.lstrip("/")
                target_path = ROOT / target
                self.assertTrue(stub_path.is_file(), f"missing stub for {source}")
                self.assertTrue(target_path.is_file(), f"missing destination {target}")
                stub = parse_page(stub_path)
                target_page = parse_page(target_path)
                self.assertEqual(len(stub.refreshes), 1)
                self.assertEqual(stub.refreshes[0], f"0; url={target}")
                self.assertEqual(len(stub.canonicals), 1)
                self.assertEqual(len(target_page.canonicals), 1)
                self.assertEqual(stub.canonicals[0], target_page.canonicals[0])
                self.assertEqual(stub.links, [target])
                self.assertFalse(any("noindex" in directive.lower() for directive in stub.robots))

    def test_targets_are_relative_valid_and_do_not_chain(self):
        for source, target in self.redirects.items():
            with self.subTest(source=source):
                parsed = urlsplit(target)
                self.assertFalse(parsed.scheme or parsed.netloc or parsed.query or parsed.fragment)
                self.assertFalse(target.startswith("/"))
                self.assertNotIn("..", Path(target).parts)
                self.assertTrue(target.startswith("tutorials/"))
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), target))
                self.assertEqual(resolved, "/" + target)
                self.assertNotIn(resolved, self.redirects)
                canonical = parse_page(ROOT / target).canonicals[0]
                self.assertEqual(urlsplit(canonical).path, resolved)

    def test_redirect_stubs_are_not_in_sitemap_and_live_pages_are_not_overwritten(self):
        sitemap = ET.parse(ROOT / "sitemap.xml")
        locations = [element.text for element in sitemap.iter() if element.tag.endswith("loc")]
        paths = {urlsplit(location or "").path for location in locations}
        self.assertTrue(paths.isdisjoint(self.redirects))
        for unchanged_page in ("about.html", "contact.html", "start-here.html", "tutorials.html", "services.html"):
            with self.subTest(page=unchanged_page):
                self.assertNotIn("/" + unchanged_page, self.redirects)
                self.assertTrue((ROOT / unchanged_page).is_file())

    def test_generated_files_match_the_small_script(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Verified 61", result.stdout)


if __name__ == "__main__":
    unittest.main()
