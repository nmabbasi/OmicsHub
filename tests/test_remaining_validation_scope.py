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
from advanced_validation_baseline import (
    allowed_asset_paths as advanced_asset_paths,
    allowed_article_paths as advanced_validation_paths,
    is_approved_workflow,
    normalize_advanced_validation_asset,
    normalize_advanced_validation_if_allowed,
    published_bytes as advanced_published_bytes,
)
from resource_content_baseline import (
    allowed_paths as resource_content_paths,
    normalize_resource_content,
    normalize_resource_sitemap,
)
from home_catalogue_baseline import HOME_CATALOGUE_ASSET_PATHS, normalize_home_catalogue
from tutorial_ui_baseline import (
    TUTORIAL_UI_PATHS,
    normalize_tutorial_ui,
    verify_tutorial_ui_file,
)
from start_here_baseline import (
    START_HERE_ASSET_PATHS,
    normalize_start_here,
    normalize_start_here_asset,
    pre_review_bytes,
)
from tutorial_execution_baseline import (
    new_execution_asset_paths,
    verify_new_execution_asset,
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
            original = normalize_tutorial_ui(
                relative, published_bytes(relative).decode("utf-8")
            ).encode("utf-8")
            self.assertTrue(current_path.is_file(), relative)
            current = current_path.read_bytes()
            current = normalize_resource_content(relative, current)
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
        resource_paths = set(resource_content_paths())
        for relative in changed_paths():
            if relative.startswith("tests/"):
                continue
            current_path = ROOT / relative
            if relative in new_execution_asset_paths():
                self.assertTrue(current_path.is_file(), relative)
                verify_new_execution_asset(relative, current_path.read_bytes())
                continue
            if relative in TUTORIAL_UI_PATHS | HOME_CATALOGUE_ASSET_PATHS:
                self.assertTrue(current_path.is_file(), relative)
                verify_tutorial_ui_file(relative, current_path.read_bytes())
                continue
            if relative in START_HERE_ASSET_PATHS:
                self.assertTrue(current_path.is_file(), relative)
                restored = normalize_start_here_asset(relative, current_path.read_bytes())
                if relative == "start-here.js":
                    self.assertIsNone(restored, "new JS is allowed only after its full hash verifies")
                else:
                    self.assertEqual(restored, pre_review_bytes(relative))
                continue
            if current_path.is_file() and is_approved_workflow(relative, current_path.read_bytes()):
                continue
            original = None
            result = subprocess.run(
                ["git", "show", f"{PUBLISHED_BASELINE}:{relative}"],
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
            )
            if result.returncode == 0:
                original = result.stdout
                original = normalize_home_catalogue(relative, original.decode("utf-8")).encode("utf-8")
                if relative == "start-here.html":
                    original = normalize_start_here(relative, original.decode("utf-8")).encode("utf-8")
                if relative.startswith("tutorials/") and relative.endswith(".html"):
                    original = normalize_tutorial_ui(
                        relative, original.decode("utf-8")
                    ).encode("utf-8")
            with self.subTest(path=relative):
                self.assertIsNotNone(original, "new public files and assets are forbidden")
                self.assertTrue(current_path.is_file(), "published public files may not be deleted")
                current = normalize_home_catalogue(
                    relative, current_path.read_bytes().decode("utf-8")
                ).encode("utf-8")
                if relative == "start-here.html":
                    current = normalize_start_here(relative, current.decode("utf-8")).encode("utf-8")
                current = normalize_resource_content(relative, current)
                if not (
                    relative in manifest_paths or relative in resource_paths
                    or relative in advanced_validation_paths()
                    or relative in advanced_asset_paths()
                    or relative == "sitemap.xml"
                ):
                    self.assertEqual(
                        current, original,
                        "unlisted public changes must disappear under exact UI normalization",
                    )
                    continue
                if relative in manifest_paths:
                    current = normalize_remaining_validation_edit(
                        relative, current.decode("utf-8")
                    ).encode("utf-8")
                elif relative == "sitemap.xml":
                    current = normalize_remaining_validation_sitemap(
                        normalize_resource_sitemap(current)
                    )
                elif relative in advanced_validation_paths():
                    current = normalize_advanced_validation_if_allowed(
                        relative, current.decode("utf-8")
                    ).encode("utf-8")
                    self.assertEqual(
                        current, advanced_published_bytes(relative),
                        "only the exact manifest-pinned PR14 article edit may differ",
                    )
                    continue
                elif relative in advanced_asset_paths():
                    current = normalize_advanced_validation_asset(relative, current)
                self.assertEqual(current, original,
                                 "every changed public file must equal pinned main after exact restoration")

    def test_unknown_body_or_date_changes_are_not_restored(self):
        relative = QC_PATH
        current = (ROOT / relative).read_text(encoding="utf-8")
        body_mutation = current.replace("</article>", "<p>unapproved text</p></article>", 1)
        with self.assertRaisesRegex(AssertionError, "article-body edit"):
            normalize_remaining_validation_edit(relative, body_mutation)

        unknown_date = re.sub(
            r'("dateModified"\s*:\s*")[^"]+(")',
            r'\g<1>2030-01-01\2', current, count=1,
        )
        self.assertNotEqual(unknown_date, current, "the negative fixture must actually change the current date")
        with self.assertRaisesRegex(AssertionError, "unapproved dateModified|unregistered or stale article-body edit"):
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
                self.assertNotEqual(mutation, current, "the negative fixture must actually change source")
                try:
                    restored = normalize_remaining_validation_edit(relative, mutation)
                except AssertionError as error:
                    # Altering a literal R-first chunk's neighboring wrapper can
                    # prevent its exact restoration. Rejecting that source is
                    # stricter than returning it for whole-file comparison.
                    self.assertRegex(str(error), r"unapproved dateModified|article-body edit")
                else:
                    self.assertNotEqual(restored, original)

    def test_sitemap_restorer_changes_only_manifest_allowlisted_lastmods(self):
        original = published_bytes("sitemap.xml")
        current = normalize_resource_sitemap((ROOT / "sitemap.xml").read_bytes())
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
