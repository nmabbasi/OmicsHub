"""Offline contracts for the R-first trajectory lesson."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import unittest


PAGE = Path(__file__).resolve().parents[1] / "tutorials" / "scrna-seq-trajectory-inference.html"


class LessonParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.article_depth = 0
        self.article_text: list[str] = []
        self.python_blocks: list[list[str]] = []
        self.r_blocks: list[list[str]] = []
        self.active_code: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "article":
            self.article_depth += 1
        if tag == "code" and values.get("class") == "language-python":
            self.active_code = []
            self.python_blocks.append(self.active_code)
        elif tag == "code" and values.get("class") == "language-r":
            self.active_code = []
            self.r_blocks.append(self.active_code)

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self.article_depth:
            self.article_depth -= 1
        if tag == "code":
            self.active_code = None

    def handle_data(self, data: str) -> None:
        if self.article_depth:
            self.article_text.append(data)
        if self.active_code is not None:
            self.active_code.append(data)


def load_lesson() -> tuple[str, LessonParser]:
    source = PAGE.read_text(encoding="utf-8")
    parser = LessonParser()
    parser.feed(source)
    parser.close()
    return source, parser


class TrajectoryLessonOfflineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source, cls.page = load_lesson()
        cls.r_code = "\n".join(cls.page.r_blocks[0]) if cls.page.r_blocks else ""
        cls.article_text = " ".join(cls.page.article_text)

    def test_worked_routes_are_r_only_and_no_non_equivalent_python_is_offered(self) -> None:
        self.assertGreaterEqual(len(self.page.r_blocks), 1)
        self.assertEqual(self.page.python_blocks, [])
        self.assertIn("R methods are the worked routes.", self.article_text)
        self.assertIn("This guide therefore shows no Python workflow", self.article_text)

    def test_paga_and_dpt_are_described_as_distinct_scanpy_methods(self) -> None:
        self.assertIn(
            "PAGA and DPT are distinct Scanpy methods, not Python translations of Slingshot or Monocle3.",
            self.article_text,
        )
        self.assertIn(
            "PAGA summarizes connectivity among selected partitions, while DPT calculates a root-relative diffusion ordering on a neighbor graph.",
            self.article_text,
        )
        self.assertIn("scanpy.readthedocs.io", self.source)

    def test_slingshot_fits_pca_and_does_not_draw_pca_curves_on_umap(self) -> None:
        self.assertIn("reducedDim = 'PCA'", self.r_code)
        self.assertIn("reducedDims(sce)$UMAP", self.r_code)
        self.assertIn("UMAP display only; fit in PCA", self.r_code)
        self.assertIn("START_CLUSTER", self.r_code)
        self.assertIn("LINEAGE_INDEX <- 1L", self.r_code)
        self.assertIn("pt_all[, LINEAGE_INDEX]", self.r_code)
        self.assertIn("'Slingshot lineage '", self.r_code)
        self.assertIn("' of ', ncol(pt_all)", self.r_code)
        self.assertIn("other inferred lineages are not shown", self.article_text)
        self.assertNotIn("slingPseudotime(sce)[, 1]", self.r_code)
        self.assertNotIn("reducedDim = 'UMAP'", self.r_code)
        self.assertNotIn("lines(SlingshotDataSet(sce)", self.r_code)

    def test_invented_graph_has_worked_roots_and_disconnected_outcome(self) -> None:
        for phrase in (
            "known invented graph", "A0 to A1", "A1 to M", "M to L", "M to R",
            "X to Y", "root A0 gives A0:0, A1:1, M:2, and L/R:3",
            "Root A1 gives A1:0, A0 and M:1, and L/R:2",
            "X and Y remain disconnected", "not observed time",
        ):
            self.assertIn(phrase, self.article_text)

    def test_legacy_report_is_clearly_optional_and_not_promised_as_reproducible(self) -> None:
        self.assertIn("Legacy Slingshot report (reference only)", self.article_text)
        self.assertIn('href="examples/Trajectory_inference_using_Slingshot.html"', self.source)
        self.assertIn("local input file is not bundled", self.article_text)
        self.assertIn("recorded execution includes errors", self.article_text)
        self.assertNotIn("Live Case Studies", self.source)
        self.assertNotIn("cancer single-cell datasets", self.source)
        self.assertIn("Compare methods and review the result", self.article_text)
        self.assertIn("Interpreting an inferred ordering", self.article_text)
        self.assertIn("known invented graph", self.article_text)

    def test_reader_facing_article_has_no_em_dash_and_navigation_contract_remains(self) -> None:
        self.assertNotIn("\u2014", self.article_text)
        self.assertIn("lesson-format--decision-guide", self.source)
        self.assertIn('href="cell-type-annotation-methods.html" rel="prev"', self.source)
        self.assertIn('href="../start-here.html#sh-single-cell" rel="next"', self.source)
        self.assertIn('data-tutorial-format="conceptual-guide"', self.source)


if __name__ == "__main__":
    unittest.main()
