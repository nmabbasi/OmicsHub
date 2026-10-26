"""Focused regression tests for the review-only lesson URL migration."""
import hashlib
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from route_migration_baseline import (
    NEW_ROUTE, OLD_ROUTE, PRE_MIGRATION_COMMIT, ROUTE_MIGRATION_SHA256,
    exact_route_migration_paths, is_redirect_stub, normalize_route_migration,
    pre_migration_bytes, published_tutorial_paths,
)

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://theomicshub.com/"


class RouteMigrationBaselineTests(unittest.TestCase):
    def test_every_allowlisted_public_file_matches_its_complete_hash_pin(self):
        self.assertEqual(len(exact_route_migration_paths(ROOT)), len(ROUTE_MIGRATION_SHA256))
        for relative_path, expected in ROUTE_MIGRATION_SHA256.items():
            with self.subTest(path=relative_path):
                current = (ROOT / relative_path).read_bytes()
                self.assertEqual(hashlib.sha256(current).hexdigest(), expected)
                mapped, restored = normalize_route_migration(relative_path, current)
                self.assertIsNotNone(pre_migration_bytes(mapped))
                self.assertEqual(restored, pre_migration_bytes(mapped))

    def test_unknown_content_mutations_are_not_normalized_away(self):
        for relative_path in ("tutorials.html", OLD_ROUTE, NEW_ROUTE):
            with self.subTest(path=relative_path):
                current = (ROOT / relative_path).read_bytes() + b"\n<!-- unrelated mutation -->\n"
                mapped, observed = normalize_route_migration(relative_path, current)
                self.assertEqual(observed, current)
                self.assertEqual(mapped, OLD_ROUTE if relative_path in {OLD_ROUTE, NEW_ROUTE} else relative_path)

    def test_redirect_stub_is_not_counted_as_a_lesson_but_remains_present(self):
        lessons = published_tutorial_paths(ROOT)
        relative = {page.relative_to(ROOT).as_posix() for page in lessons}
        self.assertEqual(len(lessons), 58)
        self.assertIn(NEW_ROUTE, relative)
        self.assertNotIn(OLD_ROUTE, relative)
        old_page = ROOT / OLD_ROUTE
        self.assertTrue(old_page.is_file())
        self.assertTrue(is_redirect_stub(old_page))
        html = old_page.read_text(encoding="utf-8")
        self.assertIn('content="0; url=rna-seq-count-matrix-qc-cpm.html"', html)
        self.assertIn('name="robots" content="noindex, follow"', html)

    def test_catalogue_and_sitemap_publish_only_the_new_canonical_url(self):
        catalogue = json.loads((ROOT / "tools/catalogue-learning.json").read_text(encoding="utf-8"))
        lessons = catalogue["lessons"]
        self.assertIn(Path(NEW_ROUTE).stem, lessons)
        self.assertNotIn(Path(OLD_ROUTE).stem, lessons)
        sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in sitemap.findall("s:url/s:loc", ns)]
        self.assertIn(SITE + NEW_ROUTE, locations)
        self.assertNotIn(SITE + OLD_ROUTE, locations)

    def test_nested_and_root_aliases_point_directly_to_the_new_canonical_page(self):
        root_alias = ROOT / "autonomous-research-orchestrator.html"
        root_html = root_alias.read_text(encoding="utf-8")
        self.assertIn("url=tutorials/rna-seq-count-matrix-qc-cpm.html", root_html)
        old_html = (ROOT / OLD_ROUTE).read_text(encoding="utf-8")
        self.assertIn("url=rna-seq-count-matrix-qc-cpm.html", old_html)
        new_html = (ROOT / NEW_ROUTE).read_text(encoding="utf-8")
        self.assertIn(f"href=\"{SITE}{NEW_ROUTE}\" rel=\"canonical\"", new_html)
        self.assertIn(f'content="{SITE}{NEW_ROUTE}" property="og:url"', new_html)
        self.assertIn(f'"@id": "{SITE}{NEW_ROUTE}"', new_html)


if __name__ == "__main__":
    unittest.main()
