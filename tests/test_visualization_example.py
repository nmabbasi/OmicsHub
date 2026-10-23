"""Lightweight integrity checks for the published synthetic visualization example."""
from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "files" / "visualization-example"
SCRIPT = EXAMPLE / "run_example.R"
FIGURES = ROOT / "images" / "tutorial-figures"
HTML = ROOT / "tutorials" / "advanced-visualization-packages.html"
EXPECTED_FIGURES = (
    "visualization-synthetic-umap.png",
    "visualization-synthetic-feature.png",
    "visualization-synthetic-dotplot.png",
    "visualization-synthetic-composition.png",
)


class VisualizationExampleTests(unittest.TestCase):
    def test_fixture_shape_and_metadata_contract(self):
        with (EXAMPLE / "synthetic_counts.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(len(rows), 37)  # header + 36 features
        self.assertEqual(len(rows[0]), 49)  # feature name + 48 cells
        self.assertEqual(len(set(rows[0][1:])), 48)
        self.assertTrue(all(len(row) == 49 for row in rows))
        self.assertTrue(all(int(value) >= 0 for row in rows[1:] for value in row[1:]))

        with (EXAMPLE / "synthetic_metadata.csv").open(newline="", encoding="utf-8") as handle:
            metadata = list(csv.DictReader(handle))
        self.assertEqual(len(metadata), 48)
        self.assertEqual([row["cell"] for row in metadata], rows[0][1:])
        self.assertTrue({"cell_type", "condition", "sample_id"}.issubset(metadata[0]))
        self.assertEqual({row["cell_type"] for row in metadata}, {"Type_A", "Type_B", "Type_C"})

    def test_script_provenance_and_core_plot_contract(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "SEED <- 20261023L",
            "CreateSeuratObject",
            "NormalizeData",
            "FindVariableFeatures",
            "ScaleData",
            "RunPCA",
            "RunUMAP",
            "DimPlot",
            "FeaturePlot",
            "DotPlot",
            "ggsave",
            "sessionInfo()",
            "synthetic_counts.csv",
            "synthetic_metadata.csv",
        ):
            self.assertIn(required, source)
        self.assertNotIn("library(SCpubr)", source)
        self.assertNotIn("library(dittoSeq)", source)

    def test_png_artifacts_are_nonempty_and_well_formed(self):
        for filename in EXPECTED_FIGURES:
            path = FIGURES / filename
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 1000, path)
            with path.open("rb") as image:
                header = image.read(24)
            self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", header[16:24])
            self.assertGreater(width, 300)
            self.assertGreater(height, 250)

    def test_provenance_versions_and_checksums_match_published_files(self):
        versions = (EXAMPLE / "package-versions.txt").read_text(encoding="utf-8")
        for version in ("R 4.3.3", "Seurat 5.0.1", "SeuratObject 5.0.1", "ggplot2 3.4.4", "uwot 0.1.16"):
            self.assertIn(version, versions)
        self.assertIn("R version 4.3.3", (EXAMPLE / "session-info.txt").read_text(encoding="utf-8"))
        checksums = (EXAMPLE / "run-checksums.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(checksums), 6)  # two CSV inputs and four PNGs
        for line in checksums:
            relative_name, expected = line.rsplit(" ", 1)
            self.assertFalse(Path(relative_name).is_absolute())
            path = ROOT / relative_name
            self.assertTrue(path.is_file(), path)
            actual = hashlib.md5(path.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, path)

    def test_tutorial_links_and_caveats_are_present(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("Optional wrapper templates (not executed in this revision)", html)
        self.assertIn("not biological observations", html)
        self.assertIn("Rscript files/visualization-example/run_example.R", html)
        for filename in EXPECTED_FIGURES:
            self.assertIn(f"../images/tutorial-figures/{filename}", html)
            self.assertTrue((FIGURES / filename).is_file())


@unittest.skipUnless(os.environ.get("RUN_R_EXAMPLE") == "1", "set RUN_R_EXAMPLE=1 to execute Rscript")
class OptionalRExecutionTest(unittest.TestCase):
    def test_example_runs_from_repository_root(self):
        rscript = shutil.which("Rscript")
        self.assertIsNotNone(rscript, "Rscript is required for the optional execution test")
        result = subprocess.run(
            [rscript, "files/visualization-example/run_example.R"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Completed synthetic Seurat/ggplot2 example.", result.stdout)
        self.assertIn("Reductions: pca, umap", result.stdout)


if __name__ == "__main__":
    unittest.main()
