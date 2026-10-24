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
    allowed_article_paths,
    is_approved_workflow,
    load_manifest,
    workflow_bytes_match,
)


class AdvancedValidationScopeTests(unittest.TestCase):
    def test_manifest_pins_pr14_exact_workflow_path_and_starts_with_no_articles(self):
        manifest = load_manifest()
        self.assertEqual(manifest["baseline_commit"], PUBLISHED_BASELINE)
        self.assertEqual(manifest["workflow"]["path"], WORKFLOW_PATH)
        self.assertEqual(allowed_article_paths(), frozenset())
        self.assertEqual(manifest["articles"], {})
        self.assertEqual(manifest["allowed_article_paths"], [])
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
