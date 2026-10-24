"""Protect the historical-test adapter itself from hiding arbitrary source edits."""
from pathlib import Path
import re
import unittest

from tutorial_ui_baseline import (
    TUTORIAL_UI_PATHS, normalize_tutorial_ui, page_patches,
    pre_ui_bytes, verify_tutorial_ui_file,
)

ROOT = Path(__file__).resolve().parents[1]

class ExactTutorialUIBaselineTests(unittest.TestCase):
    def test_every_page_restores_to_the_exact_last_published_bytes(self):
        self.assertEqual(len(page_patches()), 58)
        for relative in page_patches():
            with self.subTest(page=relative):
                original = pre_ui_bytes(relative).decode()
                current = (ROOT / relative).read_text()
                restored = normalize_tutorial_ui(relative, current)
                self.assertEqual(restored, original)
                self.assertEqual(normalize_tutorial_ui(relative, original), original)
                self.assertEqual(normalize_tutorial_ui(relative, restored), restored)

    def test_every_explicit_ui_asset_matches_its_pinned_complete_digest(self):
        self.assertEqual(len(TUTORIAL_UI_PATHS), 16)
        for relative in TUTORIAL_UI_PATHS:
            with self.subTest(path=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(verify_tutorial_ui_file(relative, data), data)
                with self.assertRaisesRegex(AssertionError, 'fingerprint mismatch'):
                    verify_tutorial_ui_file(relative, data + b'\n')
        with self.assertRaisesRegex(AssertionError, 'not an authorized'):
            verify_tutorial_ui_file('files/unrelated.csv', b'anything')

    def test_homepage_css_rebuild_changes_its_checksum_only(self):
        current = (ROOT / 'home-page.min.css').read_bytes()
        original = pre_ui_bytes('home-page.min.css')
        self.assertEqual(current.split(b'\n', 1)[1], original.split(b'\n', 1)[1])

    def test_lesson_code_inline_scripts_and_metadata_edits_are_never_hidden(self):
        relative = 'tutorials/statistics-for-bioinformatics.html'
        current = (ROOT / relative).read_text()
        original = pre_ui_bytes(relative).decode()
        candidates = [
            current.replace('import numpy as np', 'import numpy as unexpected', 1),
            current.replace('window.STATIC_RENDERED = true;', 'window.STATIC_RENDERED = false;', 1),
            current.replace('A two-group test is only meaningful', 'An unapproved claim is meaningful', 1),
            re.sub(r'("dateModified"\s*:\s*)"[^"]+"', r'\1"2099-01-01"', current, count=1),
            current.replace('<script src="../copy-code.js?v=20261024-reader-ui"></script>', '<script src="https://unapproved.invalid/extra.js"></script>', 1),
        ]
        for mutated in candidates:
            self.assertTrue(mutated != current, 'Mutation probe must actually modify the source')
            self.assertNotEqual(normalize_tutorial_ui(relative, mutated), original)

    def test_unknown_paths_and_unrelated_fragments_are_unchanged(self):
        for relative in ['index.html', 'files/unrelated.csv', 'tutorials/missing.html']:
            text = '<script>unapproved();</script><p>ordinary text</p>'
            self.assertEqual(normalize_tutorial_ui(relative, text), text)

if __name__ == '__main__': unittest.main()
