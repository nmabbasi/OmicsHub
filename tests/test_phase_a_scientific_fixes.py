"""Regression and scientific correctness tests for Phase A tutorial fixes."""
from html import unescape
from pathlib import Path
import re
import unittest

from phase_a_fixes_baseline import (
    ASSET_PATHS,
    PAGE_PATHS,
    _base_bytes,
    normalize_phase_a_fix,
    restore_phase_a_asset,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S)


def read_page(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def code_blocks(rel: str) -> list[str]:
    return [unescape(m) for m in CODE_BLOCK.findall(read_page(rel))]


class PhaseAScientificCorrectnessTests(unittest.TestCase):
    def test_illumina_fastq_header_is_escaped_and_concrete(self):
        text = read_page("tutorials/computer-data-fundamentals.html")
        self.assertIn("&lt;instrument&gt;:&lt;run&gt;", text)
        self.assertNotIn("@<instrument>:", text)
        self.assertIn("@A00123:8:H5KJ7DSXX:1:1101:10004:1000 1:N:0:ACGTACGT", text)
        self.assertIn("30x human whole-genome paired-end dataset", text)

    def test_liana_uses_r_idents_col_not_python_groupby(self):
        text = read_page("tutorials/cell-cell-communication.html")
        self.assertIn('idents_col = "cell_type"', text)
        self.assertNotIn('liana_wrap(\n  seurat_obj,\n  groupby = "cell_type"', text)

    def test_sortmerna_paired_flags_and_humann_subdirectories(self):
        mt_guide = "\n".join(code_blocks("tutorials/metatranscriptomics-guide.html"))
        self.assertIn("--out2", mt_guide)
        self.assertIn("--other sortmerna_work/non_rRNA_reads", mt_guide)
        self.assertIn("sortmerna_work/non_rRNA_reads_fwd.fq.gz", mt_guide)

        mt_func = "\n".join(code_blocks("tutorials/metatranscriptomics-functional-pathways.html"))
        self.assertEqual(mt_func.count("--search-subdirectories"), 2)

    def test_docker_bwa_indexes_in_container_and_uses_60bp_reads(self):
        blocks = "\n".join(code_blocks("tutorials/docker-singularity-bioinformatics.html"))
        self.assertNotIn("\nbwa index reference.fa", blocks)
        self.assertIn('"$IMAGE" bwa index reference.fa', blocks)
        self.assertIn("ACGTTGCAAGTCCTAGGATCCGATGCTAACGTAGCTTAGGCTAACCGTTGCATGACCTGA", blocks)

    def test_vibe_coding_definition_and_clr_margin_default(self):
        prompt_page = read_page("tutorials/ai-prompt-engineering-seurat.html")
        self.assertIn("unreviewed", prompt_page.lower())
        cite_page = read_page("tutorials/cite-seq-wnn-multiomics.html")
        self.assertIn("margin = 1", cite_page)
        self.assertNotIn("margin = 2 (default)", cite_page)

    def test_gencode_primary_assembly_and_wes_split_variant_filtration(self):
        ref_page = read_page("tutorials/reference-genomes-annotation.html")
        self.assertIn("primary_assembly", ref_page)
        self.assertIn("MANE Select", ref_page)
        self.assertIn("T2T-CHM13", ref_page)

        wes_blocks = "\n".join(code_blocks("tutorials/wes-variant-calling-pipeline.html"))
        self.assertIn("SelectVariants", wes_blocks)
        self.assertIn("--select-type-to-include SNP", wes_blocks)
        self.assertIn("--select-type-to-include INDEL", wes_blocks)
        self.assertIn("MergeVcfs", wes_blocks)

    def test_volcano_padj_zero_underflow_guidance(self):
        vis_page = read_page("tutorials/data-visualization-fundamentals.html")
        self.assertIn("underflow", vis_page.lower())

    def test_no_leaked_revision_notes_remain_in_phase_a_pages(self):
        leaked_phrases = (
            "The original page's command used isoquant.py",
            "The source example's single-read BWA command",
            "The original workflow called total_counts / 1e6",
            "The following original Python instructions are retained.",
        )
        for rel in PAGE_PATHS:
            text = read_page(rel)
            self.assertNotIn("\u2014", text, rel)
            for phrase in leaked_phrases:
                self.assertNotIn(phrase, text, f"{phrase!r} leaked in {rel}")

    def test_cross_page_conda_and_gitignore_consistency_and_slurm_commands(self):
        hpc_sub = read_page("tutorials/hpc-submission-part1.html")
        self.assertIn("Miniforge3", hpc_sub)
        self.assertIn("conda-forge", hpc_sub)
        self.assertNotIn("repo.anaconda.com/miniconda", hpc_sub)

        for rel in ("tutorials/git-github-bioinformatics.html", "tutorials/reproducible-project-structure.html"):
            txt = read_page(rel)
            self.assertIn("envs/*/", txt)
            self.assertIn("!envs/*.yml", txt)

        slurm_basic = read_page("tutorials/hpc-basic-commands.html")
        for cmd in ("scancel", "scontrol show job", "MaxRSS", "srun --nodes=1"):
            self.assertIn(cmd, slurm_basic)


class PhaseABaselineTests(unittest.TestCase):
    def test_phase_a_pages_and_assets_restore_cleanly_and_detect_mutations(self):
        for rel in PAGE_PATHS:
            with self.subTest(page=rel):
                current = read_page(rel)
                base = _base_bytes(rel).decode("utf-8")
                restored = normalize_phase_a_fix(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(normalize_phase_a_fix(rel, restored), restored)
                mutated = current.replace("<title>", "<title>Mutated ", 1)
                self.assertEqual(normalize_phase_a_fix(rel, mutated), mutated)

        for rel in ASSET_PATHS:
            with self.subTest(asset=rel):
                current = (ROOT / rel).read_bytes()
                base = _base_bytes(rel)
                restored = restore_phase_a_asset(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(restore_phase_a_asset(rel, restored), restored)
                mutated = current + b"\n"
                self.assertEqual(restore_phase_a_asset(rel, mutated), mutated)


if __name__ == "__main__":
    unittest.main()
