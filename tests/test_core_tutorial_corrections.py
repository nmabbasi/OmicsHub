"""Focused regression checks for the core tutorial corrections."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def page(slug: str) -> str:
    return (ROOT / "tutorials" / f"{slug}.html").read_text(encoding="utf-8")


class SeuratMarkerTutorialTests(unittest.TestCase):
    def test_marker_workflow_requires_and_uses_rna_and_states_dimension_order(self) -> None:
        text = page("ai-prompt-engineering-seurat")
        self.assertIn("Seurat object dimensions (features x cells)", text)
        self.assertNotIn("Seurat object dimensions (cells x genes)", text)
        self.assertIn('!("RNA" %in% Assays(seurat_obj))', text)
        self.assertIn('DefaultAssay(seurat_obj) &lt;- "RNA"', text)
        self.assertIn('assay = "RNA"', text)
        self.assertIn("satijalab.org/seurat/reference/findmarkers", text)
        self.assertIn("satijalab.org/seurat/articles/essential_commands.html", text)


class Kraken2SyntheticReportTests(unittest.TestCase):
    def test_genus_clade_total_includes_child_and_direct_fragments(self) -> None:
        text = page("metagenomics-kraken2-bracken")
        start = text.index("<h2>Practice with a synthetic report</h2>")
        end = text.index("</code></pre>", start)
        report = text[start:end]
        genus = re.search(r"^\s*(\d+\.\d+)\s+(\d+)\s+(\d+)\s+G\s+123\s+Examplegenus\s*$", report, re.M)
        self.assertIsNotNone(genus)
        percent, clade, direct = genus.groups()
        child_clades = [int(x) for x in re.findall(r"^\s*\d+\.\d+\s+(\d+)\s+\d+\s+S\s+(?:456|789)\s+.*$", report, re.M)]
        self.assertEqual(child_clades, [250, 350])
        self.assertEqual(int(clade), int(direct) + sum(child_clades))
        self.assertAlmostEqual(float(percent), 100 * int(clade) / 1000)


class GgetVersionedTranscriptTests(unittest.TestCase):
    def test_canonical_transcript_behavior_is_pinned_and_source_linked(self) -> None:
        text = page("deterministic-retrieval-gget-ai")
        self.assertIn("gget==0.28.6", text)
        self.assertIn("isoforms=False", text)
        self.assertIn("canonical_transcript", text)
        self.assertIn("github.com/pachterlab/gget/blob/v0.28.6/gget/gget_seq.py", text)
        self.assertNotIn("Do not label a record canonical unless the returned record establishes", text)


if __name__ == "__main__":
    unittest.main()
