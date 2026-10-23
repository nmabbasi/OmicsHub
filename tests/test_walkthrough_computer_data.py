"""Execution checks for the displayed synthetic FASTQ walkthrough commands."""
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ARTICLE = Path(__file__).resolve().parents[1] / "tutorials" / "computer-data-fundamentals.html"


class ArticleCodeExtractor(HTMLParser):
    """Collect displayed preformatted code blocks from the tutorial article."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.article_depth = 0
        self.pre_depth = 0
        self.code_depth = 0
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "article":
            self.article_depth += 1
        elif self.article_depth and tag == "pre":
            self.pre_depth += 1
        elif self.pre_depth and tag == "code" and self.code_depth == 0:
            self.code_depth = 1
            self.current = []

    def handle_endtag(self, tag):
        if tag == "code" and self.current is not None:
            self.blocks.append("".join(self.current))
            self.current = None
            self.code_depth = 0
        elif tag == "pre" and self.pre_depth:
            self.pre_depth -= 1
        elif tag == "article" and self.article_depth:
            self.article_depth -= 1

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)


def displayed_blocks():
    parser = ArticleCodeExtractor()
    parser.feed(ARTICLE.read_text(encoding="utf-8"))
    return parser.blocks


def block_containing(blocks, marker):
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"expected one displayed code block containing {marker!r}; got {len(matches)}")
    return matches[0]


class ComputerDataWalkthroughExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These are system tools used by the displayed Bash examples; no installs or network access.
        required = (
            "bash", "gzip", "sha256sum", "zcat", "awk", "du", "tee", "date",
            "df", "nproc", "free", "file", "head",
        )
        missing = [name for name in required if shutil.which(name) is None]
        if missing:
            raise unittest.SkipTest("missing system commands: " + ", ".join(missing))

        blocks = displayed_blocks()
        cls.displayed_sequence = [
            block_containing(blocks, "sha256sum sample_R1.fastq.gz sample_R2.fastq.gz > SHA256SUMS"),
            block_containing(blocks, "mkdir -p ~/projects/my-study/{data/raw,data/processed,scripts,results,logs}"),
            block_containing(blocks, "du -sh . | tee logs/disk_usage_"),
            block_containing(blocks, "nproc\nfree -h"),
            block_containing(blocks, "file data/raw/sample_R1.fastq.gz"),
            block_containing(blocks, "sha256sum -c SHA256SUMS"),
            block_containing(blocks, "count_fastq_records data/raw/sample_R1.fastq.gz"),
        ]
        count_call = "\ncount_fastq_records data/raw/sample_R1.fastq.gz"
        if cls.displayed_sequence[-1].count(count_call) != 1:
            raise AssertionError("expected the displayed count block to call the function once")
        cls.count_definition = cls.displayed_sequence[-1].split(count_call, 1)[0]
        cls.negative_example = block_containing(
            blocks, "count_fastq_records data/raw/missing_R1.fastq.gz"
        )

    def run_walkthrough(self, negative=None):
        with tempfile.TemporaryDirectory(prefix="computer-data-home-") as temporary:
            home = Path(temporary) / "home"
            home.mkdir()
            sequence = self.displayed_sequence
            if negative:
                sequence = sequence[:-1] + [self.count_definition]
            script = "set -e\n" + "\n".join(sequence)
            if negative == "corrupt":
                script += (
                    "\nprintf 'not a gzip stream\\n' > "
                    "\"$HOME/projects/my-study/data/raw/missing_R1.fastq.gz\"\n"
                )
            if negative:
                script += "\n" + self.negative_example + "\n"
            else:
                script += "\nprintf '\\nFINAL_CWD=%s\\n' \"$PWD\"\n"
            result = subprocess.run(
                [shutil.which("bash"), "--noprofile", "--norc"],
                input=script,
                text=True,
                capture_output=True,
                cwd=home,
                env={**os.environ, "HOME": str(home)},
                check=False,
            )
            return result

    def test_displayed_setup_checksum_and_count_run_sequentially(self):
        result = self.run_walkthrough()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sample_R1.fastq.gz: OK", result.stdout)
        self.assertIn("sample_R2.fastq.gz: OK", result.stdout)
        self.assertIn("gzip exit status: 0", result.stdout)
        self.assertIn("2 records", result.stdout)
        self.assertRegex(result.stdout, r"FINAL_CWD=.*/projects/my-study\n")
        self.assertNotIn("0 records", result.stdout)

    def test_missing_gzip_fails_without_printing_a_record_count(self):
        result = self.run_walkthrough(negative="missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("records", result.stdout)
        self.assertIn("Cannot count records: gzip integrity check failed", result.stderr)

    def test_corrupt_gzip_fails_without_printing_a_record_count(self):
        result = self.run_walkthrough(negative="corrupt")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("records", result.stdout)
        self.assertIn("Cannot count records: gzip integrity check failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
