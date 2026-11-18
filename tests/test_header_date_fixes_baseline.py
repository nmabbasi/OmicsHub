"""Safety tests for the owner-approved header date and reference fix baseline layer."""
from pathlib import Path
import unittest

from header_date_fixes_baseline import HEADER_REPLACEMENTS, normalize_header_date_fix

ROOT = Path(__file__).resolve().parents[1]


class HeaderDateFixesBaselineTests(unittest.TestCase):
    def test_clean_pages_restore_to_previous_header_or_reference_chunk(self):
        for relative, (clean, original) in HEADER_REPLACEMENTS.items():
            with self.subTest(page=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn(clean, text)
                restored = normalize_header_date_fix(relative, text)
                self.assertIn(original, restored)
                self.assertNotIn(clean, restored)

    def test_unrelated_pages_and_baseline_pages_are_untouched(self):
        sample = '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-09-22</span></div>'
        # Without 20261026-startup-v1, it remains untouched (idempotent on historical baselines)
        self.assertEqual(normalize_header_date_fix("tutorials/python-fundamentals-bioinformatics.html", sample), sample)
        self.assertEqual(normalize_header_date_fix("tutorials/other.html", sample), sample)


if __name__ == "__main__":
    unittest.main()
