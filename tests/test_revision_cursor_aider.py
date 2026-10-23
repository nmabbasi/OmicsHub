"""Regression tests for the Cursor/Aider bounded-edit lesson and offline fixtures."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "tutorials" / "ai-coding-cursor-aider.html"
FIXTURE_DIR = ROOT / "files" / "coding-assistant-lesson"
CHECK_DIFF = FIXTURE_DIR / "check_diff.py"
INSPECT_COUNTS = FIXTURE_DIR / "inspect_counts.py"
COUNTS_TSV = FIXTURE_DIR / "counts.tsv"


def load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


count_tools = load_module("lesson_inspect_counts", INSPECT_COUNTS)


class LessonContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = LESSON.read_text(encoding="utf-8")

    def test_both_tools_get_same_bounded_prompt_and_expected_change(self):
        self.assertIn("For both tools, use this exact prompt", self.html)
        self.assertIn(
            'Edit only README.md. Immediately after the Input line, add exactly this sentence: "'
            'The two sample counts sum to 20 reads." Do not alter any existing text, the values '
            '12, 8, or 20, or any other file; do not add dependencies, inspect or expose secrets, '
            'or access data outside this folder.',
            self.html,
        )
        self.assertIn("+The two sample counts sum to 20 reads.", self.html)
        self.assertIn("do not accept", self.html.lower())
        self.assertIn("12 reads", self.html)
        self.assertIn("8 reads", self.html)
        self.assertIn("20 reads", self.html)

    def test_optional_count_exercise_links_to_the_tested_fixture_and_script(self):
        self.assertIn('href="../files/coding-assistant-lesson/counts.tsv"', self.html)
        self.assertIn('href="../files/coding-assistant-lesson/inspect_counts.py"', self.html)
        self.assertIn("rows are genes and columns are samples", self.html)
        self.assertIn("finite, nonnegative integers", self.html)
        self.assertIn("independent samples", self.html)
        self.assertTrue(COUNTS_TSV.is_file())
        self.assertTrue(INSPECT_COUNTS.is_file())

    def test_offline_and_provider_execution_boundaries_are_explicit(self):
        for phrase in ("not installed or run", "No model request", "optional", "charges"):
            self.assertIn(phrase.lower(), self.html.lower())


class DiffFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        shutil.copy2(CHECK_DIFF, self.project / "check_diff.py")
        (self.project / "README.md").write_text(
            load_module("lesson_diff", CHECK_DIFF).BASE_README, encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=self.project, check=True)
        subprocess.run(["git", "config", "user.name", "Lesson Test"], cwd=self.project, check=True)
        subprocess.run(["git", "config", "user.email", "lesson-test"], cwd=self.project, check=True)
        subprocess.run(["git", "add", "README.md", "check_diff.py"], cwd=self.project, check=True)
        subprocess.run(["git", "commit", "-qm", "Create invented lesson baseline"], cwd=self.project, check=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_validator(self):
        return subprocess.run(
            [sys.executable, "check_diff.py"],
            cwd=self.project,
            capture_output=True,
            text=True,
        )

    def test_accepts_only_the_expected_one_sentence_change(self):
        module = load_module("lesson_diff_success", CHECK_DIFF)
        (self.project / "README.md").write_text(module.EXPECTED_README, encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("only the expected sentence", result.stdout)
        self.assertIn("not evidence that Cursor, Aider, or a model ran", result.stdout)

    def test_rejects_changed_count_and_unrelated_untracked_file(self):
        module = load_module("lesson_diff_reject", CHECK_DIFF)
        invalid = module.EXPECTED_README.replace("12 reads", "13 reads")
        (self.project / "README.md").write_text(invalid, encoding="utf-8")
        (self.project / "unexpected.txt").write_text("not allowed\n", encoding="utf-8")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("only one unstaged change", result.stderr)
        self.assertIn("not exactly the expected one-sentence edit", result.stderr)

    def test_rejects_an_extra_tracked_file_change(self):
        module = load_module("lesson_diff_extra", CHECK_DIFF)
        (self.project / "README.md").write_text(module.EXPECTED_README, encoding="utf-8")
        (self.project / "check_diff.py").write_text(
            (self.project / "check_diff.py").read_text(encoding="utf-8") + "# unrelated\n",
            encoding="utf-8",
        )
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("only one unstaged change", result.stderr)


class CountContractTests(unittest.TestCase):
    def test_invented_table_orientation_and_column_sums(self):
        samples, genes, matrix = count_tools.read_count_table(COUNTS_TSV)
        self.assertEqual(samples, ["sample_A", "sample_B"])
        self.assertEqual(genes, ["gene_alpha", "gene_beta", "gene_gamma"])
        self.assertEqual(count_tools.sample_totals(samples, matrix), {"sample_A": 16, "sample_B": 12})

    def test_rejects_negative_fractional_and_nonfinite_values(self):
        bad_values = ("-1", "1.5", "NaN", "inf")
        for value in bad_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                table = Path(tmp) / "counts.tsv"
                table.write_text(
                    f"gene_id\tsample_A\tsample_B\ngene_alpha\t{value}\t8\n",
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "nonnegative integer"):
                    count_tools.read_count_table(table)

    def test_rejects_ragged_rows_and_duplicate_identifiers(self):
        cases = (
            "gene_id\tsample_A\tsample_B\ngene_alpha\t12\n",
            "gene_id\tsample_A\tsample_B\ngene_alpha\t12\t8\ngene_alpha\t0\t1\n",
        )
        for content in cases:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                table = Path(tmp) / "counts.tsv"
                table.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    count_tools.read_count_table(table)


if __name__ == "__main__":
    unittest.main()
