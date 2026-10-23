"""Execute the actual language branches displayed in two tutorial articles.

Run with: python3 -m unittest tests.test_walkthrough_language_branches -v
Python science-package branches are skipped when their optional dependencies are
not present. Tests use only invented fixtures and never install packages/network.
"""
from __future__ import annotations

import csv
import importlib.util
from html import unescape
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK = re.compile(r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", re.S)
STATS_PAGE = ROOT / "tutorials/statistics-for-bioinformatics.html"
DESIGN_PAGE = ROOT / "tutorials/experimental-design-batch-effects.html"


def blocks(path: Path) -> list[str]:
    return [unescape(block) for block in CODE_BLOCK.findall(path.read_text(encoding="utf-8"))]


def find_block(path: Path, *needles: str) -> str:
    matches = [block for block in blocks(path) if all(needle in block for needle in needles)]
    if len(matches) != 1:
        raise AssertionError(f"Expected one displayed code block containing {needles}, got {len(matches)}")
    return matches[0]


def fixture_from_block(block: str, filename: str) -> str:
    match = re.search(rf"cat > {re.escape(filename)} <<'EOF'\n(.*?)\nEOF", block, re.S)
    if not match:
        raise AssertionError(f"Could not find the displayed {filename} fixture")
    return match.group(1) + "\n"


def run_script(executable: str, source: str, filename: str, directory: Path,
               *arguments: str) -> subprocess.CompletedProcess[str]:
    script = directory / filename
    script.write_text(source, encoding="utf-8")
    return subprocess.run(
        [executable, str(script), *arguments], cwd=directory,
        capture_output=True, text=True, check=False,
    )


def has_packages(*names: str) -> bool:
    return all(importlib.util.find_spec(name) is not None for name in names)


CONTROL = "value\n8.9\n9.8\n10.4\n9.5\n"
TREATED = "value\n11.2\n10.7\n12.1\n11.4\n"
PVALUES = "0.01\n0.04\n0.20\n0.80\n"


class StatisticsLanguageBranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python_welch = find_block(STATS_PAGE, "from scipy import stats", "compare_groups.py")
        cls.r_welch = find_block(STATS_PAGE, "t.test(trt, ctrl", "compare_groups.R")
        cls.python_bh = find_block(STATS_PAGE, "from statsmodels.stats.multitest", "pvalues_adjusted.txt")
        cls.r_bh = find_block(STATS_PAGE, "p.adjust(pvals, method = \"BH\")", "discoveries_fdr05.txt")
        cls.rscript = shutil.which("Rscript")

    def prepare_groups(self, directory: Path):
        (directory / "data").mkdir()
        (directory / "data/control.csv").write_text(CONTROL, encoding="utf-8")
        (directory / "data/treated.csv").write_text(TREATED, encoding="utf-8")

    @unittest.skipUnless(has_packages("numpy", "pandas", "scipy"), "optional NumPy, pandas, and SciPy are required")
    def test_displayed_python_welch_script_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare_groups(directory)
            result = run_script(sys.executable, self.python_welch, "compare_groups.py", directory,
                                "data/control.csv", "data/treated.csv", "results")
            self.assertEqual(result.returncode, 0, result.stderr)
            with (directory / "results/comparison.csv").open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["n_control"], "4")
            self.assertAlmostEqual(float(row["mean_difference_treated_minus_control"]), 1.7)
            self.assertLess(float(row["ci95_low"]), float(row["ci95_high"]))

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_displayed_base_r_welch_script_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare_groups(directory)
            result = run_script(self.rscript, self.r_welch, "compare_groups.R", directory,
                                "data/control.csv", "data/treated.csv", "results")
            self.assertEqual(result.returncode, 0, result.stderr)
            with (directory / "results/comparison_R.csv").open(newline="", encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["n_control"], "4")
            self.assertAlmostEqual(float(row["mean_difference_treated_minus_control"]), 1.7)
            self.assertLess(float(row["ci95_low"]), float(row["ci95_high"]))

    @unittest.skipUnless(has_packages("numpy", "pandas", "scipy"), "optional NumPy, pandas, and SciPy are required")
    def test_python_welch_rejects_bad_nonblank_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare_groups(directory)
            (directory / "data/control.csv").write_text("value\n1\nbad\n3\n", encoding="utf-8")
            result = run_script(sys.executable, self.python_welch, "compare_groups.py", directory,
                                "data/control.csv", "data/treated.csv", "results")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not numeric", result.stderr)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_r_welch_rejects_bad_nonblank_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare_groups(directory)
            (directory / "data/control.csv").write_text("value\n1\nbad\n3\n", encoding="utf-8")
            result = run_script(self.rscript, self.r_welch, "compare_groups.R", directory,
                                "data/control.csv", "data/treated.csv", "results")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not numeric", result.stderr)

    @unittest.skipUnless(has_packages("numpy", "statsmodels"), "optional NumPy and statsmodels are required")
    def test_python_bh_preserves_family_order_and_expected_values(self):
        self._check_bh(sys.executable, self.python_bh, "adjust_features.py")

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_base_r_bh_preserves_family_order_and_expected_values(self):
        self._check_bh(self.rscript, self.r_bh, "adjust_features.R")

    def _check_bh(self, executable, source, filename):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("Bash required for the displayed shared fixture setup")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            setup = find_block(STATS_PAGE, 'printf "0.01')
            prepared = subprocess.run([bash, "-c", setup], cwd=directory,
                                      capture_output=True, text=True, check=False)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertEqual((directory / "pvalues_all_features.txt").read_text(), PVALUES)
            result = run_script(executable, source, filename, directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            adjusted = [float(value) for value in (directory / "pvalues_adjusted.txt").read_text().split()]
            rejected = [int(value) for value in (directory / "discoveries_fdr05.txt").read_text().split()]
            for observed, expected in zip(adjusted, [0.04, 0.08, 0.2666666667, 0.8]):
                self.assertAlmostEqual(observed, expected, places=7)
            self.assertEqual(rejected, [1, 0, 0, 0])

    def test_multiple_testing_input_is_shared_before_either_language_branch(self):
        text = STATS_PAGE.read_text(encoding="utf-8")
        shared = text.index('id="statistics-bh-shared-input"')
        self.assertLess(shared, text.index('<h3>Python with statsmodels</h3>'))
        self.assertLess(shared, text.index('<h3>Base R with p.adjust</h3>'))
        self.assertNotIn("python", find_block(STATS_PAGE, 'printf "0.01').lower())

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_base_r_bh_rejects_out_of_range_p_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "pvalues_all_features.txt").write_text("0.1\n1.2\n", encoding="utf-8")
            result = run_script(self.rscript, self.r_bh, "adjust_features.R", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("between 0 and 1", result.stderr)

    @unittest.skipUnless(has_packages("numpy", "statsmodels"), "optional NumPy and statsmodels are required")
    def test_python_bh_rejects_out_of_range_p_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "pvalues_all_features.txt").write_text("0.1\n1.2\n", encoding="utf-8")
            result = run_script(sys.executable, self.python_bh, "adjust_features.py", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("between 0 and 1", result.stderr)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_base_r_bh_rejects_blank_p_value_line(self):
        self._assert_blank_p_value_rejected(self.rscript, self.r_bh, "adjust_features.R")

    @unittest.skipUnless(has_packages("numpy", "statsmodels"), "optional NumPy and statsmodels are required")
    def test_python_bh_rejects_blank_p_value_line(self):
        self._assert_blank_p_value_rejected(sys.executable, self.python_bh, "adjust_features.py")

    def _assert_blank_p_value_rejected(self, executable, source, filename):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "pvalues_all_features.txt").write_text("0.1\n\n0.2\n", encoding="utf-8")
            result = run_script(executable, source, filename, directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonblank", result.stderr)


class ExperimentalDesignLanguageBranchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python_metadata = find_block(DESIGN_PAGE, "import pandas as pd", "required = [\"sample_id\"")
        cls.r_metadata = find_block(DESIGN_PAGE, "meta <- read.csv(\"metadata.csv\"", "required <- c(\"sample_id\"")
        cls.r_pca = find_block(DESIGN_PAGE, "counts_df <- read.csv(\"counts.csv\"", "prcomp(")
        cls.python_pca = find_block(DESIGN_PAGE, "import csv", "np.linalg.svd", "pca_coordinates.csv")
        cls.rscript = shutil.which("Rscript")
        cls.metadata_csv = fixture_from_block(find_block(DESIGN_PAGE, "cat > metadata.csv"), "metadata.csv")
        cls.counts_csv = fixture_from_block(find_block(DESIGN_PAGE, "cat > counts.csv"), "counts.csv")

    def prepare(self, directory: Path, metadata=None, counts=None):
        (directory / "metadata.csv").write_text(metadata or self.metadata_csv, encoding="utf-8")
        (directory / "counts.csv").write_text(counts or self.counts_csv, encoding="utf-8")

    def run_metadata(self, directory: Path, language: str):
        source = self.python_metadata if language == "python" else self.r_metadata
        executable = sys.executable if language == "python" else self.rscript
        name = "validate_metadata.py" if language == "python" else "validate_metadata.R"
        return run_script(executable, source, name, directory)

    def assert_metadata_success(self, result, directory: Path):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((directory / "metadata.validated.csv").exists())
        self.assertIn("Lane1", result.stdout)
        with (directory / "metadata.validated.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([row["sample_id"] for row in rows], ["S01", "S02", "S03", "S04"])

    @unittest.skipUnless(has_packages("pandas"), "optional pandas is required")
    def test_displayed_python_metadata_validator_runs_on_shared_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_metadata_success(self.run_metadata(directory, "python"), directory)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_displayed_base_r_metadata_validator_runs_on_shared_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_metadata_success(self.run_metadata(directory, "r"), directory)

    @unittest.skipUnless(has_packages("pandas"), "optional pandas is required")
    def test_python_metadata_validator_rejects_duplicate_sample_ids(self):
        self._assert_duplicate_rejected("python")

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_r_metadata_validator_rejects_duplicate_sample_ids(self):
        self._assert_duplicate_rejected("r")

    def _assert_duplicate_rejected(self, language):
        duplicate = self.metadata_csv.replace("S04,Donor04", "S01,Donor04")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory, metadata=duplicate)
            result = self.run_metadata(directory, language)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Duplicate sample_id", result.stderr)

    @unittest.skipUnless(has_packages("pandas"), "optional pandas is required")
    def test_python_metadata_validator_rejects_blank_required_value(self):
        self._assert_blank_metadata_rejected("python")

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_r_metadata_validator_rejects_blank_required_value(self):
        self._assert_blank_metadata_rejected("r")

    def _assert_blank_metadata_rejected(self, language):
        metadata = self.metadata_csv.replace("S01,Donor01,control", "S01,   ,control")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory, metadata=metadata)
            result = self.run_metadata(directory, language)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing or blank values in experimental_unit", result.stderr)

    def run_pca(self, directory: Path, language: str, counts=None):
        metadata_result = self.run_metadata(directory, language)
        self.assert_metadata_success(metadata_result, directory)
        if counts is not None:
            (directory / "counts.csv").write_text(counts, encoding="utf-8")
        source = self.python_pca if language == "python" else self.r_pca
        executable = sys.executable if language == "python" else self.rscript
        name = "pca.py" if language == "python" else "pca.R"
        return run_script(executable, source, name, directory)

    def assert_pca_success(self, result, directory: Path):
        self.assertEqual(result.returncode, 0, result.stderr)
        with (directory / "pca_coordinates.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            self.assertTrue({"PC1", "PC2", "sample_id", "condition", "batch"}.issubset(reader.fieldnames))
        self.assertEqual([row["sample_id"] for row in rows], ["S01", "S02", "S03", "S04"])
        expected = {"S01": ("control", "Lane1"), "S02": ("control", "Lane2"),
                    "S03": ("treated", "Lane1"), "S04": ("treated", "Lane2")}
        for row in rows:
            self.assertTrue(float(row["PC1"]) == float(row["PC1"]))
            self.assertTrue(float(row["PC2"]) == float(row["PC2"]))
            self.assertEqual((row["condition"], row["batch"]), expected[row["sample_id"]])

    def run_pca_with_reversed_metadata(self, directory: Path, language: str):
        metadata_result = self.run_metadata(directory, language)
        self.assert_metadata_success(metadata_result, directory)
        metadata_path = directory / "metadata.validated.csv"
        with metadata_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        with metadata_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(reversed(rows))
        source = self.python_pca if language == "python" else self.r_pca
        executable = sys.executable if language == "python" else self.rscript
        name = "pca.py" if language == "python" else "pca.R"
        return run_script(executable, source, name, directory)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_displayed_base_r_pca_runs_and_aligns_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_pca_success(self.run_pca(directory, "r"), directory)

    @unittest.skipUnless(has_packages("pandas", "numpy"), "optional pandas and NumPy are required")
    def test_displayed_python_pca_runs_and_aligns_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_pca_success(self.run_pca(directory, "python"), directory)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_base_r_pca_aligns_reversed_metadata_by_sample_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_pca_success(self.run_pca_with_reversed_metadata(directory, "r"), directory)

    @unittest.skipUnless(has_packages("pandas", "numpy"), "optional pandas and NumPy are required")
    def test_python_pca_aligns_reversed_metadata_by_sample_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.assert_pca_success(self.run_pca_with_reversed_metadata(directory, "python"), directory)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is not installed")
    def test_base_r_pca_rejects_misaligned_sample_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            counts = self.counts_csv.replace("S04", "S99", 1)
            result = self.run_pca(directory, "r", counts=counts)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match exactly", result.stderr)

    @unittest.skipUnless(has_packages("pandas", "numpy"), "optional pandas and NumPy are required")
    def test_python_pca_rejects_misaligned_sample_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            counts = self.counts_csv.replace("S04", "S99", 1)
            result = self.run_pca(directory, "python", counts=counts)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must match exactly", result.stderr)


if __name__ == "__main__":
    unittest.main()
