"""Strict scope checks for the remaining tutorial validation revisions."""
import hashlib
import re
import subprocess
import unittest

from remaining_validation_baseline import (
    ARTICLE,
    PUBLISHED_BASELINE,
    ROOT,
    allowed_paths,
    load_manifest,
    normalize_remaining_validation_edit,
    normalize_remaining_validation_sitemap,
    published_bytes,
)

QC_PATH = "tutorials/quality-control-fundamentals.html"
REVISED_TUTORIALS = frozenset({
    QC_PATH,
    "tutorials/cite-seq-wnn-multiomics.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/data-visualization-fundamentals.html",
    "tutorials/reference-genomes-annotation.html",
})


def changed_paths():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "--no-renames", PUBLISHED_BASELINE, "--"],
        cwd=ROOT, text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT, text=True,
    ).splitlines()
    return sorted(set(tracked) | set(untracked))


class RemainingValidationScopeTests(unittest.TestCase):
    def test_manifest_has_full_baseline_pin_and_explicit_tutorial_allowlist(self):
        manifest = load_manifest()
        self.assertEqual(manifest["baseline_commit"], PUBLISHED_BASELINE)
        self.assertEqual(allowed_paths(), REVISED_TUTORIALS)
        self.assertTrue(allowed_paths())
        self.assertTrue(all(path.startswith("tutorials/") and path.endswith(".html")
                            for path in allowed_paths()))
        self.assertEqual(set(manifest["files"]), set(allowed_paths()))

    def test_allowlisted_page_equals_pinned_source_plus_only_exact_body_and_dates(self):
        for relative in sorted(allowed_paths()):
            current_path = ROOT / relative
            original = published_bytes(relative)
            self.assertTrue(current_path.is_file(), relative)
            current = current_path.read_bytes()
            original_articles = list(ARTICLE.finditer(original))
            current_articles = list(ARTICLE.finditer(current))
            with self.subTest(path=relative):
                self.assertEqual(len(original_articles), 1)
                self.assertEqual(len(current_articles), 1)
                # These explicit assertions make wrapper changes visible even
                # before the normalized whole-page equality below.
                self.assertEqual(current_articles[0].group("open"), original_articles[0].group("open"))
                self.assertEqual(current_articles[0].group("close"), original_articles[0].group("close"))
                self.assertEqual(
                    normalize_remaining_validation_edit(relative, current.decode("utf-8")).encode("utf-8"),
                    original,
                    "only the manifest-pinned inner article body and exact date deltas may differ",
                )

    def test_all_changed_public_paths_are_allowlisted_and_exact_after_restoration(self):
        manifest_paths = set(allowed_paths())
        for relative in changed_paths():
            if relative.startswith("tests/"):
                continue
            current_path = ROOT / relative
            original = None
            result = subprocess.run(
                ["git", "show", f"{PUBLISHED_BASELINE}:{relative}"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            )
            if result.returncode == 0:
                original = result.stdout
            with self.subTest(path=relative):
                self.assertTrue(
                    relative in manifest_paths or relative == "sitemap.xml",
                    "public changes outside the explicit article/date allowlist are forbidden",
                )
                self.assertIsNotNone(original, "new public files and assets are forbidden")
                self.assertTrue(current_path.is_file(), "published public files may not be deleted")
                current = current_path.read_bytes()
                if relative in manifest_paths:
                    current = normalize_remaining_validation_edit(
                        relative, current.decode("utf-8")
                    ).encode("utf-8")
                elif relative == "sitemap.xml":
                    current = normalize_remaining_validation_sitemap(current)
                self.assertEqual(current, original,
                                 "every changed public file must equal pinned main after exact restoration")

    def test_unknown_body_or_date_changes_are_not_restored(self):
        relative = QC_PATH
        current = (ROOT / relative).read_text(encoding="utf-8")
        body_mutation = current.replace("</article>", "<p>unapproved text</p></article>", 1)
        with self.assertRaisesRegex(AssertionError, "article-body edit"):
            normalize_remaining_validation_edit(relative, body_mutation)

        manifest = load_manifest()["files"][relative]
        unknown_date = current.replace(
            f'"dateModified": "{manifest["date_modified_approved"]}"',
            '"dateModified": "2026-10-25"', 1,
        )
        with self.assertRaisesRegex(AssertionError, "unapproved dateModified"):
            normalize_remaining_validation_edit(relative, unknown_date)

    def test_normalization_keeps_wrapper_navigation_and_other_metadata_visible(self):
        relative = QC_PATH
        original = published_bytes(relative).decode("utf-8")
        current = (ROOT / relative).read_text(encoding="utf-8")
        baseline = normalize_remaining_validation_edit(relative, current)
        self.assertEqual(baseline, original)
        mutations = (
            current.replace('aria-labelledby="tutorial-title"',
                            'aria-labelledby="unexpected-title"', 1),
            current.replace('aria-label="Learning path navigation"',
                            'aria-label="Unexpected navigation"', 1),
            current.replace('"datePublished": "2026-09-19"',
                            '"datePublished": "2026-09-20"', 1),
        )
        for mutation in mutations:
            with self.subTest(change=mutation[:80]):
                restored = normalize_remaining_validation_edit(relative, mutation)
                self.assertNotEqual(restored, original)

    def test_sitemap_restorer_changes_only_manifest_allowlisted_lastmods(self):
        original = published_bytes("sitemap.xml")
        current = (ROOT / "sitemap.xml").read_bytes()
        self.assertEqual(normalize_remaining_validation_sitemap(current), original)
        target_url = b"https://theomicshub.com/tutorials/quality-control-fundamentals.html"
        row = re.search(rb"<url>\s*<loc>" + re.escape(target_url) + rb"</loc>.*?</url>", current, re.S)
        self.assertIsNotNone(row)
        row_bytes = row.group(0)
        approved = load_manifest()["files"][QC_PATH]["sitemap_lastmod_approved"].encode("ascii")
        mutated_row = row_bytes.replace(
            b"<lastmod>" + approved + b"</lastmod>", b"<lastmod>2026-10-25</lastmod>", 1
        )
        mutated = current[:row.start()] + mutated_row + current[row.end():]
        # Unknown dates are not normalized away; reject them before the full-file
        # scope assertion can compare the normalized sitemap with the pin.
        with self.assertRaisesRegex(AssertionError, "unapproved sitemap lastmod"):
            normalize_remaining_validation_sitemap(mutated)

    def test_baseline_commit_resolves_to_the_pinned_full_sha(self):
        resolved = subprocess.check_output(
            ["git", "rev-parse", PUBLISHED_BASELINE], cwd=ROOT, text=True,
        ).strip()
        self.assertEqual(resolved, "f218d1b6c711a5a50fff8c8af67f2b3d9bf7201c")


if __name__ == "__main__":
    unittest.main()
