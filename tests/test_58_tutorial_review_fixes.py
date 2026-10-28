"""Focused regression checks for the twelve requested tutorial review fixes."""
from html import unescape
import hashlib
import json
from pathlib import Path
import re
import unittest
from tutorial_58_review_baseline import (
    REVIEW_PATHS, normalize_58_review, restore_58_review_asset, review_fixture,
)

ROOT = Path(__file__).resolve().parents[1]


def page(slug):
    return (ROOT / "tutorials" / f"{slug}.html").read_text(encoding="utf-8")


def code_blocks(slug):
    return [unescape(value) for value in re.findall(
        r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", page(slug), re.S
    )]


class TutorialReviewFixTests(unittest.TestCase):
    def test_kraken_arithmetic_and_krona_scope(self):
        article = page("metagenomics-kraken2-bracken")
        self.assertIn("620 = 20 direct assignments + 250 + 350", article)
        self.assertIn("The bacterial clade is 900, leaving 280", article)
        self.assertIn("complete species-level Bracken output totals 900 estimated reads", article)
        self.assertIn("unshown rows totaling 740", article)
        self.assertIn("fraction 100/900", article)
        self.assertIn("fraction 60/900", article)
        self.assertIn("deliberately stops before Krona", article)
        self.assertIn("not the query-ID/taxonomy-ID input", article)

    def test_liana_uses_current_label_argument_and_checks_exact_levels(self):
        article = page("cell-cell-communication")
        code = "\n".join(code_blocks("cell-cell-communication"))
        self.assertIn('idents_col = "cell_type"', code)
        self.assertNotIn("groupby =", code)
        self.assertIn("expected_cell_types", code)
        self.assertIn("setequal(observed_cell_types, expected_cell_types)", code)
        self.assertIn("leading/trailing whitespace", code)

    def test_flye_modes_are_conditional(self):
        article = page("long-read-pacbio-nanopore")
        self.assertIn("not every current basecaller/chemistry combination", article)
        self.assertIn("--nano-hq", article)
        self.assertIn("--read-error 0.05", article)
        self.assertIn("--pacbio-hifi", article)
        self.assertIn("--pacbio-raw", article)
        self.assertIn("Dorado", article)

    def test_tcr_barcode_prefix_and_overlap_are_explicit(self):
        article = page("tcr-bcr-repertoire-analysis")
        code = "\n".join(code_blocks("tcr-bcr-repertoire-analysis"))
        self.assertIn("AAACCTGAGACAGGTA-1", article)
        self.assertIn("Before (raw 10x)", code)
        self.assertIn("After one sample prefix", code)
        self.assertIn("If samples and ID both add sample_A", code)
        self.assertIn("min_expected_vdj_overlap", code)
        self.assertIn("is_valid_10x_barcode", code)
        self.assertIn("has_one_sample_prefix", code)
        self.assertIn("vapply(vdj_barcodes, has_one_sample_prefix", code)
        self.assertIn("exactly one sample prefix", code)
        self.assertIn("length(min_expected_vdj_overlap) != length(sample_ids)", code)
        self.assertIn("anyDuplicated(names(min_expected_vdj_overlap))", code)
        self.assertIn("0.95 minimum is a configurable teaching refusal gate", article)

    def test_singler_reports_overlap_and_refuses_below_documented_thresholds(self):
        article = page("advanced-ai-single-cell")
        code = "\n".join(code_blocks("advanced-ai-single-cell"))
        for marker in ("query_fraction", "reference_fraction", "unmatched_query",
                       "unmatched_reference", "singleR_unmatched_gene_ids.csv",
                       "min_shared_genes", "min_query_fraction", "min_reference_fraction"):
            self.assertIn(marker, code)
        self.assertIn("not a SingleR requirement", article)

    def test_music_reports_donors_per_type_before_fitting(self):
        article = page("single-cell-deconvolution")
        code = "\n".join(code_blocks("single-cell-deconvolution"))
        for marker in ("donors_per_type", "donor_cell_counts", "single_donor_types",
                       'clusters = cell_type_col', 'samples = donor_col'):
            self.assertIn(marker, code)
        self.assertIn("no universal donor-count cutoff", article)

    def test_16s_primary_route_includes_taxonomy_and_runnable_synthetic_fixture(self):
        article = page("16s-rrna-prokka-annotation")
        code = "\n".join(code_blocks("16s-rrna-prokka-annotation"))
        self.assertIn("R first: DADA2 denoising output through taxonomy assignment", article)
        self.assertIn("assignTaxonomy(", code)
        self.assertIn("classify-sklearn", code)
        self.assertIn("DADA2 1.30.0", article)
        self.assertIn("not evidence of taxonomic accuracy", article)
        workflow = ROOT / "files/tutorial-examples/16s-dada2-taxonomy/dada2-taxonomy-workflow.Rmd"
        self.assertTrue(workflow.is_file())
        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("taxonomy_result$tax", workflow_text)
        self.assertIn("taxonomy_result$boot", workflow_text)
        self.assertNotIn("taxonomy_result$taxa", workflow_text)
        self.assertIn("taxonomy <- taxonomy_result$tax", workflow_text)
        self.assertIn("bootstrap <- taxonomy_result$boot", workflow_text)
        self.assertNotIn("&lt;-", workflow_text)

    def test_reporting_has_worked_values_and_one_to_multi_sample_handoff(self):
        article = page("research-reporting-interpretation")
        workflow = (ROOT / "files/tutorial-examples/research-reporting-interpretation/research-reporting-workflow.Rmd").read_text(encoding="utf-8")
        for value in ("SYN_A", "90.0%", "SYN_B", "84.0%", "SYN_C", "93.0%"):
            self.assertIn(value, article)
            self.assertIn(value, workflow)
        self.assertIn("per-sample QC check", article)
        self.assertIn("independent biological replicates", article)
        self.assertIn("*.bam", article)
        self.assertIn("qc_summary_by_condition.csv", workflow)

    def test_humann_separates_abundance_and_version_specific_coverage(self):
        article = page("metatranscriptomics-functional-pathways")
        code = "\n".join(code_blocks("metatranscriptomics-functional-pathways"))
        self.assertIn("pathcoverage", article)
        self.assertIn("not the percentage of pathway reactions or enzymes", article)
        self.assertIn("retired in HUMAnN 4", article)
        self.assertIn("abundance_rpk", code)
        self.assertIn('sample = c("SYN_A", "SYN_B", "SYN_C")', code)

    def test_citeseq_records_versions_and_saves_pca_diagnostics(self):
        article = page("cite-seq-wnn-multiomics")
        code = "\n".join(code_blocks("cite-seq-wnn-multiomics"))
        self.assertIn("GSE100866", article)
        self.assertIn("R 4.3.3", article)
        self.assertIn("Seurat 5.0.1", article)
        self.assertNotIn("Seurat v4.3 example", article)
        self.assertIn("displayed calls follow the documented Seurat 5.0.1 API", article)
        self.assertIn("npcs = rna_npcs", code)
        self.assertIn('ElbowPlot(seurat_obj, reduction = "pca"', code)
        self.assertIn('ElbowPlot(seurat_obj, reduction = "apca"', code)
        self.assertIn("not a data-driven elbow choice", article)

    def test_hpc_removes_x11_custom_modulefiles_and_general_compression(self):
        article = page("hpc-submission-part1")
        for marker in ("optional-x11", "--x11", "optional-custom-modules",
                       "myprogram/1.0.lua", "optional-compression", "gzip my_file.txt",
                       "bzip2 my_file.txt", "xz my_file.txt"):
            self.assertNotIn(marker, article)
        self.assertIn("First-job route", article)

    def test_zotero_keeps_scope_caveat_but_removes_regex_exercise(self):
        article = page("mcp-zotero")
        self.assertIn("citation key", article.lower())
        for marker in ("find_keys.R", "find_keys.py", "gregexpr(", "re.findall(",
                       "zotero-citation-r", "zotero-citation-python"):
            self.assertNotIn(marker, article)
        groups = json.loads((ROOT / "tools/tutorial-code-groups.json").read_text(encoding="utf-8"))["tutorials"]
        self.assertNotIn("mcp-zotero", groups)

    def test_historical_restoration_is_full_hash_pinned_and_unknown_changes_survive(self):
        fixture = review_fixture()
        self.assertEqual(set(fixture), REVIEW_PATHS)
        self.assertEqual(sum(path.startswith("tutorials/") for path in REVIEW_PATHS), 12)
        for relative, entry in fixture.items():
            with self.subTest(path=relative):
                raw = (ROOT / relative).read_bytes()
                if relative.endswith(".html"):
                    restored = normalize_58_review(relative, raw.decode("utf-8")).encode("utf-8")
                    changed = raw.decode("utf-8") + "\n<!-- UNAPPROVED_REVIEW_TEST -->"
                    self.assertIn("UNAPPROVED_REVIEW_TEST", normalize_58_review(relative, changed))
                else:
                    restored = restore_58_review_asset(relative, raw)
                    changed = raw + b"\nUNAPPROVED_REVIEW_TEST"
                    self.assertIn(b"UNAPPROVED_REVIEW_TEST", restore_58_review_asset(relative, changed))
                self.assertEqual(hashlib.sha256(restored).hexdigest(), entry["base_sha256"])


if __name__ == "__main__":
    unittest.main()
