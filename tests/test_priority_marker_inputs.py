#!/usr/bin/env python3
"""Synthetic regression checks for the marker-input fixes in one tutorial.

No biological dataset is read. The Seurat test executes the displayed missing-UMAP
branch with Seurat and validates its actual labels; the Scanpy test executes the
source-saving and ranking lines against a deliberately misleading .raw matrix.
"""
from __future__ import annotations

from pathlib import Path
from html import unescape
import importlib.util
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "tutorials/ai-prompt-engineering-seurat.html"
CODE_BLOCK = re.compile(r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", re.S)


def displayed_pre_blocks() -> list[str]:
    """Decode displayed literal code without stripping whitespace or literal tabs."""
    return [unescape(block) for block in CODE_BLOCK.findall(TUTORIAL.read_text(encoding="utf-8"))]


def seurat_script() -> str:
    return next(block for block in displayed_pre_blocks()
                if block.startswith("# Save this as ./scripts/seurat_marker_workflow.R"))


def scanpy_script() -> str:
    return next(block for block in displayed_pre_blocks()
                if block.startswith("# Save this as ./scripts/scanpy_quick_workflow.py"))


def between(text: str, start: str, end: str) -> str:
    first = text.index(start)
    last = text.index(end, first)
    return text[first:last]


class SeuratLabelPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rscript = shutil.which("Rscript")
        if cls.rscript is None:
            raise unittest.SkipTest("Rscript is unavailable")
        check = subprocess.run(
            [cls.rscript, "-e", "quit(status=if(requireNamespace('Seurat', quietly=TRUE)) 0 else 1)"],
            capture_output=True, text=True, check=False,
        )
        if check.returncode:
            raise unittest.SkipTest("Seurat is not installed")
        block = seurat_script()
        cls.branch = between(
            block,
            "# Validate metadata before plotting or using the cluster identities.",
            "# Save UMAP plot (colored by clusters)",
        )
        cls.marker_selection = between(
            block,
            "# Select and persist the explicitly intended comparison metadata.",
            "# Filter by adjusted p-value",
        )
        cls.label_guard = between(
            block,
            "# Visualization work must leave the input biological labels unchanged.",
            "# Save UMAP plot (colored by clusters)",
        )

    def synthetic_r_harness(self, body: str) -> str:
        return "\n".join([
            "suppressPackageStartupMessages(library(Seurat))",
            "suppressPackageStartupMessages(library(ggplot2))",
            "set.seed(27)",
            "n_genes <- 24L; n_cells <- 60L",
            "counts <- matrix(rpois(n_genes * n_cells, lambda=4), nrow=n_genes)",
            "rownames(counts) <- paste0('synthetic_gene_', seq_len(n_genes))",
            "colnames(counts) <- paste0('synthetic_cell_', seq_len(n_cells))",
            "labels <- rep(c('0', '1', '2'), each=20)",
            "counts[1:4, labels == '2'] <- counts[1:4, labels == '2'] + 8L",
            "metadata <- data.frame(seurat_clusters=factor(labels, levels=c('0','1','2')), row.names=colnames(counts))",
            "seurat_obj <- CreateSeuratObject(counts=counts, meta.data=metadata)",
            "outdir <- tempdir()",
            body,
        ])

    def run_r(self, script: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="marker-seurat-synthetic-") as directory:
            path = Path(directory) / "synthetic_test.R"
            path.write_text(script, encoding="utf-8")
            return subprocess.run(
                [self.rscript, str(path)], cwd=directory, capture_output=True,
                text=True, check=False, timeout=240,
            )

    def test_missing_umap_keeps_actual_input_labels_for_marker_comparison(self):
        self.assertNotIn("FindClusters(", self.branch)
        marker_selection = self.marker_selection
        self.assertIn('Idents(seurat_obj) <- comparison_metadata$identity_field', marker_selection)
        self.assertIn("ident.2 = comparison_metadata$ident.2", marker_selection)
        self.assertIn("seurat_obj@misc$cluster2_marker_comparison <- comparison_metadata", marker_selection)

        body = self.branch + '\ncomparison_metadata$test <- "wilcox"\n' + marker_selection + "\n".join([
            'stopifnot(identical(incoming_cluster_labels, unname(as.character(seurat_obj[[]][["seurat_clusters"]]))))',
            'stopifnot(identical(comparison_metadata$identity_field, "seurat_clusters"))',
            'stopifnot(identical(comparison_metadata$cluster_of_interest, "2"))',
            'stopifnot(identical(comparison_metadata$ident.1, "2"), is.null(comparison_metadata$ident.2))',
            'stopifnot(identical(comparison_metadata$reference, "all other cells"))',
            'stopifnot(length(umap_dims) <= ncol(Embeddings(seurat_obj, reduction="pca")))',
            'stopifnot(length(WhichCells(seurat_obj, idents="2")) == 20L)',
            'stopifnot(length(WhichCells(seurat_obj, idents=c("0", "1"))) == 40L)',
            'stopifnot(identical(seurat_obj@misc$cluster2_marker_comparison$identity_field, "seurat_clusters"))',
            'cat("synthetic Seurat labels unchanged:", paste(sort(unique(incoming_cluster_labels)), collapse=","), "\\n")',
        ])
        result = self.run_r(self.synthetic_r_harness(body))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("synthetic Seurat labels unchanged: 0,1,2", result.stdout)

    def test_displayed_identity_guard_rejects_a_changed_label_vector(self):
        # Execute the exact displayed guard with a deliberately altered identity field.
        guard = self.label_guard
        self.assertIn('stop("The incoming seurat_clusters labels changed while preparing the UMAP.")', guard)
        body = "\n".join([
            "incoming_cluster_labels <- c('0', '1', '2')",
            "seurat_obj <- CreateSeuratObject(counts=matrix(1:12, nrow=3, dimnames=list(paste0('g',1:3), paste0('c',1:4))),",
            "  meta.data=data.frame(seurat_clusters=c('0','1','2','2'), row.names=paste0('c',1:4)))",
            "seurat_obj$seurat_clusters[1] <- '2'",
            guard,
        ])
        result = self.run_r("suppressPackageStartupMessages(library(Seurat))\n" + body)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("labels changed", result.stderr)


class ScanpyExpressionSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec("scanpy") is None or importlib.util.find_spec("anndata") is None:
            raise unittest.SkipTest("Scanpy/AnnData are unavailable in this Python environment")
        import scanpy as sc
        import anndata as ad
        import numpy as np

        cls.sc = sc
        cls.ad = ad
        cls.np = np
        block = scanpy_script()
        cls.source_steps = between(
            block,
            "# Normalize counts, then preserve an unscaled log-normalized source before HVG selection.",
            "# Keep adata full-gene for ranking; use an HVG-only copy for scaled embeddings.",
        )
        cls.rank_steps = between(
            block,
            "# Rank all genes retained after filtering from the saved, unscaled log1p-normalized layer.",
            "# Convert to a readable table and save",
        )

    def make_adata_with_misleading_raw(self):
        np = self.np
        counts = np.array([
            [100, 1, 5, 2], [80, 1, 2, 4], [120, 2, 1, 2], [90, 1, 3, 1],
            [1, 100, 5, 2], [1, 80, 2, 3], [2, 120, 2, 1], [1, 90, 3, 2],
        ], dtype=np.float32)
        obs = {"leiden_r10": ["0"] * 4 + ["1"] * 4}
        var = {"gene_symbol": ["A_cluster0", "B_cluster1", "shared_a", "shared_b"]}
        from scipy import sparse
        adata = self.ad.AnnData(X=sparse.csr_matrix(counts.copy()), obs=obs, var=var)
        adata.var_names = var["gene_symbol"]
        # Deliberately stale/wrong-scale values: raw ranks the opposite first two genes.
        stale = counts.copy()
        stale[:4, 0] = 1
        stale[4:, 0] = 100
        stale[:4, 1] = 100
        stale[4:, 1] = 1
        adata.raw = self.ad.AnnData(X=sparse.csr_matrix(stale), obs=adata.obs.copy(), var=adata.var.copy())
        return adata

    def rank_names(self, adata, group="0"):
        return list(adata.uns["rank_genes_groups"]["names"][group])

    def test_source_layer_overrides_existing_raw_and_ranks_all_retained_genes(self):
        sc = self.sc
        adata = self.make_adata_with_misleading_raw()
        scope = {"sc": sc, "adata": adata}
        exec(self.source_steps, scope)
        adata_hvg = adata[:, ["A_cluster0", "B_cluster1", "shared_a"]].copy()
        exec('sc.pp.scale(adata_hvg, max_value=10)', {"sc": sc, "adata_hvg": adata_hvg})

        # The layer is unchanged by scaling the separate embedding object.
        self.np.testing.assert_allclose(adata.layers["log1p_norm"].toarray(), adata.X.toarray())
        self.assertEqual(adata.shape[1], 4)
        self.assertEqual(adata.layers["log1p_norm"].shape[1], 4)
        exec(self.rank_steps, {"sc": sc, "adata": adata})
        selected_names = self.rank_names(adata)

        expected = adata.copy()
        expected.raw = None
        expected.X = expected.layers["log1p_norm"].copy()
        sc.tl.rank_genes_groups(
            expected, "leiden_r10", method="t-test_overestim_var", reference="rest",
            use_raw=False,
        )
        self.assertEqual(selected_names, self.rank_names(expected))
        self.assertEqual(set(selected_names), set(adata.var_names))

        # A deliberately wrong pre-existing .raw would produce a different ranking.
        raw_ranked = adata.copy()
        sc.tl.rank_genes_groups(
            raw_ranked, "leiden_r10", method="t-test_overestim_var", reference="rest",
            use_raw=True,
        )
        self.assertNotEqual(selected_names[:2], self.rank_names(raw_ranked)[:2])
        self.assertEqual(selected_names[0], "A_cluster0")

    def test_displayed_ranking_call_cannot_fall_back_to_raw_or_omit_layer(self):
        call = next(line.strip() for line in self.rank_steps.splitlines()
                    if line.lstrip().startswith("sc.tl.rank_genes_groups("))
        self.assertIn("layer='log1p_norm'", self.rank_steps)
        self.assertIn("use_raw=False", self.rank_steps)
        # Execute the actual multi-line call above against the intentionally stale .raw.
        self.assertIn("reference='rest'", self.rank_steps)
        self.assertTrue(call.startswith("sc.tl.rank_genes_groups("))
        adata = self.make_adata_with_misleading_raw()
        scope = {"sc": self.sc, "adata": adata}
        exec(self.source_steps, scope)
        exec(self.rank_steps, scope)
        self.assertEqual(self.rank_names(adata)[0], "A_cluster0")


class LearnerFeedbackTests(unittest.TestCase):
    def test_feedback_explains_unchanged_labels_and_selected_expression_scale(self):
        details = next(item for item in re.findall(
            r"<details\b[^>]*>.*?</details>", TUTORIAL.read_text(encoding="utf-8"), re.S
        ) if "Show the answer and feedback" in item)
        answer = unescape(re.sub(r"<[^>]+>", "", details))
        self.assertIn("incoming", answer)
        self.assertIn("does not recluster", answer)
        self.assertIn('layer="log1p_norm"', answer)
        self.assertIn("not scaled", answer)
        self.assertIn("all genes retained after filtering", answer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
