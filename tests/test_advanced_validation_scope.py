"""Exact scope tests for the advanced tutorial-platform CI addition."""
import hashlib
import re
import subprocess
import unittest

from advanced_validation_baseline import (
    MANIFEST_PATH,
    PUBLISHED_BASELINE,
    ROOT,
    WORKFLOW_PATH,
    WORKFLOW_SHA256_PLACEHOLDER,
    ASSET_PATH,
    advanced_asset_bytes_match,
    _restore_registered_page,
    _restore_registered_sitemap,
    allowed_article_paths,
    is_approved_workflow,
    load_manifest,
    workflow_bytes_match,
)


class AdvancedValidationScopeTests(unittest.TestCase):
    def test_article_normalizer_restores_only_manifest_pinned_fields(self):
        relative = "tutorials/phylogenomics-orthofinder.html"
        original = (
            b'<html><head>{"dateModified": "2026-10-21"}</head><body>'
            b'<article id="lesson"><p>published text</p></article>'
            b'<nav aria-label="Learning path navigation">Old neighbor</nav>'
            b'<p>Updated 21 October 2026</p>'
            b'<p class="text-sm text-gray-600 mb-2">No run claimed.</p></body></html>'
        )
        approved_body = b'<p>corrected text</p>'
        entry = {
            "article_body_sha256": hashlib.sha256(approved_body).hexdigest(),
            "date_modified_original": "2026-10-21",
            "date_modified_approved": "2026-10-24",
            "visible_updated_original": "21 October 2026",
            "visible_updated_approved": "24 October 2026",
            "outside_disclosure": {
                "original": '<p class="text-sm text-gray-600 mb-2">No run claimed.</p>',
                "approved": '<p class="text-sm text-gray-600 mb-2">A bounded run completed.</p>',
            },
        }
        current = (
            b'<html><head>{"dateModified": "2026-10-24"}</head><body>'
            b'<article id="lesson">' + approved_body + b'</article>'
            b'<nav aria-label="Learning path navigation">Old neighbor</nav>'
            b'<p>Updated 24 October 2026</p>'
            b'<p class="text-sm text-gray-600 mb-2">A bounded run completed.</p></body></html>'
        )
        self.assertEqual(_restore_registered_page(relative, current, entry, original), original)
        self.assertEqual(_restore_registered_page(
            "tutorials/spatial-transcriptomics-r-python.html", current, entry, original
        ), original)
        with self.assertRaisesRegex(AssertionError, "invalid outside-article disclosure entry"):
            _restore_registered_page("tutorials/advanced-ai-single-cell.html", current, entry, original)

        unapproved_body = current.replace(b"corrected text", b"unregistered text")
        with self.assertRaisesRegex(AssertionError, "article-body edit"):
            _restore_registered_page(relative, unapproved_body, entry, original)
        unknown_date = current.replace(b"2026-10-24", b"2026-10-25", 1)
        with self.assertRaisesRegex(AssertionError, "unapproved dateModified"):
            _restore_registered_page(relative, unknown_date, entry, original)
        unknown_visible_date = current.replace(b"24 October 2026", b"25 October 2026")
        with self.assertRaisesRegex(AssertionError, "unapproved visible Updated date"):
            _restore_registered_page(relative, unknown_visible_date, entry, original)

        for mutation in (
            current.replace(b'<article id="lesson">', b'<article id="changed">', 1),
            current.replace(b'aria-label="Learning path navigation"',
                            b'aria-label="Unexpected navigation"', 1),
        ):
            with self.subTest(mutation=mutation[:100]):
                self.assertNotEqual(_restore_registered_page(relative, mutation, entry, original), original)
        unknown_disclosure = current.replace(b"A bounded run completed.", b"Unknown wording.")
        with self.assertRaisesRegex(AssertionError, "outside-article disclosure"):
            _restore_registered_page(relative, unknown_disclosure, entry, original)

    def test_embedded_visible_date_remains_part_of_exact_article_hash(self):
        relative = "tutorials/infercnv-copy-number-variation.html"
        original_body = b'<span>Updated 21 October 2026</span><p>published</p>'
        approved_body = b'<span>Updated 24 October 2026</span><p>checked</p>'
        prefix = b'<html><head>{"dateModified": "2026-10-21"}</head><body><article>'
        suffix = b'</article><nav>Unchanged</nav></body></html>'
        original = prefix + original_body + suffix
        current = prefix.replace(b"2026-10-21", b"2026-10-24") + approved_body + suffix
        entry = {
            "article_body_sha256": hashlib.sha256(approved_body).hexdigest(),
            "date_modified_original": "2026-10-21",
            "date_modified_approved": "2026-10-24",
            "visible_updated_original": "21 October 2026",
            "visible_updated_approved": "24 October 2026",
        }
        self.assertEqual(_restore_registered_page(relative, current, entry, original), original)
        self.assertEqual(_restore_registered_page(relative, original, entry, original), original)
        with self.assertRaisesRegex(AssertionError, "article-body edit"):
            _restore_registered_page(
                relative, current.replace(b"24 October 2026", b"25 October 2026"), entry, original
            )
        wrapper_change = current.replace(b'<nav>Unchanged', b'<nav>Unauthorized')
        self.assertNotEqual(_restore_registered_page(relative, wrapper_change, entry, original), original)

    def test_sitemap_normalizer_restores_only_explicit_article_lastmods(self):
        path = "tutorials/synthetic-validation.html"
        url = "https://theomicshub.com/" + path
        original = (f"<url><loc>{url}</loc><lastmod>2026-10-21</lastmod></url>\n"
                    "<url><loc>https://theomicshub.com/other.html</loc>"
                    "<lastmod>2026-10-21</lastmod></url>\n").encode()
        approved = original.replace(b"2026-10-21", b"2026-10-24", 1)
        entries = {path: {"sitemap_lastmod_original": "2026-10-21",
                          "sitemap_lastmod_approved": "2026-10-24"}}
        self.assertEqual(_restore_registered_sitemap(approved, [path], entries), original)
        mutated = approved.replace(b"2026-10-24", b"2026-10-25", 1)
        with self.assertRaisesRegex(AssertionError, "unapproved sitemap lastmod"):
            _restore_registered_sitemap(mutated, [path], entries)

    def test_manifest_pins_pr14_workflow_and_explicit_article_entries(self):
        manifest = load_manifest()
        self.assertEqual(manifest["baseline_commit"], PUBLISHED_BASELINE)
        self.assertEqual(manifest["workflow"]["path"], WORKFLOW_PATH)
        self.assertEqual(set(manifest["articles"]), set(allowed_article_paths()))
        self.assertEqual(set(allowed_article_paths()), {
            "tutorials/advanced-ai-single-cell.html",
            "tutorials/infercnv-copy-number-variation.html",
            "tutorials/phylogenomics-orthofinder.html",
            "tutorials/transcriptomics-differential-expression.html",
            "tutorials/spatial-transcriptomics-r-python.html",
        })
        self.assertTrue(all(path.startswith("tutorials/") and path.endswith(".html")
                            for path in allowed_article_paths()))
        for entry in manifest["articles"].values():
            self.assertRegex(entry["article_body_sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("date_modified_original", entry)
            self.assertIn("date_modified_approved", entry)
            self.assertIn("sitemap_lastmod_original", entry)
            self.assertIn("sitemap_lastmod_approved", entry)
        self.assertEqual(set(manifest.get("assets", {})), {ASSET_PATH})
        self.assertEqual(set(manifest.get("assets", {})),
                         set(manifest.get("allowed_asset_paths", [])))
        resolved = subprocess.check_output(
            ["git", "rev-parse", PUBLISHED_BASELINE], cwd=ROOT, text=True
        ).strip()
        self.assertEqual(resolved, "d581217c96a8100d42ab919e1e26816cdcf1a7bb")

    def test_hash_predicate_accepts_only_exact_path_and_exact_complete_bytes(self):
        content = b"name: reviewed test workflow\n"
        digest = hashlib.sha256(content).hexdigest()
        self.assertTrue(workflow_bytes_match(WORKFLOW_PATH, content, digest))
        self.assertFalse(workflow_bytes_match(
            WORKFLOW_PATH, content + b"# altered\n", digest
        ))
        self.assertFalse(workflow_bytes_match(
            ".github/workflows/other.yml", content, digest
        ))
        self.assertFalse(workflow_bytes_match(
            ".github/other.yml", content, digest
        ))
        self.assertFalse(workflow_bytes_match(
            WORKFLOW_PATH, content, "not-a-sha256"
        ))

    def test_asset_gate_accepts_only_exact_full_file_bytes_and_path(self):
        content = b"#!/usr/bin/env python3\nverified range reader\n"
        original = b"#!/usr/bin/env python3\nordinary reader\n"
        original_hash = hashlib.sha256(original).hexdigest()
        approved_hash = hashlib.sha256(content).hexdigest()
        self.assertTrue(advanced_asset_bytes_match(
            ASSET_PATH, content, original_hash, approved_hash
        ))
        self.assertFalse(advanced_asset_bytes_match(
            ASSET_PATH, content + b"# mutation\n", original_hash, approved_hash
        ))
        self.assertFalse(advanced_asset_bytes_match(
            "files/other/prepare_inputs.py", content, original_hash, approved_hash
        ))
        self.assertFalse(advanced_asset_bytes_match(
            ASSET_PATH, content, "bad-hash", approved_hash
        ))

    def test_only_reviewed_workflow_path_can_use_the_manifest_gate(self):
        manifest = load_manifest()
        fingerprint = manifest["workflow"]["sha256"]
        if re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            content = (ROOT / WORKFLOW_PATH).read_bytes()
            self.assertTrue(is_approved_workflow(WORKFLOW_PATH, content))
            self.assertFalse(is_approved_workflow(
                ".github/workflows/other.yml", content
            ))
            self.assertFalse(is_approved_workflow(
                "tutorials/platform-validation.html", content
            ))
        else:
            # The platform workflow is created by a separate owner. Until it
            # exists, only the explicit placeholder is acceptable; once it is
            # created the reviewed hash must be refreshed before scope passes.
            self.assertEqual(fingerprint, WORKFLOW_SHA256_PLACEHOLDER)
            self.assertFalse(is_approved_workflow(".github/workflows/other.yml", b""))
            self.assertFalse(is_approved_workflow("tutorials/a.html", b""))
            if (ROOT / WORKFLOW_PATH).exists():
                with self.assertRaisesRegex(AssertionError, "fingerprint not finalized"):
                    is_approved_workflow(WORKFLOW_PATH, (ROOT / WORKFLOW_PATH).read_bytes())
            self.assertIn("REFRESH_REQUIRED", MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_mutated_workflow_is_not_accepted_by_its_original_fingerprint(self):
        content = b"name: platform validation\non: pull_request\n"
        original_hash = hashlib.sha256(content).hexdigest()
        self.assertTrue(workflow_bytes_match(WORKFLOW_PATH, content, original_hash))
        self.assertFalse(workflow_bytes_match(
            WORKFLOW_PATH, content.replace(b"pull_request", b"push"), original_hash
        ))
        self.assertFalse(workflow_bytes_match(
            ".github/workflows/tutorial-platforms-extra.yml", content, original_hash
        ))

    def test_native_runner_workflow_has_no_paid_or_publishing_resources(self):
        content = (ROOT / WORKFLOW_PATH).read_text(encoding="utf-8")
        runner_labels = re.findall(r"^\s{10}- ([A-Za-z0-9.-]+)\s*$", content, re.M)
        self.assertEqual(set(runner_labels), {
            "ubuntu-latest", "windows-latest", "macos-latest",
        })
        self.assertEqual(len(runner_labels), 3)
        self.assertIn("runs-on: ${{ matrix.os }}", content)
        self.assertIn("contents: read", content)
        self.assertNotRegex(content, r"(?m)^\s*[^\s:]+:\s*write\s*$")
        self.assertNotIn("secrets.", content)
        self.assertNotIn("actions/cache", content)
        self.assertNotIn("upload-artifact", content)
        self.assertNotRegex(content, r"(?m)^\s*cache(?:-[^:]*)?:")
        limits = re.findall(r"timeout-minutes:\s*(\d+)", content)
        self.assertTrue(limits)
        self.assertLessEqual(max(map(int, limits)), 30)


if __name__ == "__main__":
    unittest.main()
