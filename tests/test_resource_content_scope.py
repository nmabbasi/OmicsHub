"""Mutation tests for the PR15-pinned resource-dependent content allowance."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from resource_content_baseline import (
    ARTICLE,
    MANIFEST_PATH,
    PUBLISHED_BASELINE,
    ROOT,
    allowed_paths,
    load_manifest,
    normalize_resource_content,
    normalize_resource_sitemap,
    published_bytes,
    restore_page_to_pr15,
    restore_sitemap_to_pr15,
    restore_whitelisted_metadata,
)


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class ResourceContentScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (
            b'<html><head><script type="application/ld+json">'
            b'{"dateModified": "2026-10-21"}</script></head><body>'
            b'<article id="lesson"><p>Published lesson text.</p>'
            b'<pre><code>python\nprint("stable")\n</code></pre></article>'
            b'<nav aria-label="Learning path navigation">Same nav</nav>'
            b'<p>Updated 21 October 2026</p></body></html>'
        )
        cls.approved_body = (
            b'<p>Reviewed lesson text.</p>'
            b'<pre><code>python\nprint("stable")\n</code></pre>'
        )
        cls.approved = (
            b'<html><head><script type="application/ld+json">'
            b'{"dateModified": "2026-10-24"}</script></head><body>'
            b'<article id="lesson">' + cls.approved_body + b'</article>'
            b'<nav aria-label="Learning path navigation">Same nav</nav>'
            b'<p>Updated 24 October 2026</p></body></html>'
        )
        cls.entry = {
            "article_body_sha256": hashlib.sha256(cls.approved_body).hexdigest(),
            "date_modified_original": "2026-10-21",
            "date_modified_approved": "2026-10-24",
            "visible_updated_original": "21 October 2026",
            "visible_updated_approved": "24 October 2026",
            "sitemap_lastmod_original": "2026-10-21",
            "sitemap_lastmod_approved": "2026-10-24",
        }
        cls.path = "tutorials/synthetic-resource-content.html"

    def assert_restores_exactly(self, changed, entry=None):
        entry = entry or self.entry
        restored = restore_page_to_pr15(self.path, changed, entry, self.original)
        self.assertEqual(restored, self.original)

    def test_manifest_allowlist_is_explicit_and_pinned_to_exact_pr15(self):
        manifest = load_manifest()
        self.assertEqual(manifest["baseline_commit"], PUBLISHED_BASELINE)
        self.assertEqual(PUBLISHED_BASELINE, "5846304f76551252b97ca674f6020d2983901fca")
        self.assertEqual(set(manifest["allowed_paths"]), set(manifest["articles"]))
        self.assertEqual(allowed_paths(), frozenset(manifest["allowed_paths"]))
        resolved = subprocess.check_output(
            ["git", "rev-parse", PUBLISHED_BASELINE], cwd=ROOT, text=True
        ).strip()
        self.assertEqual(resolved, PUBLISHED_BASELINE)

    def test_allowlist_cannot_expand_beyond_the_reviewed_eighteen_pages(self):
        self.assertEqual(allowed_paths(), frozenset({
            "tutorials/ai-bioinformatics-github-copilot.html",
            "tutorials/ai-coding-cursor-aider.html",
            "tutorials/ai-prompt-engineering-seurat.html",
            "tutorials/cell-cell-communication.html",
            "tutorials/docker-singularity-bioinformatics.html",
            "tutorials/evolutionary-phylogeny-analysis.html",
            "tutorials/hpc-connection.html",
            "tutorials/hpc-submission-part1.html",
            "tutorials/hpc-support.html",
            "tutorials/mcp-zotero.html",
            "tutorials/metagenomics-assembly-mapping.html",
            "tutorials/notebooklm-research-brain.html",
            "tutorials/protein-structure-design-alphafold.html",
            "tutorials/scrna-seq-downstream-analysis.html",
            "tutorials/scrna-seq-quality-control.html",
            "tutorials/single-cell-deconvolution.html",
            "tutorials/tcr-bcr-repertoire-analysis.html",
            "tutorials/wes-variant-calling-pipeline.html",
        }))

    def test_registered_final_pages_restore_exactly_and_idempotently(self):
        for relative in allowed_paths():
            with self.subTest(page=relative):
                original = published_bytes(relative)
                restored = normalize_resource_content(relative, (ROOT / relative).read_bytes())
                self.assertEqual(restored, original)
                self.assertEqual(normalize_resource_content(relative, restored), original)

    def test_nonempty_manifest_accepts_realistic_visible_updated_date_labels(self):
        manifest = {
            "schema_version": 1,
            "baseline_commit": PUBLISHED_BASELINE,
            "allowed_paths": [self.path],
            "articles": {
                self.path: {
                    "article_body_sha256": "a" * 64,
                    "date_modified_original": "2026-10-21",
                    "date_modified_approved": "2026-10-24",
                    "visible_updated_original": "21 October 2026",
                    "visible_updated_approved": "24 October 2026",
                    "sitemap_lastmod_original": "2026-10-21",
                    "sitemap_lastmod_approved": "2026-10-24",
                }
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch("resource_content_baseline.MANIFEST_PATH", path):
                self.assertEqual(load_manifest(), manifest)
                manifest["articles"][self.path]["visible_updated_approved"] = "31 February 2026"
                path.write_text(json.dumps(manifest), encoding="utf-8")
                with self.assertRaisesRegex(AssertionError, "visible updated"):
                    load_manifest()

    def test_exact_approved_body_and_exact_date_pairs_restore_to_pr15(self):
        self.assertEqual(len(ARTICLE.findall(self.approved)), 1)
        self.assert_restores_exactly(self.approved)
        self.assert_restores_exactly(self.original)

    def test_unknown_body_mutation_is_rejected_by_complete_body_fingerprint(self):
        changed = self.approved.replace(b"Reviewed lesson text", b"Unregistered lesson text", 1)
        with self.assertRaisesRegex(AssertionError, "article-body edit"):
            self.assert_restores_exactly(changed)

    def test_wrapper_navigation_and_outside_page_mutations_remain_visible(self):
        mutations = (
            self.approved.replace(b'<article id="lesson">', b'<article id="changed">', 1),
            self.approved.replace(b'</article>', b'</article extra>', 1),
            self.approved.replace(
                b'aria-label="Learning path navigation"',
                b'aria-label="Changed navigation"', 1,
            ),
            self.approved.replace(b"Same nav", b"Changed nav", 1),
            self.approved.replace(b"<head>", b"<head><!-- changed --", 1),
        )
        for changed in mutations:
            with self.subTest(mutation=changed[:100]):
                try:
                    restored = restore_page_to_pr15(self.path, changed, self.entry, self.original)
                except AssertionError:
                    continue
                self.assertNotEqual(restored, self.original)

    def test_pre_code_blocks_are_protected_even_when_other_prose_is_approved(self):
        changed = self.approved.replace(b'print("stable")', b'print("mutated")', 1)
        with self.assertRaisesRegex(AssertionError, "<pre><code>"):
            self.assert_restores_exactly(changed)

    def test_article_fingerprint_cannot_hide_an_executable_script(self):
        changed = self.approved.replace(
            b'</article>', b'<script>unexpected();</script></article>', 1,
        )
        entry = dict(self.entry)
        entry['article_body_sha256'] = hashlib.sha256(
            ARTICLE.search(changed).group('body')
        ).hexdigest()
        with self.assertRaisesRegex(AssertionError, 'executable-script mutation'):
            self.assert_restores_exactly(changed, entry)

    def test_metadata_restores_only_fixed_path_field_and_exact_snippet_pairs(self):
        path = "tutorials/ai-prompt-engineering-seurat.html"
        original = b'<meta content="Published wording" name="description"/>'
        approved = b'<meta content="Reviewed wording" name="description"/>'
        entry = {"outside_metadata": {
            "description_meta": {
                "original": 'content="Published wording"',
                "approved": 'content="Reviewed wording"',
            }
        }}
        self.assertEqual(
            restore_whitelisted_metadata(path, approved, entry, original), original
        )

        with self.assertRaisesRegex(AssertionError, "not authorized"):
            restore_whitelisted_metadata(
                "tutorials/not-allowlisted.html", approved, entry, original
            )
        with self.assertRaisesRegex(AssertionError, "not authorized"):
            restore_whitelisted_metadata(
                path, approved,
                {"outside_metadata": {"arbitrary_field": {
                    "original": "x", "approved": "y",
                }}}, original,
            )
        with self.assertRaisesRegex(AssertionError, "unapproved metadata snippet"):
            restore_whitelisted_metadata(
                path, b'<meta content="Unregistered wording" name="description"/>',
                entry, original,
            )

    def test_unknown_date_modified_and_visible_updated_values_are_rejected(self):
        changed_modified = self.approved.replace(b"2026-10-24", b"2026-10-25", 1)
        with self.assertRaisesRegex(AssertionError, "dateModified"):
            self.assert_restores_exactly(changed_modified)
        changed_visible = self.approved.replace(b"24 October 2026", b"25 October 2026", 1)
        with self.assertRaisesRegex(AssertionError, "visible Updated"):
            self.assert_restores_exactly(changed_visible)

    def test_unlisted_path_cannot_use_a_registered_entry(self):
        changed = self.approved.replace(b"Reviewed lesson text", b"Unregistered lesson text", 1)
        result = normalize_resource_content("tutorials/not-allowlisted.html", changed)
        self.assertEqual(result, changed)
        self.assertNotEqual(result, self.original)

    def test_sitemap_restores_only_explicit_article_lastmod(self):
        original = (
            b"<url><loc>https://theomicshub.com/tutorials/synthetic-resource-content.html</loc>"
            b"<lastmod>2026-10-21</lastmod></url>\n"
            b"<url><loc>https://theomicshub.com/tutorials/other.html</loc>"
            b"<lastmod>2026-10-21</lastmod></url>\n"
        )
        approved = original.replace(b"<lastmod>2026-10-21</lastmod>",
                                   b"<lastmod>2026-10-24</lastmod>", 1)
        entries = {self.path: self.entry}
        self.assertEqual(restore_sitemap_to_pr15(approved, [self.path], entries), original)
        unknown = approved.replace(b"2026-10-24", b"2026-10-25", 1)
        with self.assertRaisesRegex(AssertionError, "unapproved sitemap lastmod"):
            restore_sitemap_to_pr15(unknown, [self.path], entries)
        unrelated = approved.replace(b"other.html", b"changed.html", 1)
        self.assertNotEqual(restore_sitemap_to_pr15(unrelated, [self.path], entries), original)
        with patch("resource_content_baseline.load_manifest", return_value={
            "allowed_paths": [self.path], "articles": entries,
        }):
            self.assertEqual(normalize_resource_sitemap(original), original)

    def test_sitemap_unlisted_lastmod_change_is_not_normalized(self):
        original = (
            b"<url><loc>https://theomicshub.com/tutorials/other.html</loc>"
            b"<lastmod>2026-10-21</lastmod></url>\n"
        )
        changed = original.replace(b"2026-10-21", b"2026-10-24")
        with patch("resource_content_baseline.load_manifest", return_value={
            "allowed_paths": [], "articles": {},
        }):
            self.assertEqual(normalize_resource_sitemap(changed), changed)
            self.assertNotEqual(normalize_resource_sitemap(changed), original)


if __name__ == "__main__":
    unittest.main()
