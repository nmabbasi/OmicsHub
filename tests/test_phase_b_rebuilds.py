"""Regression and execution tests for Phase B Tier 1 rebuilds and AI/Python upgrades."""
from html import unescape
from pathlib import Path
import re
import subprocess
import sys
import unittest

from phase_b_fixes_baseline import (
    ASSET_PATHS,
    PAGE_PATHS,
    _base_bytes,
    normalize_phase_b_fix,
    restore_phase_b_asset,
)

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S)


def read_page(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def code_blocks(rel: str) -> list[str]:
    return [unescape(m) for m in CODE_BLOCK.findall(read_page(rel))]


class PhaseBRebuildsTests(unittest.TestCase):
    def test_no_em_dashes_across_phase_b_pages(self):
        for rel in PAGE_PATHS:
            self.assertNotIn("\u2014", read_page(rel), rel)

    def test_scrna_qc_covers_pre_integration_cell_qc_and_pbmc_silhouette(self):
        text = read_page("tutorials/scrna-seq-quality-control.html")
        for item in ("emptyDrops", "scDblFinder", "SoupX", "CellBender", "898.5", "1597.0", "0.2731", "0.3410"):
            self.assertIn(item, text)

    def test_scrna_downstream_covers_five_branches_and_decoupler_v2(self):
        text = read_page("tutorials/scrna-seq-downstream-analysis.html")
        for item in ("scCODA", "miloR", "dc.mt.mlm", "score_mlm", "Version-stripped overlap: 3/4", "0.167"):
            self.assertIn(item, text)

    def test_methods_guide_and_long_read_cover_design_rank_and_cancer_genomics(self):
        methods = read_page("tutorials/modern-bioinformatics-methods-2026.html")
        self.assertIn("Confounded design: ncol=3, rank=2, estimable=FALSE", methods)
        self.assertIn("Squair et al. (2021)", methods)

        lr = read_page("tutorials/long-read-pacbio-nanopore.html")
        for item in ("sniffles", "--mosaic", "Clair3", "WhatsHap", "modkit pileup", "MLH1"):
            self.assertIn(item, lr)

    def test_project_structure_and_alphafold_upgrades(self):
        proj = read_page("tutorials/reproducible-project-structure.html")
        self.assertIn("config/samples.tsv", proj)
        self.assertIn("config/data_dictionary.tsv", proj)
        self.assertIn("renv::install", proj)

        prot = read_page("tutorials/protein-structure-design-alphafold.html")
        for item in ("extract_ca_bfactors", "paeDocUrl", "His88", "color bfactor palette alphafold"):
            self.assertIn(item, prot)

    def test_clinvar_state_machine_and_mcp_sqlite_scripts_execute_cleanly(self):
        orch_blocks = code_blocks("tutorials/advanced-ai-orchestration-bioinformatics.html")
        py_state = next(b for b in orch_blocks if "VCV000017661" in b and "def run_packet" in b)
        res = subprocess.run([sys.executable, "-c", py_state], capture_output=True, text=True, check=True)
        self.assertIn("Valid draft status: human_review_ready | attempts: 1", res.stdout)
        self.assertIn("halted_retry_cap_reached | attempts: 3", res.stdout)

        mcp_blocks = code_blocks("tutorials/mcp-zotero.html")
        py_mcp = next(b for b in mcp_blocks if "sqlite3" in b and "MCP-test-20261118" in b)
        res_mcp = subprocess.run([sys.executable, "-c", py_mcp], capture_output=True, text=True, check=True)
        self.assertIn("['zotero_delete_item']", res_mcp.stdout)
        self.assertIn("K9X2ABCD", res_mcp.stdout)
        self.assertNotIn("P7M4ZZZZ", res_mcp.stdout)

    def test_python_fundamentals_is_python_first_and_steps_execute(self):
        py_page = read_page("tutorials/python-fundamentals-bioinformatics.html")
        self.assertNotIn("Primary route: FASTA statistics in base R", py_page)
        self.assertIn("Step 1: Strings, slicing, and reverse complements", py_page)
        self.assertIn("Step 4: Why generators", py_page)
        blocks = code_blocks("tutorials/python-fundamentals-bioinformatics.html")
        for idx in (0, 2, 4):
            res = subprocess.run([sys.executable, "-c", blocks[idx]], capture_output=True, text=True, check=True)
            self.assertTrue(res.stdout.strip())

    def test_copilot_cursor_and_foundation_model_upgrades(self):
        copilot = read_page("tutorials/ai-bioinformatics-github-copilot.html")
        self.assertIn("3. Configure VS Code Copilot Chat and repository instructions", copilot)
        self.assertIn(".github/copilot-instructions.md", copilot)

        cursor = read_page("tutorials/ai-coding-cursor-aider.html")
        self.assertIn(".cursor/rules/bioinformatics.mdc", cursor)
        self.assertIn("--test-cmd", cursor)

        fm = read_page("tutorials/single-cell-foundation-models.html")
        self.assertIn("0.9499", fm)
        self.assertIn("0.8422", fm)
        self.assertIn("Kedzierska et al. (2025)", fm)


class PhaseBBaselineTests(unittest.TestCase):
    def test_phase_b_pages_and_assets_restore_cleanly_and_detect_mutations(self):
        for rel in PAGE_PATHS:
            with self.subTest(page=rel):
                current = read_page(rel)
                base = _base_bytes(rel).decode("utf-8")
                restored = normalize_phase_b_fix(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(normalize_phase_b_fix(rel, restored), restored)
                mutated = current.replace("<title>", "<title>Mutated ", 1)
                self.assertEqual(normalize_phase_b_fix(rel, mutated), mutated)

        for rel in ASSET_PATHS:
            with self.subTest(asset=rel):
                current = (ROOT / rel).read_bytes()
                base = _base_bytes(rel)
                restored = restore_phase_b_asset(rel, current)
                self.assertEqual(restored, base)
                self.assertEqual(restore_phase_b_asset(rel, restored), restored)
                mutated = current + b"\n"
                self.assertEqual(restore_phase_b_asset(rel, mutated), mutated)


if __name__ == "__main__":
    unittest.main()
