from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R_SCRIPT = shutil.which("Rscript")
FOUNDATION = ROOT / "files/tutorial-examples/foundation-model-evaluation"
PROTEIN = ROOT / "files/tutorial-examples/protein-structure-review"


def run_r(script: Path, *args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [R_SCRIPT, str(script), *(str(arg) for arg in args)],
        capture_output=True, text=True, timeout=30,
    )


@unittest.skipUnless(R_SCRIPT, "Rscript is required for executable R tutorial checks")
class FoundationEmbeddingRTests(unittest.TestCase):
    def test_synthetic_fixture_runs_real_donor_heldout_knn_and_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / "toy"
            result = run_r(
                FOUNDATION / "evaluate_embeddings.R",
                FOUNDATION / "synthetic_embeddings.csv",
                FOUNDATION / "synthetic_metadata.csv",
                prefix,
                1,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(f"{prefix}_predictions.csv", newline="", encoding="utf-8") as handle:
                predictions = list(csv.DictReader(handle))
            self.assertEqual({row["cell_id"]: row["prediction"] for row in predictions},
                             {"query_T": "T-cell", "query_B": "B-cell"})
            self.assertEqual({row["cell_id"]: row["truth"] for row in predictions},
                             {"query_T": "T-cell", "query_B": "B-cell"})
            with open(f"{prefix}_metrics.csv", newline="", encoding="utf-8") as handle:
                metrics = {(row["metric"], row["group"]): float(row["value"])
                           for row in csv.DictReader(handle)}
            self.assertEqual(metrics[("accuracy", "all")], 1.0)
            self.assertEqual(metrics[("macro_f1", "all")], 1.0)
            self.assertEqual(metrics[("donor_accuracy", "heldout_1")], 1.0)
            self.assertIn("inference_performed=false", result.stdout)

    def test_donor_leakage_stops_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            metadata = Path(temp) / "metadata.csv"
            metadata.write_text(
                "cell_id,donor_id,label,split\n"
                "query_B,reference_2,B-cell,test\n"
                "ref_B,reference_2,B-cell,train\n"
                "ref_T,reference_1,T-cell,train\n"
                "query_T,heldout_1,T-cell,test\n", encoding="utf-8"
            )
            prefix = Path(temp) / "leaky"
            result = run_r(
                FOUNDATION / "evaluate_embeddings.R",
                FOUNDATION / "synthetic_embeddings.csv", metadata, prefix, 1,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Donor leakage", result.stderr)
            self.assertFalse(Path(f"{prefix}_predictions.csv").exists())
            self.assertFalse(Path(f"{prefix}_metrics.csv").exists())

    def test_mismatched_ids_fail_instead_of_row_order_join(self):
        with tempfile.TemporaryDirectory() as temp:
            metadata = Path(temp) / "metadata.csv"
            metadata.write_text(
                "cell_id,donor_id,label,split\nother,d1,A,train\n", encoding="utf-8"
            )
            prefix = Path(temp) / "mismatch"
            result = run_r(
                FOUNDATION / "evaluate_embeddings.R",
                FOUNDATION / "synthetic_embeddings.csv", metadata, prefix, 1,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Cell ID mismatch", result.stderr)
            self.assertFalse(Path(f"{prefix}_predictions.csv").exists())

    def test_comparison_term_guard_stops_before_exact_knn_work(self):
        with tempfile.TemporaryDirectory() as temp:
            embeddings = Path(temp) / "embeddings.csv"
            metadata = Path(temp) / "metadata.csv"
            dims = [f"embedding_{i}" for i in range(10)]
            with embeddings.open("w", encoding="utf-8", newline="") as handle:
                handle.write("cell_id," + ",".join(dims) + "\n")
                for i in range(1000):
                    handle.write(f"ref{i}," + ",".join(["0"] * 10) + "\n")
                for i in range(1001):
                    handle.write(f"test{i}," + ",".join(["0.1"] * 10) + "\n")
            with metadata.open("w", encoding="utf-8", newline="") as handle:
                handle.write("cell_id,donor_id,label,split\n")
                for i in range(1000):
                    handle.write(f"ref{i},refdonor{i},A,train\n")
                for i in range(1001):
                    handle.write(f"test{i},testdonor{i},A,test\n")
            prefix = Path(temp) / "large"
            result = run_r(FOUNDATION / "evaluate_embeddings.R", embeddings, metadata, prefix, 1)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("10 million distance terms", result.stderr)
            self.assertFalse(Path(f"{prefix}_predictions.csv").exists())
            self.assertFalse(Path(f"{prefix}_metrics.csv").exists())


@unittest.skipUnless(R_SCRIPT, "Rscript is required for executable R tutorial checks")
class ProteinStructureRTests(unittest.TestCase):
    def test_offline_synthetic_pdb_inspection_reports_values_and_provenance_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix = Path(temp) / "fixture"
            result = run_r(
                PROTEIN / "inspect_alphafold.R", "analyze",
                PROTEIN / "synthetic_ca_fixture.pdb", prefix,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with open(f"{prefix}_summary.csv", newline="", encoding="utf-8") as handle:
                summary = {row["field"]: row["value"] for row in csv.DictReader(handle)}
            self.assertEqual(summary["ca_residue_count"], "3")
            self.assertEqual(summary["chains"], "A;B")
            self.assertEqual(float(summary["mean_ca_bfactor"]), 60.0)
            self.assertEqual(float(summary["min_ca_bfactor"]), 40.0)
            self.assertEqual(float(summary["max_ca_bfactor"]), 80.0)
            self.assertIn("provenance was not verified", summary["interpretation"])
            self.assertIn("experimental B-factors are not pLDDT", summary["interpretation"])
            with open(f"{prefix}_residues.csv", newline="", encoding="utf-8") as handle:
                residues = list(csv.DictReader(handle))
            self.assertEqual(len(residues), 3)
            self.assertEqual([row["residue_id"] for row in residues], ["1", "2", "1"])

    def test_unsupported_multiple_models_fail_without_report_files(self):
        atom = "ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 80.00           C\n"
        with tempfile.TemporaryDirectory() as temp:
            pdb = Path(temp) / "multiple.pdb"
            pdb.write_text("MODEL        1\n" + atom + "ENDMDL\nMODEL        2\n" + atom, encoding="ascii")
            prefix = Path(temp) / "bad"
            result = run_r(PROTEIN / "inspect_alphafold.R", "analyze", pdb, prefix)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("multiple MODEL", result.stderr)
            self.assertFalse(Path(f"{prefix}_residues.csv").exists())


class RFirstArticleContentTests(unittest.TestCase):
    def test_both_tutorials_link_r_downloads_fixtures_and_optional_python_routes(self):
        foundation = (ROOT / "tutorials/single-cell-foundation-models.html").read_text(encoding="utf-8")
        protein = (ROOT / "tutorials/protein-structure-design-alphafold.html").read_text(encoding="utf-8")
        for html, needles in (
            (foundation, ("base R", "evaluate_embeddings.R", "synthetic_embeddings.csv",
                         "synthetic_metadata.csv", "foundation_embedding_evaluation.Rmd",
                         "optional existing Python workflow", "donor-held-out")),
            (protein, ("R is the primary route", "inspect_alphafold.R", "synthetic_ca_fixture.pdb",
                       "protein_structure_review.Rmd", "Optional Python route", "jsonlite",
                       "Offline provenance is unverified")),
        ):
            for needle in needles:
                self.assertIn(needle, html)
            self.assertIn("class=\"language-r\"", html)
            self.assertIn("class=\"language-bash\"", html)
            self.assertNotIn("—", html)
            for href in re.findall(r'href="(\.\./files/[^\"]+)"', html):
                self.assertTrue((ROOT / "tutorials" / href).resolve().is_file(), href)
        self.assertIn("reject donor leakage", foundation)
        self.assertIn("does not predict a new structure", protein)
        for html, first, second in (
            (foundation, "foundation-embedding-r-run-stage", "foundation-embedding-python-run-stage"),
            (protein, "protein-structure-r-fetch-stage", "protein-structure-python-fetch-stage"),
            (protein, "protein-structure-r-local-stage", "protein-structure-python-local-stage"),
        ):
            r_block = re.search(r'<pre id="' + re.escape(first) + r'">.*?</pre>\s*', html, re.S)
            self.assertIsNotNone(r_block, first)
            self.assertTrue(html.startswith(f'<pre id="{second}">', r_block.end()), second)


if __name__ == "__main__":
    unittest.main()
