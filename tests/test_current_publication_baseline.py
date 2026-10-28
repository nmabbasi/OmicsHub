"""Tests for exact normalization of the latest pinned mainline revisions."""
import hashlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from current_publication_baseline import (
    ROOT,
    _css_rules,
    current_published_bytes,
    normalize_approved_navigation,
    normalize_current_publication,
    normalize_latest_publication,
    publication_layers,
)


class CurrentPublicationBaselineTests(unittest.TestCase):
    def test_each_exact_mainline_blob_restores_to_its_pinned_parent(self):
        layers = publication_layers()
        for layer_index, layer in enumerate(layers):
            for relative_path, entry in layer["files"].items():
                with self.subTest(layer=layer["name"], path=relative_path):
                    expected = entry["base"]
                    for older_layer in layers[layer_index + 1:]:
                        older = older_layer["files"].get(relative_path)
                        if older is not None and hashlib.sha256(expected).hexdigest() == older["head_sha256"]:
                            expected = older["base"]
                    self.assertEqual(
                        normalize_current_publication(relative_path, entry["head"]),
                        expected,
                    )

    def test_generated_homepage_css_is_pinned_and_changes_only_its_hash_comment(self):
        layers = publication_layers()
        approved_layer = next(layer for layer in layers if layer["name"] == "approved-navigation")
        approved = approved_layer["files"]["home-page.min.css"]
        generated = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(
            hashlib.sha256(generated).hexdigest(),
            approved["generated_head_sha256"],
        )
        self.assertEqual(_css_rules(generated), _css_rules(approved["base"]))
        self.assertEqual(normalize_current_publication("home-page.min.css", generated), approved["base"])

    def test_approved_navigation_adapter_stops_at_exact_immediate_parent(self):
        approved = next(
            layer for layer in publication_layers() if layer["name"] == "approved-navigation"
        )
        relative_path = "tutorials/16s-rrna-prokka-annotation.html"
        entry = approved["files"][relative_path]
        self.assertEqual(normalize_approved_navigation(relative_path, entry["head"]), entry["base"])
        self.assertEqual(normalize_approved_navigation(relative_path, entry["base"]), entry["base"])
        changed = entry["head"] + b"<!-- unknown scope mutation -->\n"
        self.assertEqual(normalize_approved_navigation(relative_path, changed), changed)
        generated = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(
            normalize_approved_navigation("home-page.min.css", generated),
            approved["files"]["home-page.min.css"]["base"],
        )

    def test_current_published_sitemap_has_67_unique_canonical_urls_and_page_dates(self):
        sitemap = current_published_bytes("sitemap.xml")
        self.assertEqual((ROOT / "sitemap.xml").read_bytes(), sitemap)
        root = ET.fromstring(sitemap)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = root.findall("s:url", ns)
        urls = [entry.findtext("s:loc", namespaces=ns) for entry in entries]
        dates = {
            entry.findtext("s:loc", namespaces=ns): entry.findtext("s:lastmod", namespaces=ns)
            for entry in entries
        }
        self.assertEqual(len(urls), 67)
        self.assertEqual(len(set(urls)), 67)
        self.assertTrue(all(url.startswith("https://theomicshub.com/") for url in urls))
        self.assertTrue(all("?" not in url for url in urls))
        self.assertEqual(set(dates.values()), {"2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24", "2026-10-25"})
        self.assertEqual(dates["https://theomicshub.com/about.html"], "2026-10-23")
        self.assertEqual(
            dates["https://theomicshub.com/tutorials/wes-variant-calling-pipeline.html"],
            "2026-10-25",
        )
        latest = publication_layers()[0]["files"]["sitemap.xml"]
        self.assertEqual(normalize_latest_publication("sitemap.xml", sitemap), latest["base"])

    def test_unknown_mutations_and_unlisted_paths_remain_visible(self):
        relative_path = "tutorials/scrna-seq-basics.html"
        current = (ROOT / relative_path).read_bytes()
        changed = current + b"<!-- unknown scope mutation -->\n"
        self.assertEqual(normalize_current_publication(relative_path, changed), changed)
        self.assertEqual(
            normalize_current_publication("unlisted/path.txt", b"unregistered bytes"),
            b"unregistered bytes",
        )
        css = (ROOT / "home-page.min.css").read_bytes()
        changed_css = css + b"/* unknown css mutation */\n"
        self.assertEqual(normalize_current_publication("home-page.min.css", changed_css), changed_css)
        sitemap = current_published_bytes("sitemap.xml")
        changed_sitemap = sitemap.replace(
            b"<lastmod>2026-10-23</lastmod>", b"<lastmod>2026-10-24</lastmod>", 1
        )
        self.assertNotEqual(changed_sitemap, sitemap)
        self.assertEqual(normalize_current_publication("sitemap.xml", changed_sitemap), changed_sitemap)
        self.assertEqual(normalize_latest_publication("sitemap.xml", changed_sitemap), changed_sitemap)


if __name__ == "__main__":
    unittest.main()
