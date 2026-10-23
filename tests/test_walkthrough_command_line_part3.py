"""Offline execution checks for the beginner Bash walkthrough in Part 3."""

from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTICLE_PATH = REPO_ROOT / "tutorials" / "command-line-part3.html"
SEQKIT_PATH = REPO_ROOT.parent / "tooling" / "text-processing-lesson" / "seqkit"
REQUIRED_TOOLS = ("bash", "awk", "gzip", "sort", "cat", "mkdir", "dirname", "mktemp", "mv")


class PreBlockParser(HTMLParser):
    """Collect rendered preformatted code with HTML entities decoded."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_pre = False
        self.current = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.in_pre = True
            self.current = []

    def handle_endtag(self, tag):
        if tag == "pre" and self.in_pre:
            self.blocks.append("".join(self.current))
            self.in_pre = False

    def handle_data(self, data):
        if self.in_pre:
            self.current.append(data)


def article_blocks():
    parser = PreBlockParser()
    parser.feed(ARTICLE_PATH.read_text(encoding="utf-8"))
    return parser.blocks


def block_containing(blocks, marker):
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"Expected one displayed code block containing {marker!r}, found {len(matches)}")
    return matches[0]


def run_bash(block, cwd, check=True):
    return subprocess.run(
        [shutil.which("bash") or "bash", "-e", "-c", block],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
        env={**os.environ, "LC_ALL": "C"},
    )


@unittest.skipUnless(all(shutil.which(tool) for tool in REQUIRED_TOOLS), "requires the lesson's Bash and system utilities")
class CommandLinePart3WalkthroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.article = ARTICLE_PATH.read_text(encoding="utf-8")
        cls.blocks = article_blocks()
        cls.preflight = block_containing(cls.blocks, "bash --version")
        cls.setup = block_containing(cls.blocks, "shell-tutorial already exists")
        cls.save_script = block_containing(cls.blocks, "cat > summarize.sh <<'BASH'")
        cls.run_summaries = block_containing(cls.blocks, "./summarize.sh fastq test_data/example.fastq.gz")
        cls.expected_tables = block_containing(cls.blocks, "reads\t2\t8\t12\t10.00")
        cls.failure_case = block_containing(cls.blocks, "if ./summarize.sh fastq test_data/bad-length.fastq")
        cls.modification = block_containing(cls.blocks, "@read3")
        cls.modified_expected = block_containing(cls.blocks, "reads\t3\t6\t12\t8.67")

    def test_documented_lab_saves_runs_fails_safely_and_modifies(self):
        with tempfile.TemporaryDirectory(prefix="part3-walkthrough-") as temp_dir:
            parent = Path(temp_dir)
            run_bash(self.preflight, parent)
            run_bash(self.setup, parent)
            lab = parent / "shell-tutorial"

            run_bash(self.save_script, lab)
            program = lab / "summarize.sh"
            self.assertTrue(program.is_file())
            self.assertTrue(os.access(program, os.X_OK))
            self.assertTrue(program.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash\n"))

            run_bash(self.run_summaries, lab)
            self.assertEqual(
                (lab / "results" / "fastq_summary.tsv").read_text(encoding="utf-8"),
                "#type\tcount\tmin_len\tmax_len\tmean_len\nreads\t2\t8\t12\t10.00\n",
            )
            self.assertEqual(
                (lab / "results" / "annotations_summary.tsv").read_text(encoding="utf-8"),
                "#chr\tfeature_count\tavg_length\nchr1\t2\t76.00\nchr2\t1\t351.00\n",
            )
            self.assertIn("chr1\t2\t76.00", self.expected_tables)

            failed = run_bash(self.failure_case, lab)
            self.assertIn("Invalid FASTQ: sequence and quality lengths differ (record 1)", failed.stderr)
            self.assertIn("Rejected malformed FASTQ as expected", failed.stdout)
            self.assertFalse((lab / "results" / "rejected.tsv").exists())
            self.assertEqual(list((lab / "results").glob("rejected.tsv.tmp.*")), [])

            run_bash(self.modification, lab)
            self.assertEqual(
                (lab / "results" / "fastq_summary_with_third.tsv").read_text(encoding="utf-8"),
                "#type\tcount\tmin_len\tmax_len\tmean_len\nreads\t3\t6\t12\t8.67\n",
            )

    def test_setup_refuses_to_overwrite_an_existing_lab_directory(self):
        with tempfile.TemporaryDirectory(prefix="part3-overwrite-guard-") as temp_dir:
            parent = Path(temp_dir)
            existing = parent / "shell-tutorial"
            existing.mkdir()
            sentinel = existing / "keep.txt"
            sentinel.write_text("leave this file alone\n", encoding="utf-8")
            result = run_bash(self.setup, parent, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shell-tutorial already exists", result.stderr)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "leave this file alone\n")

    @unittest.skipUnless(SEQKIT_PATH.is_file() and os.access(SEQKIT_PATH, os.X_OK), "optional SeqKit binary is not present")
    def test_optional_seqkit_check_accepts_the_synthetic_fastq(self):
        with tempfile.TemporaryDirectory(prefix="part3-seqkit-") as temp_dir:
            parent = Path(temp_dir)
            run_bash(self.setup, parent)
            fastq = parent / "shell-tutorial" / "test_data" / "example.fastq"
            result = subprocess.run(
                [str(SEQKIT_PATH), "stats", "-T", str(fastq)],
                text=True,
                capture_output=True,
                check=True,
                env={**os.environ, "LC_ALL": "C"},
            )
            rows = [line.split("\t") for line in result.stdout.splitlines()]
            self.assertEqual(rows[0], ["file", "format", "type", "num_seqs", "sum_len", "min_len", "avg_len", "max_len"])
            self.assertEqual(rows[1][1:], ["FASTQ", "DNA", "2", "20", "8", "10.0", "12"])

    def test_walkthrough_keeps_tool_scope_and_reader_facing_copy_clear(self):
        article_text = self.article[self.article.index("<article "):self.article.index("</article>")]
        self.assertNotIn("—", article_text)
        self.assertNotIn("[[SCRIPT]]", article_text)
        self.assertIn("does not call SeqKit, R, or Python", article_text)
        self.assertIn("cat > summarize.sh <<'BASH'", self.save_script)
        self.assertIn("printf", self.run_summaries)
        self.assertIn("8.67", self.modified_expected)
        self.assertIn("Optional cleanup", self.article)


if __name__ == "__main__":
    unittest.main()
