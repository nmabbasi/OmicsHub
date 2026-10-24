"""Bounded contracts for the newly reproduced advanced tutorial failures."""
from html import unescape
import csv
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def text(slug):
    return unescape((ROOT / "tutorials" / (slug + ".html")).read_text(encoding="utf-8"))


class PseudobulkSourceContracts(unittest.TestCase):
    def test_seurat_assays_are_qualified_after_loading_deseq2(self):
        source = text("transcriptomics-differential-expression")
        self.assertIn("library(DESeq2)", source)
        self.assertIn('if (!"RNA" %in% SeuratObject::Assays(seurat_obj))', source)
        self.assertNotIn('%in% Assays(seurat_obj)', source)

    def test_both_ggplot_exports_explicitly_have_white_backgrounds(self):
        source = text("transcriptomics-differential-expression")
        for filename in ("pca", "volcano"):
            match = re.search(r'ggsave\("output/plots/' + filename + r'\.png"[^\n]+', source)
            self.assertIsNotNone(match, filename)
            self.assertIn('bg = "white"', match.group())


@unittest.skipUnless(os.environ.get("PSEUDOBULK_TEST_R_LIBRARY") and shutil.which("Rscript"),
                     "Set the isolated DESeq2 library for the real namespace regression")
class RealPseudobulkNamespaceTests(unittest.TestCase):
    def test_assay_accessor_works_with_both_packages_attached(self):
        source = '''
.libPaths(c(Sys.getenv("PSEUDOBULK_TEST_R_LIBRARY"), .libPaths()))
library(Seurat)
library(DESeq2)
# Invented tiny matrix tests dispatch only; no biological analysis is performed.
counts <- matrix(c(1L, 2L, 3L, 4L), nrow=2,
                 dimnames=list(c("fixture1", "fixture2"), c("cell1", "cell2")))
object <- CreateSeuratObject(counts=counts, min.cells=0, min.features=0)
stopifnot("RNA" %in% SeuratObject::Assays(object))
original <- tryCatch("RNA" %in% Assays(object), error=function(error) error)
stopifnot(inherits(original, "error"))
cat("Qualified accessor passed with DESeq2 attached; original accessor reproduced failure\\n")
'''
        result = subprocess.run([shutil.which("Rscript"), "--vanilla", "-e", source],
                                capture_output=True, text=True, timeout=120,
                                env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("original accessor reproduced failure", result.stdout)

    def test_displayed_aggregation_preserves_ids_seurat_would_rewrite_or_merge(self):
        page = text("transcriptomics-differential-expression")
        stage = page.split("# Temporary codes prevent Seurat", 1)[1]
        stage = "# Temporary codes prevent Seurat" + stage.split("# Make the column order explicit", 1)[0]
        setup = '''
.libPaths(c(Sys.getenv("PSEUDOBULK_TEST_R_LIBRARY"), .libPaths()))
library(Seurat)
library(DESeq2)
# Invented software-only fixture: four labels, not a biological study.
counts <- matrix(seq_len(16L), nrow=2,
                 dimnames=list(c("fixture1", "fixture2"), paste0("cell", seq_len(8L))))
obj_ct <- CreateSeuratObject(counts=counts, min.cells=0, min.features=0)
obj_ct$sample_id <- rep(c("donor_1", "donor-1", "101", "g101"), each=2L)
meta_ct <- obj_ct[[]]
'''
        validation = '''
stopifnot(setequal(colnames(pb), c("donor_1", "donor-1", "101", "g101")))
stopifnot(ncol(pb) == 4L)
for (id in colnames(pb)) {
  expected <- rowSums(counts[, as.character(meta_ct$sample_id) == id, drop=FALSE])
  stopifnot(identical(as.numeric(pb[, id]), as.numeric(expected)))
}
cat("All original IDs and sample sums preserved without collisions\\n")
'''
        result = subprocess.run([shutil.which("Rscript"), "--vanilla", "-e", setup + stage + validation],
                                capture_output=True, text=True, timeout=120,
                                env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("without collisions", result.stdout)

    def test_patchwork_theme_reaches_both_panels(self):
        source = '''
.libPaths(c(Sys.getenv("PSEUDOBULK_TEST_R_LIBRARY"), .libPaths()))
library(ggplot2)
p <- patchwork::wrap_plots(ggplot() + theme(legend.position="top"),
                           ggplot() + theme(legend.position="top"))
original <- p + theme(legend.position="right")
stopifnot(original[[1]]$theme$legend.position == "top")
corrected <- p & theme(legend.position="right")
stopifnot(corrected[[1]]$theme$legend.position == "right",
          corrected[[2]]$theme$legend.position == "right")
cat("Both panel themes updated; original only updated final panel\\n")
'''
        result = subprocess.run([shutil.which("Rscript"), "--vanilla", "-e", source],
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Both panel themes updated", result.stdout)


class SpatialRawCountContracts(unittest.TestCase):
    def test_library_size_qc_is_computed_once_before_transformations(self):
        source = text("spatial-transcriptomics-r-python")
        self.assertEqual(source.count("sc.pp.calculate_qc_metrics(adata, inplace=True)"), 1)
        qc = source.index("sc.pp.calculate_qc_metrics(adata, inplace=True)")
        self.assertLess(source.index("adata.var_names_make_unique()"), qc)
        self.assertLess(qc, source.index("sc.pp.normalize_total(adata, inplace=True)"))
        self.assertLess(qc, source.index("sc.pp.log1p(adata)"))
        self.assertIn("raw counts per spot", source)

    def test_reader_and_plots_still_use_the_documented_squidpy_apis(self):
        source = text("spatial-transcriptomics-r-python")
        self.assertIn('sq.read.visium(shared_input, counts_file="filtered_feature_bc_matrix.h5")', source)
        self.assertIn('sq.pl.spatial_scatter(adata, color=["total_counts", "Snap25"]', source)
        self.assertIn('sq.pl.spatial_scatter(adata, color="clusters"', source)

    def test_hdf5_reader_preflight_precedes_loading(self):
        source = text("spatial-transcriptomics-r-python")
        readiness = source.index('if (!requireNamespace("hdf5r", quietly = TRUE)) stop(')
        self.assertLess(readiness, source.index("spatial_data <- Load10X_Spatial"))
        self.assertIn("libhdf5-dev", source)

    def test_combined_feature_plot_styles_every_panel(self):
        source = text("spatial-transcriptomics-r-python")
        self.assertIn('SpatialFeaturePlot(spatial_data, features = c("nCount_Spatial", "Snap25")) &', source)
        self.assertNotIn('SpatialFeaturePlot(spatial_data, features = c("nCount_Spatial", "Snap25")) +', source)


class OrthoFinderVersionContracts(unittest.TestCase):
    def test_version_three_core_tree_is_not_described_as_stag_only(self):
        source = text("phylogenomics-orthofinder")
        self.assertIn("OrthoFinder 3.2", source)
        self.assertIn("concatenated alignment of single-copy orthogroups", source)
        self.assertIn("--assign", source)
        self.assertIn("-ST astral-pro", source)
        self.assertNotIn("does not simply concatenate", source)

    def test_final_orthogroups_path_and_legacy_n0_are_version_scoped(self):
        source = text("phylogenomics-orthofinder")
        self.assertIn("From version 3.1", source)
        self.assertIn("Orthogroups/Orthogroups.tsv", source)
        self.assertIn("is no longer produced", source)
        self.assertIn("orthofinder -f ExampleData -t 4", source)
        self.assertNotIn("No OrthoFinder run or release is asserted as tested here", source)


@unittest.skipUnless(os.environ.get("ORTHOFINDER_TEST_RESULTS_DIR"),
                     "Set the saved genuine upstream OrthoFinder results for output checks")
class RealOrthoFinderOutputTests(unittest.TestCase):
    def test_official_example_has_four_species_and_a_consistent_group_table(self):
        directory = Path(os.environ["ORTHOFINDER_TEST_RESULTS_DIR"])
        table = directory / "Orthogroups/Orthogroups.tsv"
        tree = directory / "Species_Tree/SpeciesTree_rooted.txt"
        with table.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            self.assertEqual(reader.fieldnames[0], "Orthogroup")
            species = reader.fieldnames[1:]
            self.assertEqual(len(species), 4)
            rows = list(reader)
        self.assertGreater(len(rows), 0)
        newick = tree.read_text()
        self.assertTrue(newick.strip().endswith(";"))
        for name in species:
            self.assertIn(name, newick)
        self.assertFalse((directory / "Phylogenetic_Hierarchical_Orthogroups/N0.tsv").exists())
        for row in rows:
            self.assertTrue(row["Orthogroup"])
            self.assertTrue(any(row[name].strip() for name in species))


if __name__ == "__main__":
    unittest.main()
