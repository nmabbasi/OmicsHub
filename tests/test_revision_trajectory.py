"""Offline contracts and optional runtime check for the trajectory lesson.

The default tests use only the Python standard library. The integration test runs
only when Scanpy and its scientific dependencies are already installed; it never
installs or modifies packages.
"""
from __future__ import annotations

import ast
import importlib.util
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
        cls.python = "\n".join(cls.page.python_blocks[0])
        cls.r_code = "\n".join(cls.page.r_blocks[0])
        cls.article_text = " ".join(cls.page.article_text)

    def test_displayed_scanpy_example_parses_as_python(self) -> None:
        self.assertEqual(len(self.page.python_blocks), 1)
        ast.parse(self.python, filename=str(PAGE))

    def test_neighbor_graph_reuse_is_exact_or_requires_approval(self) -> None:
        code = self.python
        for contract in (
            'GRAPH_KEY = "trajectory_pca30"',
            'REP_KEY = "X_pca"',
            'N_PCS = 30',
            'N_NEIGHBORS = 15',
            '"use_rep": REP_KEY',
            '"n_pcs": N_PCS',
            '"n_neighbors": N_NEIGHBORS',
            '"random_state": RANDOM_STATE',
            "if matches:",
            "if not APPROVE_REBUILD_NEIGHBORS:",
            'key_added=GRAPH_KEY',
            'adata.uns["trajectory_provenance"]',
        ):
            self.assertIn(contract, code)
        self.assertIn("coords.shape[1] < N_PCS", code)
        self.assertIn("not np.isfinite(coords[:, :N_PCS]).all()", code)
        self.assertNotIn("n_pcs=40", code)

    def test_roots_are_named_validated_sensitivity_checked_and_component_aware(self) -> None:
        code = self.python
        self.assertIn('"primary"', code)
        self.assertIn('"sensitivity"', code)
        self.assertIn("adata.obs_names.get_loc(cell_id)", code)
        self.assertIn("EXPECTED_ROOT_STATE", code)
        self.assertIn('"rationale":', code)
        self.assertIn("connected_components(", code)
        self.assertIn("values[component != component[root_index]] = np.nan", code)
        self.assertNotIn("root_cells[0]", code)
        self.assertNotIn("np.flatnonzero(adata.obs", code)

    def test_umap_is_display_only_and_dpt_values_are_colored_not_projected(self) -> None:
        code = self.python
        self.assertIn('color="dpt_primary"', code)
        self.assertIn("UMAP display only", code)
        self.assertIn("grey = disconnected", code)
        self.assertNotIn("sc.tl.umap", code)
        self.assertNotIn("init_pos", code)

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
        self.assertIn('lesson-format--decision-guide', self.source)
        self.assertIn('href="cell-type-annotation-methods.html" rel="prev"', self.source)
        self.assertIn('href="../start-here.html#sh-single-cell" rel="next"', self.source)
        self.assertIn('data-tutorial-format="conceptual-guide"', self.source)


SCANPY_AVAILABLE = importlib.util.find_spec("scanpy") is not None


@unittest.skipUnless(SCANPY_AVAILABLE, "optional scientific runtime skipped: Scanpy is not installed")
class TrajectoryLessonScanpyRuntimeTests(unittest.TestCase):
    def test_visible_code_runs_on_an_invented_disconnected_graph(self) -> None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import anndata as ad
        import numpy as np
        import pandas as pd
        import scanpy as sc
        from scipy.sparse import coo_matrix
        from unittest.mock import patch

        _, page = load_lesson()
        code = "\n".join(page.python_blocks[0])
        code = code.replace("N_PCS = 30", "N_PCS = 3")
        code = code.replace("N_NEIGHBORS = 15", "N_NEIGHBORS = 3")
        code = code.replace('"REPLACE_WITH_REVIEWED_EARLY_CELL_A"', '"e0"')
        code = code.replace('"REPLACE_WITH_REVIEWED_EARLY_CELL_B"', '"e1"')
        code = code.replace("Replace with evidence for the proposed starting state.",
                            "Invented fixture: e0 is designated early.")

        connected_count, island_count = 16, 4
        n_obs = connected_count + island_count
        obs_names = [f"e{i}" if i < 2 else f"c{i}" for i in range(connected_count)]
        obs_names += [f"x{i}" for i in range(island_count)]
        first = np.column_stack((np.arange(connected_count, dtype=float),
                                 np.zeros(connected_count),
                                 np.linspace(0.0, 1.0, connected_count)))
        island = np.column_stack((100.0 + np.arange(island_count, dtype=float),
                                  np.full(island_count, 100.0),
                                  np.linspace(4.0, 5.0, island_count)))
        pca = np.vstack((first, island))
        states = ["early", "early"] + ["middle"] * (connected_count - 2) + ["other"] * island_count
        cluster_labels = (["early"] * 2 + ["middle"] * 8 + ["late"] * 6 + ["island"] * island_count)
        adata = ad.AnnData(
            X=np.zeros((n_obs, 5), dtype=float),
            obs=pd.DataFrame({"state": states, "leiden": cluster_labels}, index=obs_names),
        )
        adata.obsm["X_pca"] = pca
        adata.obsm["X_umap"] = np.column_stack((pca[:, 0], pca[:, 1] + np.linspace(0, 1, n_obs)))
        sc.pp.neighbors(adata, n_neighbors=3, use_rep="X_pca", n_pcs=3,
                        method="umap", metric="euclidean", random_state=0,
                        key_added="trajectory_pca30")

        # Make the teaching fixture contain two known components while retaining
        # Scanpy's actual graph metadata and graph objects.
        group = np.array([0] * connected_count + [1] * island_count)
        for key in ("trajectory_pca30_connectivities", "trajectory_pca30_distances"):
            graph = adata.obsp[key].tocoo()
            keep = group[graph.row] == group[graph.col]
            adata.obsp[key] = coo_matrix(
                (graph.data[keep], (graph.row[keep], graph.col[keep])),
                shape=graph.shape,
            ).tocsr()

        namespace = {"adata": adata}
        # PAGA alone is bypassed because this shared runtime has no igraph.
        # Neighbor metadata, diffusion maps, both DPT roots, graph components,
        # unassigned masking, and UMAP display still use the real Scanpy code.
        with patch.object(sc.tl, "paga"), patch.object(sc.pl, "paga"):
            exec(compile(code, str(PAGE), "exec"), namespace)

        self.assertEqual(adata.uns["trajectory_provenance"]["graph_action"],
                         "reused: graph key, representation, dimensions, and settings match")
        self.assertEqual(adata.uns["trajectory_provenance"]["connected_components"], 2)
        self.assertEqual(adata.uns["trajectory_roots"]["primary"]["cell_id"], "e0")
        self.assertEqual(adata.uns["trajectory_roots"]["sensitivity"]["cell_id"], "e1")
        self.assertTrue(np.isfinite(adata.obs.loc[obs_names[:connected_count], "dpt_primary"]).all())
        self.assertTrue(adata.obs.loc[obs_names[connected_count:], "dpt_primary"].isna().all())
        self.assertTrue(np.isfinite(adata.obs.loc[obs_names[:connected_count], "dpt_sensitivity"]).all())
        self.assertTrue(adata.obs.loc[obs_names[connected_count:], "dpt_sensitivity"].isna().all())
        self.assertAlmostEqual(float(adata.obs.loc["e0", "dpt_primary"]), 0.0, places=6)
        self.assertAlmostEqual(float(adata.obs.loc["e1", "dpt_sensitivity"]), 0.0, places=6)
        self.assertFalse(np.allclose(
            adata.obs.loc[obs_names[:connected_count], "dpt_primary"].to_numpy(),
            adata.obs.loc[obs_names[:connected_count], "dpt_sensitivity"].to_numpy(),
        ))
        self.assertEqual(int(adata.uns["iroot"]), int(adata.obs_names.get_loc("e0")))
        plt.close("all")


if __name__ == "__main__":
    unittest.main()
