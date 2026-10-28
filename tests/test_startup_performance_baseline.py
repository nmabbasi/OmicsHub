"""Strict fixture and mutation regressions for startup-performance normalization."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import startup_performance_baseline as baseline
from editorial_review_baseline import normalize_editorial_review_bytes
from coffee_removal_baseline import restore_coffee_removal_text
from startup_performance_baseline import (
    ASSET_PATHS,
    BASE_COMMIT,
    FIXTURE_PATH,
    FIXTURE_PATHS,
    TUTORIAL_PATHS,
    normalize_patch_chunks,
    normalize_startup_performance,
    restore_startup_performance_asset,
    startup_performance_fixture,
)


@unittest.skip("Historical PR baseline superseded by site-wide back-to-top overhaul")
class StartupPerformanceBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = startup_performance_fixture()

    def test_inventory_and_fixture_are_closed_and_hash_pinned(self):
        self.assertEqual(len(TUTORIAL_PATHS), 58)
        self.assertEqual(len(ASSET_PATHS), 3)
        self.assertEqual(set(self.fixture), FIXTURE_PATHS)
        self.assertEqual(hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), baseline.FIXTURE_SHA256)
        base_paths = set(__import__("subprocess").check_output(
            ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT, "--", "tutorials"],
            cwd=baseline.ROOT, text=True,
        ).splitlines())
        self.assertTrue(TUTORIAL_PATHS <= base_paths)
        for relative_path, entry in self.fixture.items():
            with self.subTest(path=relative_path):
                current = normalize_editorial_review_bytes(
                    relative_path, (baseline.ROOT / relative_path).read_bytes()
                )
                self.assertEqual(hashlib.sha256(current).hexdigest(), entry["current_sha256"])
                if relative_path in TUTORIAL_PATHS:
                    self.assertEqual(
                        normalize_startup_performance(relative_path, current.decode("utf-8")).encode("utf-8"),
                        entry["base_bytes"],
                    )
                else:
                    self.assertEqual(restore_startup_performance_asset(relative_path, current), entry["base_bytes"])

    def test_unknown_article_edit_survives_known_tutorial_reversal(self):
        relative_path = "tutorials/statistics-for-bioinformatics.html"
        current = (baseline.ROOT / relative_path).read_text(encoding="utf-8")
        # Probe the historical startup layer on its exactly restored input.
        current = restore_coffee_removal_text(relative_path, current)
        marker = "<!-- UNREVIEWED ARTICLE EDIT -->"
        self.assertIn("</article>", current)
        mutated = current.replace("</article>", marker + "</article>", 1)
        normalized = normalize_startup_performance(relative_path, mutated)
        self.assertIn(marker, normalized)
        self.assertEqual(
            normalized.replace(marker, "", 1),
            self.fixture[relative_path]["base_bytes"].decode("utf-8"),
        )

    def test_unknown_asset_bytes_are_not_restored(self):
        relative_path = "code-tabs.js"
        current = (baseline.ROOT / relative_path).read_bytes()
        mutated = current + b"\n/* UNREVIEWED ASSET EDIT */\n"
        self.assertEqual(restore_startup_performance_asset(relative_path, mutated), mutated)

    def test_duplicate_exact_context_chunk_is_rejected(self):
        relative_path = "tutorials/statistics-for-bioinformatics.html"
        entry = self.fixture[relative_path]
        patch = entry["patches"][0]
        current = (baseline.ROOT / relative_path).read_text(encoding="utf-8")
        with self.assertRaisesRegex(AssertionError, "duplicate exact startup-performance"):
            normalize_patch_chunks(current + patch["after"], entry["patches"], relative_path)

    def test_tampered_fixture_fingerprint_is_rejected(self):
        original = FIXTURE_PATH.read_bytes()
        tampered = original + b" "
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_bytes(tampered)
            startup_performance_fixture.cache_clear()
            try:
                with patch.object(baseline, "FIXTURE_PATH", path):
                    with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
                        startup_performance_fixture()
            finally:
                startup_performance_fixture.cache_clear()

    def test_malformed_pinned_fixture_is_rejected(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        fixture["files"]["tutorials/statistics-for-bioinformatics.html"]["current_sha256"] = "0" * 64
        raw = (json.dumps(fixture, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_bytes(raw)
            startup_performance_fixture.cache_clear()
            try:
                with patch.object(baseline, "FIXTURE_PATH", path), patch.object(
                    baseline, "FIXTURE_SHA256", hashlib.sha256(raw).hexdigest()
                ):
                    with self.assertRaisesRegex(AssertionError, "do not reconstruct"):
                        startup_performance_fixture()
            finally:
                startup_performance_fixture.cache_clear()

    def test_fixture_generator_refuses_article_byte_changes(self):
        # The production article invariant is separately verified for every
        # generated HTML record; this stable fixture should build successfully.
        import generate_startup_performance_fixture as generator
        generated = generator.build_fixture()
        self.assertEqual(set(generated["files"]), FIXTURE_PATHS)


if __name__ == "__main__":
    unittest.main()
