"""Verification tests for Phase C (Tier 2 major revisions) and Phase D (Tier 3 minor polish)."""
from pathlib import Path
import unittest

from phase_cd_fixes_baseline import (
    ASSET_PATHS,
    PAGE_PATHS,
    _base_bytes,
    normalize_phase_cd_fix,
    restore_phase_cd_asset,
)

ROOT = Path(__file__).resolve().parents[1]


def read_page(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class PhaseCDScientificUpgradeTests(unittest.TestCase):
    def test_single_cell_and_cancer_omics_depth_upgrades(self):
        deconv = read_page("tutorials/single-cell-deconvolution.html")
        self.assertIn("MAE unweighted=0.1227 | MAE weighted=0.0036", deconv)
        self.assertIn("BayesPrism", deconv)

        ccc = read_page("tutorials/cell-cell-communication.html")
        self.assertIn("liana_dotplot", ccc)
        self.assertIn("liana_bysample", ccc)

        tcr = read_page("tutorials/tcr-bcr-repertoire-analysis.html")
        self.assertIn("clonalDiversity", tcr)
        self.assertIn("clonalOverlap", tcr)
        self.assertIn("clonalOccupy", tcr)

        spatial = read_page("tutorials/spatial-transcriptomics-r-python.html")
        self.assertIn("moransi", spatial)
        self.assertIn("sq.gr.spatial_autocorr", spatial)
        self.assertIn("Visium HD", spatial)

        wes = read_page("tutorials/wes-variant-calling-pipeline.html")
        self.assertIn("Mutect2", wes)
        self.assertIn("BedToIntervalList", wes)
        self.assertIn("2.8-3.3", wes)

        cite = read_page("tutorials/cite-seq-wnn-multiomics.html")
        self.assertIn("DSBNormalizeProtein", cite)
        self.assertIn("Nature Methods", cite)

        cnv = read_page("tutorials/infercnv-copy-number-variation.html")
        self.assertIn("cnv_msq", cnv)
        self.assertIn("Numbat", cnv)

        pb_de = read_page("tutorials/transcriptomics-differential-expression.html")
        self.assertIn("design    = ~ donor + condition", pb_de)
        self.assertIn('type = "apeglm"', pb_de)

    def test_workflows_foundations_microbiome_and_ai_upgrades(self):
        wf = read_page("tutorials/reproducible-workflows-snakemake-nextflow.html")
        self.assertIn("rule summarize_sample:", wf)
        self.assertIn("rule merge_cohort:", wf)

        stats = read_page("tutorials/statistics-for-bioinformatics.html")
        self.assertIn("t = 3.9885", stats)
        self.assertIn("df = 5.9679", stats)

        mamba = read_page("tutorials/conda-mamba-part1.html")
        self.assertIn("R --no-echo", mamba)
        self.assertNotIn("R --slave", mamba)
        self.assertIn('eval "$(micromamba shell hook -s bash)"', mamba)
        self.assertNotIn("/tmp/micromamba-hook.sh", mamba)

        orthofinder = read_page("tutorials/phylogenomics-orthofinder.html")
        self.assertIn("primary_transcript.py", orthofinder)
        self.assertIn("ASTRAL-Pro", orthofinder)

        assembly = read_page("tutorials/metagenomics-assembly-mapping.html")
        self.assertIn("seqkit stats -a spades_output/contigs.fasta", assembly)
        self.assertIn("samtools coverage", assembly)

        ai_sc = read_page("tutorials/advanced-ai-single-cell.html")
        self.assertIn("TRAC", ai_sc)
        self.assertIn('de.method = "wilcox"', ai_sc)

        for rel in PAGE_PATHS:
            self.assertNotIn("\u2014", read_page(rel), rel)


class PhaseCDBaselineTests(unittest.TestCase):
    def test_phase_cd_pages_and_assets_restore_cleanly_and_detect_mutations(self):
        for rel in PAGE_PATHS:
            with self.subTest(page=rel):
                current = read_page(rel)
                base = _base_bytes(rel).decode("utf-8")
                restored = normalize_phase_cd_fix(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(normalize_phase_cd_fix(rel, restored), restored)
                mutated = current.replace("<title>", "<title>Mutated ", 1)
                self.assertEqual(normalize_phase_cd_fix(rel, mutated), mutated)

        for rel in ASSET_PATHS:
            with self.subTest(asset=rel):
                current = (ROOT / rel).read_bytes()
                base = _base_bytes(rel)
                restored = restore_phase_cd_asset(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(restore_phase_cd_asset(rel, restored), restored)
                mutated = current + b"\n"
                self.assertEqual(restore_phase_cd_asset(rel, mutated), mutated)


if __name__ == "__main__":
    unittest.main()
