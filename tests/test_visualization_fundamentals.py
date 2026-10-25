"""Focused checks for the R-first visualization lesson and its learner download."""
from __future__ import annotations

import csv
from html.parser import HTMLParser
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "tutorials" / "data-visualization-fundamentals.html"
RMD = ROOT / "files" / "tutorial-examples" / "data-visualization-fundamentals" / "data-visualization-fundamentals.Rmd"
FIXTURES = RMD.parent
R_CHUNKS = {
    "visualization-qc-r-stage": "qc-plots",
    "visualization-pca-r-stage": "pca",
    "visualization-umap-r-stage": "umap",
    "visualization-heatmap-r-stage": "heatmap",
    "visualization-volcano-stage": "volcano",
}
PYTHON_STAGES = {
    "visualization-qc-python-stage",
    "visualization-pca-stage",
    "visualization-umap-stage",
    "visualization-heatmap-python-stage",
    "visualization-volcano-python-stage",
}


class CodeStageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stage_id: str | None = None
        self.in_code = False
        self.code: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "pre":
            self.stage_id = attrs.get("id")
            if self.stage_id:
                self.code[self.stage_id] = ""
        elif tag == "code" and self.stage_id:
            self.in_code = True

    def handle_data(self, data):
        if self.in_code and self.stage_id:
            self.code[self.stage_id] += data

    def handle_endtag(self, tag):
        if tag == "code":
            self.in_code = False
        elif tag == "pre":
            self.stage_id = None


def parse_stages() -> dict[str, str]:
    parser = CodeStageParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser.code


class VisualizationFundamentalsContentTests(unittest.TestCase):
    def test_r_markdown_download_and_render_instructions_are_linked(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertIn("R Markdown lab", html)
        self.assertIn("data-visualization-fundamentals.Rmd", html)
        self.assertTrue(RMD.is_file())
        for name in ("qc_metrics.tsv", "counts.tsv", "deseq2_results.tsv"):
            self.assertTrue((FIXTURES / name).is_file(), name)
            self.assertIn(name, html)
        for text in (
            "rmarkdown::render",
            "install.packages(c(\"rmarkdown\", \"ggplot2\", \"uwot\"))",
            "not biological observations",
            "does not run differential-expression analysis",
            "Optional Python setup",
            "python -m pip install numpy pandas matplotlib seaborn scikit-learn umap-learn",
        ):
            self.assertIn(text, html + RMD.read_text(encoding="utf-8"))
        self.assertIn("sessionInfo()", RMD.read_text(encoding="utf-8"))

    def test_each_plot_task_has_r_first_and_same_task_python_alternative(self):
        stages = parse_stages()
        self.assertTrue(set(R_CHUNKS).issubset(stages))
        self.assertTrue(PYTHON_STAGES.issubset(stages))
        html = HTML.read_text(encoding="utf-8")
        for task in ("Inspect distributions", "PCA:", "UMAP:", "Heatmaps:", "Volcano plots:"):
            self.assertIn(task, html)
        for stage in R_CHUNKS:
            self.assertIn("library(ggplot2)", stages[stage], stage)
        self.assertIn("uwot::umap", stages["visualization-umap-r-stage"])
        self.assertIn("geom_tile", stages["visualization-heatmap-r-stage"])
        self.assertIn("np.log10", stages["visualization-volcano-python-stage"])
        self.assertIn("synthetic", html.lower())
        self.assertNotIn("—", html)

    def test_displayed_r_panels_match_the_downloadable_report_chunks(self):
        stages = parse_stages()
        markdown = RMD.read_text(encoding="utf-8")
        for stage, label in R_CHUNKS.items():
            match = re.search(r"```\{r " + re.escape(label) + r"\}\n(.*?)\n```", markdown, re.S)
            self.assertIsNotNone(match, label)
            self.assertEqual(stages[stage].strip(), match.group(1).strip(), label)

    def test_fixture_is_small_and_explicitly_synthetic(self):
        with (FIXTURES / "qc_metrics.tsv").open(newline="", encoding="utf-8") as handle:
            qc = list(csv.DictReader(handle, delimiter="\t"))
        with (FIXTURES / "counts.tsv").open(newline="", encoding="utf-8") as handle:
            counts = list(csv.reader(handle, delimiter="\t"))
        self.assertEqual(len(qc), 6)
        self.assertEqual(len(counts), 11)
        self.assertEqual(counts[0][1:], [row["sample"] for row in qc])
        self.assertIn("synthetic", RMD.read_text(encoding="utf-8").lower())


R_AVAILABLE = bool(shutil.which("Rscript"))
if R_AVAILABLE:
    check = subprocess.run(
        [shutil.which("Rscript"), "-e", 'quit(status=if(all(vapply(c("rmarkdown", "knitr", "ggplot2", "uwot"), requireNamespace, logical(1), quietly=TRUE)) && rmarkdown::pandoc_available()) 0L else 1L)'],
        capture_output=True, text=True, timeout=20,
    )
    R_AVAILABLE = check.returncode == 0


@unittest.skipUnless(R_AVAILABLE, "local Rscript, rmarkdown, knitr, Pandoc, ggplot2, and uwot are required for render check")
class VisualizationRMarkdownRenderTests(unittest.TestCase):
    def test_report_renders_all_figures_and_six_sample_coordinates(self):
        rscript = shutil.which("Rscript")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "data").mkdir()
            (project / "results").mkdir()
            shutil.copyfile(RMD, project / RMD.name)
            for name in ("qc_metrics.tsv", "counts.tsv"):
                shutil.copyfile(FIXTURES / name, project / "data" / name)
            shutil.copyfile(FIXTURES / "deseq2_results.tsv", project / "results" / "deseq2_results.tsv")
            run = subprocess.run(
                [rscript, "-e", 'rmarkdown::render("data-visualization-fundamentals.Rmd", output_dir="results")'],
                cwd=project, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            for name in (
                "data-visualization-fundamentals.html",
                "qc_boxplot.png", "qc_histogram.png", "pca_plot.png",
                "umap_plot.png", "heatmap_topgenes.png", "volcano.png",
            ):
                path = project / "results" / name
                self.assertTrue(path.is_file(), name)
                self.assertGreater(path.stat().st_size, 1000, name)
            report = (project / "results" / "data-visualization-fundamentals.html").read_text(encoding="utf-8")
            self.assertGreaterEqual(report.count("data:image/png;base64"), 6)
            self.assertIn("R version", report)
            for name, expected_columns in (("pca_coords.tsv", {"sample", "PC1", "PC2"}),
                                           ("umap_coords.tsv", {"sample", "UMAP1", "UMAP2"})):
                with (project / "results" / name).open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle, delimiter="\t"))
                self.assertEqual(len(rows), 6, name)
                self.assertTrue(expected_columns.issubset(rows[0]), name)
            with (project / "results" / "pca_plot.png").open("rb") as image:
                header = image.read(24)
            self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
            self.assertGreater(struct.unpack(">II", header[16:24])[0], 300)


if __name__ == "__main__":
    unittest.main()
