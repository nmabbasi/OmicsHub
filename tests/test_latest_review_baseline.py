"""Mutation regressions for the newest exact review-baseline layer."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import latest_review_baseline as baseline
from latest_review_baseline import (
    FIXTURE_PATHS, FIXTURE_PATH, _check_context, latest_review_fixture,
    normalize_latest_review, normalize_patch_chunks, restore_latest_review_asset,
)
from startup_generated_asset_baseline import restore_startup_generated_asset
from coffee_removal_baseline import restore_coffee_removal_text
from gget_mobile_baseline import restore_gget_mobile_bytes
from current_publication_baseline import normalize_current_publication


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class LatestReviewBaselineTests(unittest.TestCase):
    def setUp(self):
        self.before = "one\ntwo\nthree\nold literal\nfive\nsix\nseven\n"
        self.after = "one\ntwo\nthree\nnew literal\nfive\nsix\nseven\n"
        self.patch = {"before": self.before, "after": self.after}

    def test_exact_contextual_chunk_reverses(self):
        _check_context(self.before, self.after, "fixture probe")
        self.assertEqual(
            normalize_patch_chunks(self.after, [self.patch], "probe.html"),
            self.before,
        )

    def test_unrecognized_edit_remains_visible_after_known_chunk_reversal(self):
        mutation = self.after + "<!-- mutation remains visible -->\n"
        normalized = normalize_patch_chunks(mutation, [self.patch], "probe.html")
        self.assertEqual(normalized, self.before + "<!-- mutation remains visible -->\n")

    def test_mutation_inside_context_prevents_chunk_reversal(self):
        mutation = self.after.replace("two\n", "two changed\n", 1)
        self.assertEqual(
            normalize_patch_chunks(mutation, [self.patch], "probe.html"),
            mutation,
        )

    def test_duplicate_exact_chunk_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "duplicate exact latest-review"):
            normalize_patch_chunks(self.after + self.after, [self.patch], "probe.html")

    def test_changed_hunk_requires_matching_three_line_context(self):
        with self.assertRaisesRegex(AssertionError, "three-line context"):
            _check_context(
                "one\ntwo\nold\nfour\nfive\nsix\n",
                "one\ntwo\nnew\nfour\nfive\nsix\n",
                "too-small-context",
            )

    def test_final_fixture_is_hash_pinned_and_closed_to_exact_review_paths(self):
        records = latest_review_fixture()
        self.assertEqual(set(records), FIXTURE_PATHS)
        self.assertEqual(hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), baseline.FIXTURE_SHA256)

    def test_final_text_and_asset_changes_restore_exactly_to_base(self):
        for relative_path, record in latest_review_fixture().items():
            with self.subTest(path=relative_path):
                current = (baseline.ROOT / relative_path).read_bytes()
                current = normalize_current_publication(relative_path, current)
                current = restore_gget_mobile_bytes(relative_path, current)
                current_text = baseline.normalize_navigation_performance(
                    relative_path, current.decode("utf-8")
                ).encode("utf-8") if record["kind"] == "text" else current
                if record["kind"] == "asset":
                    current_text = restore_startup_generated_asset(
                        relative_path, current_text, "main"
                    )
                self.assertEqual(hashlib.sha256(current_text).hexdigest(), record["current_sha256"])
                if record["kind"] == "text":
                    normalized = normalize_latest_review(relative_path, current.decode("utf-8")).encode("utf-8")
                    base = record["base_bytes"]
                else:
                    normalized = restore_latest_review_asset(relative_path, current)
                    base = record["base_bytes"]
                self.assertEqual(normalized, base)

    def test_unrecognized_text_mutation_survives_known_patch_reversal(self):
        path = "index.html"
        current = normalize_current_publication(
            path, (baseline.ROOT / path).read_bytes()
        ).decode("utf-8")
        # Restore the closed newer delta before probing this historical layer.
        # Raw coffee-review mutations are separately rejected by its strict tests.
        current = restore_coffee_removal_text(path, current)
        mutation = "<!-- unrecognized mutation remains visible -->\n"
        normalized = normalize_latest_review(path, current + mutation)
        base = latest_review_fixture()[path]["base_bytes"].decode("utf-8")
        self.assertEqual(normalized, base + mutation)

    def test_asset_is_restored_only_for_the_complete_pinned_current_sha(self):
        path = "home-page.min.css"
        current = (baseline.ROOT / path).read_bytes()
        base = latest_review_fixture()[path]["base_bytes"]
        self.assertEqual(restore_latest_review_asset(path, current), base)
        changed = current[:-1] + bytes([current[-1] ^ 1])
        self.assertEqual(restore_latest_review_asset(path, changed), changed)

    def test_text_assets_also_require_the_complete_pinned_current_sha(self):
        for path in ['script.js', 'style.css', 'sitemap.xml', '.github/workflows/tutorial-review.yml']:
            with self.subTest(path=path):
                current = (baseline.ROOT / path).read_bytes()
                base = latest_review_fixture()[path]['base_bytes']
                self.assertEqual(restore_latest_review_asset(path, current), base)
                changed = current + b'\nunknown mutation\n'
                self.assertEqual(restore_latest_review_asset(path, changed), changed)

    def test_validly_repinned_fixture_cannot_expand_path_scope(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        fixture["files"]["unapproved/anything.html"] = {}
        raw = json.dumps(fixture).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_bytes(raw)
            latest_review_fixture.cache_clear()
            try:
                with patch.object(baseline, "FIXTURE_PATH", path), patch.object(
                    baseline, "FIXTURE_SHA256", hashlib.sha256(raw).hexdigest()
                ):
                    with self.assertRaisesRegex(AssertionError, "header or scope"):
                        latest_review_fixture()
            finally:
                latest_review_fixture.cache_clear()


if __name__ == "__main__":
    unittest.main()
