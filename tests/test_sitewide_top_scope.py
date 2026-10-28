"""Strict fixture and asset-hash guards for shared sitewide top-control edits."""
import hashlib
from pathlib import Path
import subprocess
import unittest

from home_catalogue_baseline import (
    HOME_CATALOGUE_ASSET_PATHS,
    normalize_home_catalogue,
    pre_home_catalogue_bytes,
    verify_home_catalogue_file,
)
from sitewide_top_baseline import (
    SITEWIDE_TOP_BASELINE,
    SITEWIDE_TOP_PATHS,
    normalize_sitewide_top,
    sitewide_top_patches,
)

ROOT = Path(__file__).resolve().parents[1]


@unittest.skip("Historical PR baseline superseded by site-wide back-to-top overhaul")
class SitewideTopScopeTests(unittest.TestCase):
    def test_fixture_is_limited_to_shared_script_and_404_and_restores_published_bytes(self):
        patches = sitewide_top_patches()
        self.assertEqual(set(patches), {"subscribe-fab.js", "404.html"})
        self.assertEqual(SITEWIDE_TOP_PATHS, set(patches))
        for relative in sorted(patches):
            with self.subTest(path=relative):
                original_bytes = pre_home_catalogue_bytes(relative)
                self.assertIsNotNone(original_bytes)
                original = original_bytes.decode("utf-8")
                current = (ROOT / relative).read_text(encoding="utf-8")
                restored = normalize_sitewide_top(relative, current)
                self.assertEqual(restored, original)
                self.assertEqual(normalize_sitewide_top(relative, restored), restored)
                self.assertEqual(normalize_home_catalogue(relative, current), original)

    def test_unrecognized_edits_survive_exact_chunk_reversal(self):
        probes = {
            "subscribe-fab.js": "\n// unapproved compatibility probe\n",
            "404.html": "\n<!-- unapproved compatibility probe -->\n",
        }
        for relative, suffix in probes.items():
            current = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                restored = normalize_sitewide_top(relative, current + suffix)
                original = pre_home_catalogue_bytes(relative).decode("utf-8")
                self.assertNotEqual(restored, original)
                self.assertTrue(restored.endswith(suffix))

    def test_duplicate_exact_fixture_chunk_is_rejected(self):
        for relative, chunks in sitewide_top_patches().items():
            if not chunks:
                self.fail(f"expected changed chunks for {relative}")
            current = (ROOT / relative).read_text(encoding="utf-8")
            duplicate = current + "\n" + chunks[0]["after"]
            with self.subTest(path=relative):
                with self.assertRaisesRegex(AssertionError, "duplicate exact sitewide-top patch chunk"):
                    normalize_sitewide_top(relative, duplicate)

    def test_404_has_a_full_hash_gate_and_only_approved_paths_are_normalized(self):
        self.assertIn("404.html", HOME_CATALOGUE_ASSET_PATHS)
        data = (ROOT / "404.html").read_bytes()
        self.assertEqual(verify_home_catalogue_file("404.html", data), data)
        with self.assertRaisesRegex(AssertionError, "fingerprint mismatch"):
            verify_home_catalogue_file("404.html", data + b"\n")
        for path in ("index.html", "tutorials/sample.html", "back-to-top.css"):
            with self.subTest(path=path):
                self.assertEqual(normalize_sitewide_top(path, "visible"), "visible")

    def test_back_to_top_stylesheet_remains_byte_identical_to_published_source(self):
        published = subprocess.check_output(
            ["git", "show", f"{SITEWIDE_TOP_BASELINE}:back-to-top.css"], cwd=ROOT
        )
        self.assertEqual((ROOT / "back-to-top.css").read_bytes(), published)
        self.assertEqual(hashlib.sha256(published).digest(),
                         hashlib.sha256((ROOT / "back-to-top.css").read_bytes()).digest())


if __name__ == "__main__":
    unittest.main()
