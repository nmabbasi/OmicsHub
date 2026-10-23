#!/usr/bin/env python3
"""Regression checks for the displayed Nextflow DSL2 text-fixture workflow."""
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "tutorials/reproducible-workflows-snakemake-nextflow.html"


class GroovyCodeExtractor(HTMLParser):
    """Collect displayed Groovy code verbatim, decoding HTML entities."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_groovy = False
        self.depth = 0
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "code" and "language-groovy" in attrs.get("class", "").split():
            self.in_groovy = True
            self.depth = 1
            self.parts = []
        elif self.in_groovy and tag == "code":
            self.depth += 1

    def handle_endtag(self, tag):
        if self.in_groovy and tag == "code":
            self.depth -= 1
            if self.depth == 0:
                self.blocks.append("".join(self.parts))
                self.in_groovy = False

    def handle_data(self, data):
        if self.in_groovy:
            self.parts.append(data)


def displayed_nextflow_workflow():
    parser = GroovyCodeExtractor()
    parser.feed(TUTORIAL.read_text(encoding="utf-8"))
    if len(parser.blocks) != 1:
        raise AssertionError(f"expected one displayed Groovy code block; got {len(parser.blocks)}")
    return parser.blocks[0]


def nextflow_executable():
    configured = os.environ.get("NEXTFLOW_EXECUTABLE")
    return shutil.which(configured) if configured else shutil.which("nextflow")


class NextflowPriorityFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = displayed_nextflow_workflow()

    def test_displayed_script_declares_input_output_and_publication_contract(self):
        workflow = self.workflow
        self.assertIn("params.input = 'data/demo.txt'", workflow)
        self.assertIn("path source", workflow)
        self.assertIn('cp "$source" copied.txt', workflow)
        self.assertIn("path 'copied.txt'", workflow)
        self.assertIn("publishDir 'results', mode: 'copy'", workflow)
        self.assertIn("channel.fromPath(params.input, checkIfExists: true)", workflow)
        page = TUTORIAL.read_text(encoding="utf-8")
        self.assertIn("cmp -- data/demo.txt results/copied.txt", page)
        self.assertIn("Nextflow records task cache entries on each run, but reuses them only when you explicitly pass", page)

    @unittest.skipUnless(nextflow_executable(), "Nextflow is not installed; real DSL2 integration checks skipped")
    def test_real_workflow_publishes_identical_bytes_and_rejects_missing_input(self):
        executable = nextflow_executable()
        original = b"fixture text for workflow practice\nexact bytes\n"

        with tempfile.TemporaryDirectory(prefix="nextflow-publish-") as tmp:
            run_dir = Path(tmp)
            (run_dir / "main.nf").write_text(self.workflow, encoding="utf-8")
            (run_dir / "data").mkdir()
            source = run_dir / "data/demo.txt"
            source.write_bytes(original)
            result = subprocess.run(
                [executable, "run", "main.nf"], cwd=run_dir, capture_output=True,
                text=True, check=False, timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            published = run_dir / "results/copied.txt"
            self.assertTrue(published.is_file(), "workflow did not publish results/copied.txt")
            self.assertEqual(published.read_bytes(), source.read_bytes())

        with tempfile.TemporaryDirectory(prefix="nextflow-missing-") as tmp:
            run_dir = Path(tmp)
            (run_dir / "main.nf").write_text(self.workflow, encoding="utf-8")
            (run_dir / "data").mkdir()
            result = subprocess.run(
                [executable, "run", "main.nf", "--input", "data/missing.txt"],
                cwd=run_dir, capture_output=True, text=True, check=False, timeout=180,
            )
            self.assertNotEqual(result.returncode, 0, "missing workflow input unexpectedly succeeded")
            feedback = (result.stdout + result.stderr).casefold()
            self.assertIn("missing.txt", feedback, feedback)


if __name__ == "__main__":
    unittest.main()
