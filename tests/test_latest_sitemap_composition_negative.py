"""Negative checks that latest sitemap composition never hides unknown edits."""
from pathlib import Path
import unittest

from latest_review_baseline import normalize_latest_review
from remaining_validation_baseline import normalize_remaining_validation_sitemap

ROOT = Path(__file__).resolve().parents[1]


class LatestSitemapCompositionNegativeTests(unittest.TestCase):
    def test_unknown_url_node_attribute_remains_visible_and_is_rejected(self):
        current = (ROOT / "sitemap.xml").read_bytes()
        mutation = current.replace(b"<url>", b'<url unexpected="visible">', 1)
        self.assertNotEqual(mutation, current)

        # Exact fixture chunks reverse independently; the unpinned node change
        # remains visible and prevents the older whole-asset layers from matching.
        latest_normalized = normalize_latest_review(
            "sitemap.xml", mutation.decode("utf-8")
        ).encode("utf-8")
        self.assertIn(b'<url unexpected="visible">', latest_normalized)
        with self.assertRaisesRegex(AssertionError, "unapproved sitemap lastmod"):
            normalize_remaining_validation_sitemap(mutation)


if __name__ == "__main__":
    unittest.main()
