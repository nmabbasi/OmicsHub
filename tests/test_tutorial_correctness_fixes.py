#!/usr/bin/env python3
"""Regression tests for three bounded tutorial code/correctness fixes (stdlib only)."""
from html import unescape
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE_BLOCK = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S)


def code_blocks(relative_path):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    return [unescape(code) for code in CODE_BLOCK.findall(text)]


class MarkerExporterTests(unittest.TestCase):
    def test_structured_logfoldchange_field_is_indexed_without_get(self):
        blocks = code_blocks("tutorials/ai-prompt-engineering-seurat.html")
        block = next(code for code in blocks if "r = adata.uns['rank_genes_groups']" in code)
        exporter_line = next(
            line.strip() for line in block.splitlines()
            if line.lstrip().startswith("logfoldchanges =")
        )

        class GroupArray:
            def tolist(self):
                return [0.4, 0.9]

        class StructuredResult(dict):
            def get(self, *_args, **_kwargs):
                raise AssertionError("structured Scanpy result fields do not support dict.get")

        result = StructuredResult({"logfoldchanges": {"cluster_a": GroupArray()}})
        scope = {"r": result, "group": "cluster_a", "names": ["gene1", "gene2"]}
        exec(exporter_line, scope)
        self.assertEqual(scope["logfoldchanges"], [0.4, 0.9])

    def test_absent_optional_logfoldchange_field_gets_missing_values(self):
        block = next(
            code for code in code_blocks("tutorials/ai-prompt-engineering-seurat.html")
            if "r = adata.uns['rank_genes_groups']" in code
        )
        exporter_line = next(
            line.strip() for line in block.splitlines()
            if line.lstrip().startswith("logfoldchanges =")
        )

        class NoGetMapping(dict):
            def get(self, *_args, **_kwargs):
                raise AssertionError("must not call .get on structured result")

        scope = {"r": NoGetMapping(), "group": "cluster_a", "names": ["gene1", "gene2"]}
        exec(exporter_line, scope)
        self.assertEqual(scope["logfoldchanges"], [None, None])


class WESLiftoverConsistencyTests(unittest.TestCase):
    def test_optional_liftover_has_explicit_grch37_source_and_grch38_target(self):
        page = (ROOT / "tutorials/wes-variant-calling-pipeline.html").read_text(encoding="utf-8")
        self.assertIn("The calling and filtering commands above use GRCh38", page)
        block = next(code for code in code_blocks("tutorials/wes-variant-calling-pipeline.html")
                     if "gatk LiftoverVcf" in code)
        self.assertIn("Separate input: this VCF was called against GRCh37", block)
        self.assertIn("-I vcf/NA12878_GRCh37_filtered.vcf.gz", block)
        self.assertIn("-CHAIN refs/hg19ToHg38.over.chain.gz", block)
        self.assertIn("-R refs/GRCh38.fa", block)
        self.assertIn("-O vcf/NA12878_GRCh37input_liftedToGRCh38.vcf.gz", block)
        self.assertNotIn("-I vcf/NA12878_filtered.vcf.gz", block)


class BashInputOutputAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        saved_blocks = [
            code for code in code_blocks("tutorials/command-line-part3.html")
            if "cat > summarize.sh <<'BASH'" in code
        ]
        if len(saved_blocks) != 1:
            raise AssertionError("expected exactly one displayed summarize.sh save block")
        match = re.search(
            r"^cat > summarize\.sh <<'BASH'\n(.*?)\nBASH(?:\n|$)",
            saved_blocks[0], re.S | re.M,
        )
        if not match or not match.group(1).startswith("#!/usr/bin/env bash\n"):
            raise AssertionError("expected the actual Bash script within the quoted save block")
        cls.script = match.group(1) + "\n"

    def run_script(self, input_path, output_path):
        return subprocess.run(
            ["bash", "-c", self.script, "tutorial-summarize", "fastq", str(input_path), str(output_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )

    def assert_alias_refused_and_source_unchanged(self, input_path, output_path, source, original):
        result = self.run_script(input_path, output_path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Input and output must be different files", result.stderr)
        self.assertEqual(source.read_bytes(), original)

    def test_same_path_is_refused_without_replacing_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "reads.fastq"
            original = b"@r1\nACGT\n+\nIIII\n"
            source.write_bytes(original)
            self.assert_alias_refused_and_source_unchanged(source, source, source, original)

    def test_symlink_alias_is_refused_without_replacing_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "reads.fastq"
            output = Path(temporary) / "summary.tsv"
            original = b"@r1\nACGT\n+\nIIII\n"
            source.write_bytes(original)
            output.symlink_to(source)
            self.assert_alias_refused_and_source_unchanged(source, output, source, original)
            self.assertTrue(output.is_symlink())

    def test_hardlink_alias_is_refused_without_replacing_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "reads.fastq"
            output = Path(temporary) / "hardlink.fastq"
            original = b"@r1\nACGT\n+\nIIII\n"
            source.write_bytes(original)
            output.hardlink_to(source)
            self.assert_alias_refused_and_source_unchanged(source, output, source, original)
            self.assertEqual(source.stat().st_ino, output.stat().st_ino)

    def test_distinct_input_and_output_still_produce_expected_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "reads.fastq"
            output = Path(temporary) / "results" / "summary.tsv"
            source.write_bytes(b"@r1\nACGT\n+\nIIII\n")
            result = self.run_script(source, output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"),
                             "#type\tcount\tmin_len\tmax_len\tmean_len\nreads\t1\t4\t4\t4.00\n")
            self.assertEqual(source.read_bytes(), b"@r1\nACGT\n+\nIIII\n")


if __name__ == "__main__":
    unittest.main()
