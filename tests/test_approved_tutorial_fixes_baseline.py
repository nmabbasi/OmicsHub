"""Safety tests for the exact owner-approved November tutorial-fix layer."""
import hashlib
from pathlib import Path
import unittest

from approved_tutorial_fixes_baseline import (
    ASSET_PATHS,
    BASE_COMMIT,
    FIXTURE_PATH,
    FIXTURE_SHA256,
    PAGE_PATHS,
    _base_bytes,
    _fixture,
    approved_tutorial_fix_asset_paths,
    approved_tutorial_fix_page_paths,
    normalize_approved_tutorial_fix,
    restore_approved_tutorial_fix_asset,
)

ROOT = Path(__file__).resolve().parents[1]


class ApprovedTutorialFixBaselineTests(unittest.TestCase):
    def test_fixture_pin_and_exact_page_asset_scopes(self):
        raw = FIXTURE_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA256)
        fixture = _fixture()
        self.assertEqual(fixture["base_commit"], BASE_COMMIT)
        self.assertEqual(approved_tutorial_fix_page_paths(), frozenset(PAGE_PATHS))
        self.assertEqual(approved_tutorial_fix_asset_paths(), frozenset(ASSET_PATHS))

    def test_exact_pages_restore_to_main_and_are_idempotent(self):
        for relative in PAGE_PATHS:
            with self.subTest(page=relative):
                current = (ROOT / relative).read_text(encoding="utf-8")
                baseline = _base_bytes(relative).decode("utf-8")
                restored = normalize_approved_tutorial_fix(relative, current)
                self.assertEqual(restored, baseline)
                self.assertEqual(normalize_approved_tutorial_fix(relative, restored), restored)

    def test_unknown_page_mutations_are_not_hidden(self):
        for relative in PAGE_PATHS:
            with self.subTest(page=relative):
                current = (ROOT / relative).read_text(encoding="utf-8")
                mutated = current.replace("<title>", "<title>Unapproved edit ", 1)
                self.assertNotEqual(mutated, current)
                self.assertEqual(normalize_approved_tutorial_fix(relative, mutated), mutated)
        sample = "<p>Unrelated page</p>"
        self.assertEqual(normalize_approved_tutorial_fix("tutorials/unlisted.html", sample), sample)

    def test_exact_assets_restore_to_main_and_mutations_remain_visible(self):
        for relative in ASSET_PATHS:
            with self.subTest(asset=relative):
                current = (ROOT / relative).read_bytes()
                baseline = _base_bytes(relative)
                restored = restore_approved_tutorial_fix_asset(relative, current)
                self.assertEqual(restored, baseline)
                self.assertEqual(restore_approved_tutorial_fix_asset(relative, restored), restored)
                mutated = current + b"\n/* unapproved mutation */"
                self.assertEqual(restore_approved_tutorial_fix_asset(relative, mutated), mutated)
        sample = b"unrelated asset"
        self.assertEqual(
            restore_approved_tutorial_fix_asset("files/unlisted.txt", sample), sample
        )


if __name__ == "__main__":
    unittest.main()
