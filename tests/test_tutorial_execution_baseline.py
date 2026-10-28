"""Safety and idempotence tests for the exact 2026-10-25 regression adapter."""
import hashlib
from pathlib import Path
import re
import unittest

from r_first_revision_baseline import (
    normalize_r_first_revision, pre_r_first_bytes, restore_r_first_asset,
)
from tutorial_execution_baseline import (
    BASE_COMMIT, FIXTURE_PATH, FIXTURE_SHA256, _base_bytes, _fixture,
    new_execution_asset_paths, normalize_execution_delta,
    overlapping_execution_asset_paths, restore_overlapping_execution_asset,
    verify_execution_asset_or_overlapping, verify_new_execution_asset,
)
from navigation_performance_baseline import normalize_navigation_performance

ROOT = Path(__file__).resolve().parents[1]


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class TutorialExecutionBaselineTests(unittest.TestCase):
    def test_fixture_pin_and_explicit_scopes_are_frozen(self):
        raw = FIXTURE_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA256)
        fixture = _fixture()
        self.assertEqual(fixture["base_commit"], BASE_COMMIT)
        self.assertEqual(len(fixture["page_map"]), 58)
        self.assertEqual(len(fixture["overlapping_asset_map"]), 6)
        self.assertEqual(len(fixture["new_asset_map"]), 14)
        self.assertTrue(all(path.startswith("tutorials/") for path in fixture["page_map"]))

    def test_exact_pages_restore_to_base_and_are_idempotent(self):
        fixture = _fixture()
        for relative, entry in fixture["page_map"].items():
            with self.subTest(page=relative):
                current = (ROOT / relative).read_text(encoding="utf-8")
                baseline = _base_bytes(relative).decode("utf-8")
                historical = pre_r_first_bytes(relative).decode("utf-8")
                restored = normalize_execution_delta(relative, current)
                self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(), entry["base_sha256"])
                self.assertEqual(restored, baseline)
                self.assertEqual(normalize_execution_delta(relative, restored), restored)
                self.assertEqual(normalize_r_first_revision(relative, current), historical)
                self.assertEqual(normalize_r_first_revision(relative, restored), historical)

    def test_code_prose_date_and_cache_key_mutations_are_not_hidden(self):
        relative = "tutorials/data-visualization-fundamentals.html"
        current = (ROOT / relative).read_text(encoding="utf-8")
        baseline = pre_r_first_bytes(relative).decode("utf-8")
        code = re.search(r"<pre\b[^>]*>.*?</pre>", current, re.S)
        self.assertIsNotNone(code, "regression probe needs a displayed code block")
        mutated_code = current[:code.end()] + "<!-- unapproved code-boundary mutation -->" + current[code.end():]
        mutations = {
            "code": mutated_code,
            "prose": current.replace("<p>", "<p>Unapproved prose. ", 1),
            "date": current.replace('"dateModified": "2026-10-25"', '"dateModified": "2099-01-01"', 1),
            "cache_key": current.replace(
                "20261026-startup-v1", "unapproved-cache-key", 1
            ),
        }
        for label, text in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(text, current)
                # The startup adapter must still peel its exact pinned hunks;
                # all unknown edits remain in the normalized historical text.
                self.assertEqual(
                    normalize_execution_delta(relative, text),
                    normalize_navigation_performance(relative, text),
                )
                normalized = normalize_r_first_revision(relative, text)
                self.assertNotEqual(normalized, baseline)
                if label == "date":
                    self.assertIn('"dateModified": "2099-01-01"', normalized)
                elif label == "cache_key":
                    self.assertIn("unapproved-cache-key", normalized)
                elif label == "prose":
                    self.assertIn("Unapproved prose.", normalized)

    def test_new_asset_scope_is_exact_and_mutation_rejected(self):
        self.assertEqual(len(new_execution_asset_paths()), 14)
        for relative in sorted(new_execution_asset_paths()):
            with self.subTest(asset=relative):
                data = (ROOT / relative).read_bytes()
                self.assertEqual(verify_new_execution_asset(relative, data), data)
                self.assertEqual(verify_execution_asset_or_overlapping(relative, data), data)
                with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                    verify_new_execution_asset(relative, data + b"\n")
        with self.assertRaisesRegex(AssertionError, "not an authorized new execution asset"):
            verify_new_execution_asset("images/unapproved.png", b"anything")

    def test_overlapping_asset_layer_restores_only_exact_current_digest(self):
        self.assertEqual(len(overlapping_execution_asset_paths()), 6)
        for relative in sorted(overlapping_execution_asset_paths()):
            with self.subTest(asset=relative):
                current = (ROOT / relative).read_bytes()
                restored = restore_overlapping_execution_asset(relative, current)
                self.assertEqual(restored, _base_bytes(relative))
                self.assertEqual(restore_overlapping_execution_asset(relative, restored), restored)
                self.assertEqual(verify_execution_asset_or_overlapping(relative, current), current)
                self.assertEqual(restore_overlapping_execution_asset(relative, current + b"\n"), current + b"\n")
                self.assertEqual(restore_r_first_asset(relative, current), pre_r_first_bytes(relative))

    def test_unknown_paths_and_non_delta_text_are_not_authorized(self):
        sample = "<p>untouched</p>\n"
        self.assertEqual(normalize_execution_delta("tutorials/unlisted.html", sample), sample)
        self.assertEqual(normalize_execution_delta("files/private.R", sample), sample)
        with self.assertRaisesRegex(AssertionError, "not an authorized execution asset"):
            verify_execution_asset_or_overlapping("files/private.R", b"payload")


if __name__ == "__main__":
    unittest.main()
