"""Regression checks for two runnable tutorial code handoffs."""

from __future__ import annotations

import shutil
import struct
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WES_FIXTURE = ROOT / "files/wes-contract-fixture/filter_status_ad_dp.vcf"


class _PreBlocks(HTMLParser):
    """Collect preformatted code text using only the Python standard library."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._in_pre = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "pre":
            self._in_pre = True
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self._in_pre:
            self.blocks.append("".join(self._parts))
            self._in_pre = False

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self._parts.append(data)


def pre_blocks(path: Path) -> list[str]:
    parser = _PreBlocks()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.blocks


def qc_blocks() -> tuple[str, str]:
    blocks = pre_blocks(ROOT / "tutorials/scrna-seq-quality-control.html")
    first = next(block for block in blocks if "library(lisi)" in block and "compute_lisi" in block)
    summary = next(block for block in blocks if "lisi_metadata.csv" in block and "aggregate(cbind" in block)
    return first, summary


class TutorialExecutionFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("Rscript") or not shutil.which("bash"):
            raise unittest.SkipTest("Optional runtime contracts require existing Rscript and Bash; no packages are installed by these tests")

    def test_exact_displayed_wes_command_runs_on_public_toy_vaf_fixture(self) -> None:
        self.assertTrue(WES_FIXTURE.is_file())
        command = next(
            block for block in pre_blocks(ROOT / "tutorials/wes-variant-calling-pipeline.html")
            if "Rscript -e" in block and "VAF_distribution.png" in block
        )
        self.assertNotRegex(command, r"\\\s*\n")
        fractions = []
        for line in WES_FIXTURE.read_text().splitlines():
            if line.startswith("#"):
                continue
            fields = line.split("\t")
            if fields[6] != "PASS":
                continue
            sample = dict(zip(fields[8].split(":"), fields[9].split(":")))
            depths = [int(value) for value in sample["AD"].split(",")]
            fractions.append(str(depths[1] / sum(depths)) if "," not in fields[4] and len(depths) == 2 else "NA")
        self.assertEqual(fractions, ["0.4", "NA"])
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "vcf").mkdir()
            (work / "diagnostics").mkdir()
            # This is a source-derived format fixture, not a saved research output.
            (work / "vcf/NA12878_pass.withVAF.tsv").write_text("VAF\n" + "\n".join(fractions) + "\n")
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", command],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            image = work / "diagnostics/VAF_distribution.png"
            self.assertTrue(image.is_file())
            self.assertGreater(image.stat().st_size, 1000)
            self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", image.read_bytes()[16:24]), (800, 600))

    def test_qc_summary_handoff_survives_a_new_r_process_and_fails_without_metadata(self) -> None:
        first, summary = qc_blocks()
        self.assertIn('write.csv(meta, file = "lisi_metadata.csv")', first)
        self.assertIn('read.csv("lisi_metadata.csv", row.names = 1, check.names = FALSE)', summary)
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            # A fresh process without stage-one output must fail clearly, not use inherited `meta`.
            missing = subprocess.run(
                ["Rscript", "--vanilla", "-e", summary], cwd=work, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("lisi_metadata.csv", missing.stderr)

            # Match the CSV layout written by write.csv(meta); these values are
            # handoff fixtures only and are not a PBMC or LISI result.
            (work / "lisi_metadata.csv").write_text(
                '\"\",\"seurat_clusters\"\n'
                '\"cell1\",\"0\"\n'
                '\"cell2\",\"0\"\n'
                '\"cell3\",\"1\"\n'
                '\"cell4\",\"1\"\n',
                encoding="utf-8",
            )
            (work / "lisi_scores.csv").write_text(
                '\"\",\"patient_id\",\"cell_type\"\n'
                '\"cell1\",1,1\n'
                '\"cell2\",1,1.2\n'
                '\"cell3\",1,2\n'
                '\"cell4\",1,2.2\n',
                encoding="utf-8",
            )
            completed = subprocess.run(
                ["Rscript", "--vanilla", "-e", summary], cwd=work, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("seurat_clusters", completed.stdout)
            self.assertIn("ilisi", completed.stdout)
            self.assertIn("clisi", completed.stdout)


if __name__ == "__main__":
    unittest.main()
