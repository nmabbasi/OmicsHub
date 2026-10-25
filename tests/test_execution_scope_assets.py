"""Scope checks for the exact SHA-pinned tutorial execution assets."""
from pathlib import Path
import unittest

from tutorial_execution_baseline import (
    new_execution_asset_paths,
    verify_new_execution_asset,
)

ROOT = Path(__file__).resolve().parents[1]
PINNED_EXECUTION_PNGS = {
    "images/tutorial-figures/quality-control-r-public-pbmc3k-violin.png",
    "images/tutorial-figures/research-reporting-r-synthetic-qc.png",
    "images/tutorial-figures/scrna-seq-basics-r-pbmc3k-elbow.png",
    "images/tutorial-figures/scrna-seq-basics-r-pbmc3k-qc.png",
    "images/tutorial-figures/scrna-seq-basics-r-pbmc3k-umap.png",
    "images/tutorial-figures/tidyverse-r-supplied-count-totals.png",
    "images/tutorial-figures/visualization-fundamentals-r-heatmap_topgenes.png",
    "images/tutorial-figures/visualization-fundamentals-r-pca_plot.png",
    "images/tutorial-figures/visualization-fundamentals-r-qc_boxplot.png",
    "images/tutorial-figures/visualization-fundamentals-r-qc_histogram.png",
    "images/tutorial-figures/visualization-fundamentals-r-umap_plot.png",
    "images/tutorial-figures/visualization-fundamentals-r-volcano.png",
}


class ExecutionScopeAssetTests(unittest.TestCase):
    def test_all_exact_new_execution_assets_verify(self):
        paths = new_execution_asset_paths()
        self.assertEqual(len(paths), 14)
        self.assertEqual(paths & PINNED_EXECUTION_PNGS, PINNED_EXECUTION_PNGS)
        for relative in sorted(paths):
            with self.subTest(path=relative):
                verify_new_execution_asset(relative, (ROOT / relative).read_bytes())

    def test_unknown_png_path_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "not an authorized new execution asset"):
            verify_new_execution_asset(
                "images/tutorial-figures/unreviewed-new.png",
                b"\x89PNG\r\n\x1a\nunknown",
            )

    def test_mutated_bytes_for_each_pinned_execution_png_are_rejected(self):
        paths = new_execution_asset_paths()
        self.assertTrue(PINNED_EXECUTION_PNGS <= paths)
        for relative in sorted(PINNED_EXECUTION_PNGS):
            raw = (ROOT / relative).read_bytes()
            mutated = raw[:-1] + bytes([raw[-1] ^ 1])
            with self.subTest(path=relative):
                with self.assertRaisesRegex(AssertionError, "execution asset fingerprint mismatch"):
                    verify_new_execution_asset(relative, mutated)


if __name__ == "__main__":
    unittest.main()
