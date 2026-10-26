"""Strictness tests for the deployed-main editorial-review normalization layer."""
import hashlib
from pathlib import Path
import unittest

from editorial_review_baseline import (
    BASE_COMMIT, FIXTURE_PATH, FIXTURE_SHA256, PUBLIC_PATHS,
    editorial_review_fixture, normalize_editorial_review,
)

ROOT = Path(__file__).resolve().parents[1]


class EditorialReviewBaselineTests(unittest.TestCase):
    def test_fixture_is_pinned_closed_and_restores_every_public_path_exactly(self):
        self.assertEqual(BASE_COMMIT, "e846ce3fb6053ed611dc87fc62748865499913d0")
        self.assertEqual(set(editorial_review_fixture()), PUBLIC_PATHS)
        self.assertEqual(hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), FIXTURE_SHA256)
        for relative in sorted(PUBLIC_PATHS):
            with self.subTest(path=relative):
                entry = editorial_review_fixture()[relative]
                current = (ROOT / relative).read_text(encoding="utf-8")
                original = entry["base_bytes"].decode("utf-8")
                restored = normalize_editorial_review(relative, current)
                self.assertEqual(restored, original)
                self.assertEqual(normalize_editorial_review(relative, original), original)
                self.assertEqual(normalize_editorial_review(relative, restored), restored)

    def test_unknown_article_script_image_ad_and_url_mutations_remain_visible(self):
        relative = "tutorials/scrna-seq-trajectory-inference.html"
        current = (ROOT / relative).read_text(encoding="utf-8")
        mutations = {
            "article content": current.replace(
                "Use the method guidance above to assess assumptions",
                "UNAPPROVED content: use the method guidance above to assess assumptions",
                1,
            ),
            "inline script": current.replace(
                "function toggleMobileMenu()", "function unapprovedToggleMobileMenu()", 1,
            ),
            "image URL": current.replace(
                "trajectory-inference-workstation.webp",
                "unapproved-trajectory-image.webp", 1,
            ),
            "advertising URL": current.replace(
                "adsbygoogle.js?client=ca-",
                "adsbygoogle.js?client=unapproved-", 1,
            ),
            "canonical URL": current.replace(
                "https://theomicshub.com/tutorials/scrna-seq-trajectory-inference.html",
                "https://unapproved.invalid/tutorials/scrna-seq-trajectory-inference.html", 1,
            ),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, current, "mutation probe must change the source")
                normalized = normalize_editorial_review(relative, mutated)
                self.assertIn("unapproved", normalized.lower())
                self.assertNotEqual(
                    normalized,
                    editorial_review_fixture()[relative]["base_bytes"].decode("utf-8"),
                )

    def test_unknown_paths_are_never_normalized(self):
        text = "<script>unapproved()</script>"
        self.assertEqual(normalize_editorial_review("tutorials/not-approved.html", text), text)
        self.assertEqual(normalize_editorial_review("files/unknown.js", text), text)


if __name__ == "__main__":
    unittest.main()
