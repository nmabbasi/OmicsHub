"""Regression checks for the exact historical adapter used by PR #36 tests."""
import unittest

from core_tutorial_corrections_baseline import (
    CORE_TUTORIAL_CORRECTION_PATHS,
    PR36_BASE_COMMIT,
    PR36_SOURCE_COMMIT,
    _git_blob,
    normalize_core_tutorial_corrections,
)


class CoreTutorialCorrectionsBaselineTests(unittest.TestCase):
    def test_only_exact_pr36_files_restore_to_parent_main(self):
        self.assertEqual(CORE_TUTORIAL_CORRECTION_PATHS, {
            "tutorials/ai-prompt-engineering-seurat.html",
            "tutorials/biological-data-formats.html",
            "tutorials/deterministic-retrieval-gget-ai.html",
            "tutorials/metagenomics-kraken2-bracken.html",
            "tutorials/scrna-seq-trajectory-inference.html",
            "tools/tutorial-code-groups.json",
            "tools/tutorial-code-languages.json",
            "tutorial-code-data.js",
        })
        for relative_path in sorted(CORE_TUTORIAL_CORRECTION_PATHS):
            with self.subTest(path=relative_path):
                source = _git_blob(PR36_SOURCE_COMMIT, relative_path)
                baseline = _git_blob(PR36_BASE_COMMIT, relative_path)
                self.assertNotEqual(source, baseline)
                self.assertEqual(
                    normalize_core_tutorial_corrections(relative_path, source),
                    baseline,
                )
                mutated = source + b"\n"
                self.assertEqual(
                    normalize_core_tutorial_corrections(relative_path, mutated),
                    mutated,
                    "unknown bytes must remain visible to existing scope guards",
                )
                self.assertEqual(
                    normalize_core_tutorial_corrections(relative_path, baseline),
                    baseline,
                )
        unlisted = "tutorials/infercnv-copy-number-variation.html"
        source = _git_blob(PR36_SOURCE_COMMIT, "tutorials/scrna-seq-trajectory-inference.html")
        self.assertEqual(normalize_core_tutorial_corrections(unlisted, source), source)


if __name__ == "__main__":
    unittest.main()
