"""Focused regression checks for the five approved tutorial corrections."""
from html import unescape
import gzip
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def page(slug: str) -> str:
    return (ROOT / "tutorials" / f"{slug}.html").read_text(encoding="utf-8")


class SeuratMarkerTutorialTests(unittest.TestCase):
    def test_marker_workflow_requires_rna_and_states_dimension_order(self) -> None:
        text = page("ai-prompt-engineering-seurat")
        self.assertIn("Seurat object dimensions (features x cells)", text)
        self.assertNotIn("Seurat object dimensions (cells x genes)", text)
        self.assertIn('!("RNA" %in% Assays(seurat_obj))', text)
        self.assertIn('DefaultAssay(seurat_obj) &lt;- "RNA"', text)
        self.assertIn('assay = "RNA"', text)
        self.assertIn("satijalab.org/seurat/reference/findmarkers", text)
        self.assertIn("satijalab.org/seurat/articles/essential_commands.html", text)


class EmptyFastqPairTests(unittest.TestCase):
    def test_r_route_rejects_two_empty_files(self) -> None:
        text = unescape(page("biological-data-formats"))
        self.assertRegex(
            text,
            r'if \(n == 0L\) stop\("FAIL: both files are empty"',
        )

    def test_python_route_rejects_empty_and_accepts_a_matching_pair(self) -> None:
        text = unescape(page("biological-data-formats"))
        marker = "python3 - reads_R1.fastq.gz reads_R2.fastq.gz <<'PY'\n"
        start = text.index(marker) + len(marker)
        end = text.index("\nPY</code></pre>", start)
        source = text[start:end]

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = [Path(temp_dir) / "reads_R1.fastq.gz", Path(temp_dir) / "reads_R2.fastq.gz"]
            for path in paths:
                with gzip.open(path, "wt", encoding="utf-8"):
                    pass
            result = subprocess.run(
                [sys.executable, "-", *(str(path) for path in paths)],
                input=source,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL: both files are empty", result.stderr)
            good_pairs = [
                "@read_A/1 instrument\nACGT\n+\n!!!!\n",
                "@read_A/2 instrument\nTGCA\n+\n####\n",
            ]
            for path, records in zip(paths, good_pairs):
                with gzip.open(path, "wt", encoding="utf-8") as handle:
                    handle.write(records)
            result = subprocess.run(
                [sys.executable, "-", *(str(path) for path in paths)],
                input=source,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS: 1 paired records", result.stdout)


class Kraken2SyntheticReportTests(unittest.TestCase):
    def test_genus_clade_total_includes_child_and_direct_fragments(self) -> None:
        text = page("metagenomics-kraken2-bracken")
        start = text.index("<h2>Practice with a synthetic report</h2>")
        end = text.index("</code></pre>", start)
        report = text[start:end]
        genus = re.search(
            r"^\s*(\d+\.\d+)\s+(\d+)\s+(\d+)\s+G\s+123\s+Examplegenus\s*$",
            report,
            re.M,
        )
        self.assertIsNotNone(genus)
        percent, clade, direct = genus.groups()
        child_clades = [
            int(value)
            for value in re.findall(
                r"^\s*\d+\.\d+\s+(\d+)\s+\d+\s+S\s+(?:456|789)\s+.*$",
                report,
                re.M,
            )
        ]
        self.assertEqual(child_clades, [250, 350])
        self.assertEqual(int(clade), int(direct) + sum(child_clades))
        self.assertAlmostEqual(float(percent), 100 * int(clade) / 1000)


class TrajectoryMethodScopeTests(unittest.TestCase):
    def test_non_equivalent_python_workflow_is_not_presented_as_a_route(self) -> None:
        text = page("scrna-seq-trajectory-inference")
        self.assertIn(
            "PAGA and DPT are discussed as distinct methods, not as equivalent Python translations.",
            text,
        )
        self.assertNotIn("Optional Python method (distinct): Scanpy PAGA and DPT", text)
        self.assertNotRegex(text, r'<pre><code class="language-python">')
        self.assertRegex(text, r'<pre><code class="language-r">')


class GgetVersionedTranscriptTests(unittest.TestCase):
    def test_canonical_transcript_behavior_is_pinned_and_source_linked(self) -> None:
        text = page("deterministic-retrieval-gget-ai")
        self.assertIn("gget==0.28.6", text)
        self.assertIn("isoforms=False", text)
        self.assertIn("canonical_transcript", text)
        self.assertIn("github.com/pachterlab/gget/blob/v0.28.6/gget/gget_seq.py", text)
        self.assertNotIn(
            "Do not label a record canonical unless the returned record establishes",
            text,
        )


if __name__ == "__main__":
    unittest.main()
