"""Regression tests for composing the exact execution sitemap delta first."""
import re
import unittest

from remaining_validation_baseline import normalize_remaining_validation_sitemap
from resource_content_baseline import normalize_resource_sitemap
from tutorial_execution_baseline import (
    BASE_COMMIT,
    _base_bytes,
    restore_overlapping_execution_asset,
)
from current_publication_baseline import normalize_current_publication
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ExecutionSitemapCompositionTests(unittest.TestCase):
    def test_exact_execution_asset_restores_to_122bd_then_historical_layers(self):
        current = normalize_current_publication(
            "sitemap.xml", (ROOT / "sitemap.xml").read_bytes()
        )
        execution_base = _base_bytes("sitemap.xml")
        self.assertIsNotNone(execution_base)
        self.assertEqual(restore_overlapping_execution_asset("sitemap.xml", current), execution_base)

        composed_current = normalize_remaining_validation_sitemap(
            normalize_resource_sitemap(current)
        )
        composed_base = normalize_remaining_validation_sitemap(
            normalize_resource_sitemap(execution_base)
        )
        self.assertEqual(composed_current, composed_base)
        self.assertEqual(
            normalize_remaining_validation_sitemap(
                normalize_resource_sitemap(composed_current)
            ),
            composed_current,
        )
        self.assertEqual(BASE_COMMIT, "122bd466feb11efd304769faff19e77bd40a98b4")

    def test_direct_remaining_entry_point_composes_and_rejects_unknown_dates(self):
        current = (ROOT / "sitemap.xml").read_bytes()
        base = _base_bytes("sitemap.xml")
        self.assertEqual(
            normalize_remaining_validation_sitemap(current),
            normalize_remaining_validation_sitemap(base),
        )
        mutation = current.replace(b"<lastmod>2026-10-28</lastmod>", b"<lastmod>2099-01-01</lastmod>", 1)
        self.assertNotEqual(mutation, current)
        with self.assertRaisesRegex(AssertionError, "unapproved sitemap lastmod"):
            normalize_remaining_validation_sitemap(mutation)

    def test_unpinned_sitemap_mutations_are_not_absorbed_by_asset_restore(self):
        current = (ROOT / "sitemap.xml").read_bytes()
        restored = restore_overlapping_execution_asset("sitemap.xml", current)

        # Alter one row's date and a separate row attribute. Neither modified
        # whole-file byte sequence may be mistaken for the pinned execution asset.
        target = b"https://theomicshub.com/tutorials/wes-variant-calling-pipeline.html"
        row = re.search(rb"<url>\s*<loc>" + re.escape(target) + rb"</loc>.*?</url>", current, re.S)
        self.assertIsNotNone(row)
        mutated_row = row.group(0).replace(b"<lastmod>2026-10-28</lastmod>", b"<lastmod>2099-01-01</lastmod>", 1)
        self.assertNotEqual(mutated_row, row.group(0))
        future_date = current[:row.start()] + mutated_row + current[row.end():]
        self.assertEqual(restore_overlapping_execution_asset("sitemap.xml", future_date), future_date)

        attribute_mutation = current.replace(b"<url>", b'<url mutation="visible">', 1)
        self.assertEqual(restore_overlapping_execution_asset("sitemap.xml", attribute_mutation), attribute_mutation)
        try:
            normalized_attribute_mutation = normalize_resource_sitemap(attribute_mutation)
        except AssertionError:
            pass  # Legacy row-level guards may reject the unpinned full-file edit.
        else:
            self.assertIn(b'<url mutation="visible">', normalized_attribute_mutation)

        try:
            normalized_future_date = normalize_remaining_validation_sitemap(
                normalize_resource_sitemap(future_date)
            )
        except AssertionError:
            pass  # Existing row guards may reject the unknown date outright.
        else:
            self.assertIn(b"2099-01-01", normalized_future_date)
            self.assertNotEqual(
                normalized_future_date,
                normalize_remaining_validation_sitemap(normalize_resource_sitemap(current)),
            )


if __name__ == "__main__":
    unittest.main()
