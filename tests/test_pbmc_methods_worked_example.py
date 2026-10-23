"""Offline integrity tests: no network or R installation required by this suite."""
from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import statistics
import struct
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "files/pbmc-methods-worked-example"
OBSERVED = EXAMPLE / "observed"
SPEC = importlib.util.spec_from_file_location("pbmc_prepare_inputs", EXAMPLE / "prepare_inputs.py")
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


def rows(name):
    with (OBSERVED / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


class PublicInputPreparerTests(unittest.TestCase):
    def setUp(self):
        # Software-unit fixture bytes, never used as biological analysis input.
        self.content = b"checksum unit test fixture\n"
        self.source = {"filename": "unit-fixture.bin", "url": "https://example.invalid/fixture",
                       "bytes": len(self.content), "sha256": hashlib.sha256(self.content).hexdigest()}

    def test_cached_input_is_verified_and_idempotent_without_network(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(PREPARE, "urlopen", side_effect=AssertionError("unexpected network")):
            root = Path(temporary)
            cache = root / "cache.bin"
            cache.write_bytes(self.content)
            target = PREPARE.prepare(root / "data", self.source, cache)
            self.assertEqual(target.read_bytes(), self.content)
            self.assertEqual(PREPARE.prepare(root / "data", self.source), target)

    def test_existing_mismatched_input_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / self.source["filename"]
            original = b"x" * len(self.content)
            target.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                PREPARE.prepare(root, self.source)
            self.assertEqual(target.read_bytes(), original)

    def test_failed_download_is_not_published(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(PREPARE, "urlopen", return_value=io.BytesIO(b"bad input")):
            root = Path(temporary)
            with self.assertRaises(ValueError):
                PREPARE.prepare(root, self.source)
            self.assertEqual(list(root.iterdir()), [])

    def test_manifest_rejects_parent_path_and_non_https(self):
        with tempfile.TemporaryDirectory() as temporary:
            for changed in ({"filename": "../escaped.bin"}, {"url": "file:///tmp/input"}):
                with self.assertRaises(ValueError):
                    PREPARE.prepare(Path(temporary), dict(self.source, **changed))


class PbmcWorkedExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((EXAMPLE / "inputs.json").read_text())
        cls.summary = json.loads((OBSERVED / "run_summary.json").read_text())
        cls.cells = rows("selected_cells.csv")
        cls.annotations = rows("annotation.csv")
        cls.lisi = rows("lisi_per_cell.csv")

    def test_provenance_and_source_fingerprint(self):
        data = self.manifest["data_package"]
        self.assertEqual(data["package_version"], "3.0.0")
        self.assertEqual(data["package_declared_license"], "CC BY 4.0")
        self.assertEqual(data["bytes"], 58634290)
        self.assertEqual(self.summary["dataset"]["sha256"], data["sha256"])
        self.assertEqual(self.summary["dataset"]["script_sha256"], hashlib.sha256((EXAMPLE / "run_example.R").read_bytes()).hexdigest())
        for check in ("public_only", "reference_query_cell_ids_disjoint", "reference_query_count_profiles_disjoint", "detected_gene_metadata_matches_counts", "rna_counts_unchanged"):
            self.assertIs(self.summary["dataset"][check], True)
        for source in self.manifest["r_sources"]:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertRegex(source["sha256"], r"^[a-f0-9]{64}$")
        self.assertEqual(self.manifest["tested_direct_versions"]["harmony"], "1.2.3")
        self.assertEqual(self.manifest["tested_direct_versions"]["scran"], "1.30.2")

    def test_selected_roles_are_disjoint_and_capped_before_scoring(self):
        self.assertEqual(len(self.cells), len({r["cell_id"] for r in self.cells}))
        query = [r for r in self.cells if r["role"] == "query"]
        reference = [r for r in self.cells if r["role"] == "reference"]
        self.assertEqual(len(query), self.summary["filter"]["selected_query_cells"])
        self.assertEqual(len(reference), self.summary["filter"]["selected_reference_cells"])
        self.assertTrue({r["cell_id"] for r in query}.isdisjoint({r["cell_id"] for r in reference}))
        self.assertTrue({r["counts_sha256"] for r in query}.isdisjoint({r["counts_sha256"] for r in reference}))
        counts = Counter((r["role"], r["batch"], r["source_label"]) for r in self.cells)
        self.assertLessEqual(max(counts.values()), 80)
        self.assertTrue(all(int(r["detected_genes"]) > 200 for r in self.cells))
        self.assertTrue(all(r["source_label"] not in ("", "Unknown", "Unassigned") for r in self.cells))
        self.assertEqual({r["batch"] for r in query}, set(self.manifest["predeclared_design"]["query_methods"]))
        self.assertEqual({r["batch"] for r in reference}, {self.manifest["predeclared_design"]["reference_method"]})
        self.assertEqual({r["cell_id"] for r in query}, {r["cell_id"] for r in self.annotations})
        self.assertFalse(any(r["batch"] == "10x Chromium (v3)" and r["source_label"] == "Plasmacytoid dendritic cell" for r in query))

    def test_annotation_counts_and_uncertainty_fields(self):
        self.assertEqual(len(self.annotations), len({r["cell_id"] for r in self.annotations}))
        disagreement = sum(r["SingleR_pruned_label"] != r["Seurat_predicted_label"] for r in self.annotations)
        unassigned = sum(r["SingleR_pruned_label"] == "Unassigned" for r in self.annotations)
        self.assertEqual(disagreement, self.summary["annotation"]["grouped_disagreement_cells"])
        self.assertEqual(unassigned, self.summary["annotation"]["pruned_singleR_unassigned_n"])
        self.assertEqual(sum(int(r["n"]) for r in rows("annotation_grouped_counts.csv")), len(self.annotations))
        for row in self.annotations:
            self.assertTrue(math.isfinite(float(row["SingleR_delta_next"])))
            self.assertTrue(0 <= float(row["Seurat_prediction_score_max"]) <= 1 + 1e-12)

    def test_lisi_same_cells_metadata_and_raw_bounds(self):
        annotation = {r["cell_id"]: r for r in self.annotations}
        label_count = len({r["source_label"] for r in self.annotations})
        for reduction in ("PCA", "Harmony"):
            subset = [r for r in self.lisi if r["reduction"] == reduction]
            self.assertEqual([r["cell_id"] for r in subset], [r["cell_id"] for r in self.annotations])
            for row in subset:
                self.assertEqual(row["batch"], annotation[row["cell_id"]]["group"])
                self.assertEqual(row["source_label"], annotation[row["cell_id"]]["source_label"])
                # Keep saved raw scores; allow only a tiny floating-point overshoot.
                self.assertTrue(1 - 1e-6 <= float(row["iLISI_batch"]) <= 2 + 1e-6)
                self.assertTrue(1 - 1e-6 <= float(row["cLISI_source_label"]) <= label_count + 1e-6)
            embeddings = rows(f"embeddings_{reduction.lower()}.csv")
            self.assertEqual([r["cell_id"] for r in embeddings], [r["cell_id"] for r in self.annotations])
            self.assertTrue(all(len(r) == 21 for r in embeddings))

    def test_published_quartiles_and_paired_changes_recompute(self):
        for result in rows("lisi_summary.csv"):
            subset = [r for r in self.lisi if r["reduction"] == result["reduction"]]
            if result["stratum"] != "overall":
                subset = [r for r in subset if r[result["stratum"]] == result["group"]]
            values = [float(r[result["metric"]]) for r in subset]
            self.assertEqual(len(values), int(result["n"]))
            for field, probability in (("q25", .25), ("median", .5), ("q75", .75)):
                self.assertAlmostEqual(float(result[field]), quantile(values, probability), places=10)
        lookup = {(r["cell_id"], r["reduction"]): r for r in self.lisi}
        for row in rows("lisi_paired_differences.csv"):
            for metric in ("iLISI_batch", "cLISI_source_label"):
                expected = float(lookup[row["cell_id"], "Harmony"][metric]) - float(lookup[row["cell_id"], "PCA"][metric])
                self.assertAlmostEqual(float(row[f"delta_{metric}_Harmony_minus_PCA"]), expected, places=10)

    def test_figures_and_reproduction_check_are_real_outputs(self):
        for filename in ("annotation_confusion.png", "marker_dotplot.png", "lisi_distributions.png", "umap_before_after.png"):
            content = (OBSERVED / filename).read_bytes()
            self.assertEqual(content[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", content[16:24])
            self.assertGreaterEqual(width, 1000)
            self.assertGreaterEqual(height, 800)
            self.assertGreater(len(content), 10000)
        check = json.loads((OBSERVED / "reproduction_check.json").read_text())
        self.assertEqual(check["successful_runs"], 2)
        self.assertTrue(check["identical_csvs"])
        self.assertEqual(check["different_csvs"], [])

    def test_bundle_and_hands_on_promises(self):
        archive = ROOT / "downloads/pbmc-methods-worked-example.zip"
        with zipfile.ZipFile(archive) as bundle:
            for relative in ("run_example.R", "prepare_inputs.py", "inputs.json", "README.md", "observed/run_summary.json", "observed/selected_cells.csv"):
                member = "pbmc-methods-worked-example/" + relative
                self.assertEqual(bundle.read(member), (EXAMPLE / relative).read_bytes())
            self.assertFalse(any(name.endswith((".rds", ".rda", ".tar.gz")) for name in bundle.namelist()))
        for filename in ("cell-type-annotation-methods.html", "scrna-seq-integration-strategies.html"):
            html = (ROOT / "tutorials" / filename).read_text()
            self.assertIn('data-tutorial-format="hands-on-lab"', html)
            self.assertIn("pbmc-methods-worked-example.zip", html)
            self.assertIn("source-label", html)
            self.assertIn("not independent", html)
            self.assertNotIn("@@", html)
            self.assertNotIn("your_dataset.rds", html)
            self.assertNotIn("public-plant-dotplot", html)


if __name__ == "__main__":
    unittest.main()
