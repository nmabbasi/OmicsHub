"""WES contract tests: toy VCF semantics and a stubbed alignment failure path.

These checks do not run GATK, use human reference/reads, call variants, or claim
scientific validation. The BWA/samtools test is a shell-contract test only.
"""
from html import unescape
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials/wes-variant-calling-pipeline.html"
FIXTURE = ROOT / "files/wes-contract-fixture/filter_status_ad_dp.vcf"
CODE_BLOCK = re.compile(r"<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>", re.S)


def code_blocks():
    return [unescape(code) for code in CODE_BLOCK.findall(PAGE.read_text(encoding="utf-8"))]


def find_block(predicate):
    return next(block for block in code_blocks() if predicate(block))


def run_bash(script, *, cwd, env=None):
    return subprocess.run(
        ["bash", "-c", script], cwd=cwd, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


class WESAlignmentFailureContractTests(unittest.TestCase):
    def test_bwa_failure_stops_alignment_block_before_bam_indexing(self):
        alignment = find_block(lambda block: "bwa mem -t 16" in block and "samtools sort" in block)
        self.assertIn("set -euo pipefail", alignment)
        self.assertIn("bwa index -a bwtsw refs/GRCh38.fa", alignment)
        self.assertIn("Alignment pipeline failed (BWA or samtools sort); stopping before BAM indexing.", alignment)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("raw", "refs", "aligned", "metrics", "vcf", "diagnostics"):
                (root / directory).mkdir()
            (root / "refs/GRCh38.fa").write_text(">chrToy\nACGTACGT\n", encoding="ascii")
            (root / "raw/NA12878_R1.fastq.gz").touch()
            (root / "raw/NA12878_R2.fastq.gz").touch()
            stub_bin = root / "stub-bin"
            stub_bin.mkdir()
            log = root / "stub.log"
            bwa_stub = stub_bin / "bwa"
            bwa_stub.write_text(
                "#!/usr/bin/env bash\n"
                "set -u\n"
                "case \"$1\" in\n"
                "  index)\n"
                "    printf 'bwa-index\\n' >> \"$STUB_LOG\"\n"
                "    shift\n"
                "    while (($#)); do if [[ $1 == -a ]]; then shift 2; else fasta=$1; shift; fi; done\n"
                "    for suffix in amb ann bwt pac sa; do printf 'toy index\\n' > \"${fasta}.${suffix}\"; done\n"
                "    ;;\n"
                "  mem)\n"
                "    printf 'bwa-mem\\n' >> \"$STUB_LOG\"\n"
                "    echo 'synthetic upstream BWA failure' >&2\n"
                "    exit 23\n"
                "    ;;\n"
                "  *) echo \"unexpected bwa subcommand: $1\" >&2; exit 2 ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            samtools_stub = stub_bin / "samtools"
            samtools_stub.write_text(
                "#!/usr/bin/env bash\n"
                "set -u\n"
                "case \"$1\" in\n"
                "  sort)\n"
                "    printf 'samtools-sort\\n' >> \"$STUB_LOG\"\n"
                "    output=\n"
                "    while (($#)); do if [[ $1 == -o ]]; then shift; output=$1; fi; shift; done\n"
                "    cat >/dev/null\n"
                "    printf 'stub sorted BAM\\n' > \"$output\"\n"
                "    ;;\n"
                "  index) printf 'bam-index\\n' >> \"$STUB_LOG\" ;;\n"
                "  *) echo \"unexpected samtools subcommand: $1\" >&2; exit 2 ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            bwa_stub.chmod(0o755)
            samtools_stub.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{stub_bin}{os.pathsep}{environment.get('PATH', '')}"
            environment["STUB_LOG"] = str(log)

            result = run_bash(alignment, cwd=root, env=environment)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("synthetic upstream BWA failure", result.stderr)
            self.assertIn("Alignment pipeline failed (BWA or samtools sort); stopping before BAM indexing.", result.stderr)
            events = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(events[0], "bwa-index")
            self.assertCountEqual(events[1:], ["bwa-mem", "samtools-sort"])
            self.assertNotIn("bam-index", events)


class WESVcfContractTests(unittest.TestCase):
    def parse_fixture(self):
        records = []
        for line in FIXTURE.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                fields = line.split("\t")
                records.append(dict(zip(
                    ("chrom", "pos", "id", "ref", "alt", "qual", "filter", "info", "format", "sample"),
                    fields,
                )))
        return records

    def test_synthetic_fixture_encodes_filter_and_ad_dp_arithmetic(self):
        records = self.parse_fixture()
        self.assertEqual([(row["pos"], row["filter"]) for row in records],
                         [("2", "PASS"), ("4", "QD_lt_2"), ("6", "PASS"), ("8", ".")])
        genotype, ad, format_dp = records[0]["sample"].split(":")
        ref_ad, alt_ad = map(int, ad.split(","))
        self.assertEqual((genotype, ref_ad, alt_ad, int(format_dp)), ("0/1", 18, 12, 33))
        self.assertEqual(alt_ad / (ref_ad + alt_ad), 0.4)
        self.assertNotEqual(ref_ad + alt_ad, int(format_dp))
        self.assertEqual(records[2]["sample"].split(":")[1], "10,5,3")

    def test_displayed_pass_and_vaf_commands_produce_expected_tsv_with_bcftools(self):
        bcftools = shutil.which("bcftools")
        if not bcftools:
            self.skipTest("bcftools unavailable; install/use a bounded external build to run this integration contract")
        pass_block = find_block(lambda block: "bcftools view --apply-filters PASS" in block)
        vaf_block = find_block(lambda block: "bcftools query -f '%CHROM" in block and "NA12878_pass.vcf.gz" in block)
        self.assertIn("set -euo pipefail", pass_block)
        self.assertIn("--apply-filters PASS", pass_block)
        self.assertIn("%FILTER", vaf_block)
        self.assertIn("%AD", vaf_block)
        self.assertIn("%DP", vaf_block)
        self.assertIn('if ($5!="PASS"', vaf_block)
        self.assertIn('|| $4 ~ /,/', vaf_block)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vcf_dir = root / "vcf"
            vcf_dir.mkdir()
            filtered = vcf_dir / "NA12878_filtered.vcf.gz"
            passed = vcf_dir / "NA12878_pass.vcf.gz"
            output = vcf_dir / "NA12878_pass.withVAF.tsv"
            compressed = subprocess.run(
                [bcftools, "view", "--output-type", "z", "--output", str(filtered), str(FIXTURE)],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            )
            self.assertEqual(compressed.returncode, 0, compressed.stderr)

            pass_script = pass_block.replace("vcf/NA12878_filtered.vcf.gz", str(filtered))
            pass_script = pass_script.replace("vcf/NA12878_pass.vcf.gz", str(passed))
            result = run_bash(pass_script, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)

            vaf_script = vaf_block.replace("vcf/NA12878_pass.vcf.gz", str(passed))
            vaf_script = vaf_script.replace("vcf/NA12878_pass.withVAF.tsv", str(output))
            result = run_bash(vaf_script, cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            observed = output.read_text(encoding="utf-8")
            expected = (
                "CHROM\tPOS\tREF\tALT\tFILTER\tGT\tREF_AD\tALT_AD\tFORMAT_DP\tVAF\n"
                "chrToy\t2\tC\tT\tPASS\t0/1\t18\t12\t33\t0.4\n"
                "chrToy\t6\tA\tC,G\tPASS\t1/2\t10\t5\t19\tNA\n"
            )
            self.assertEqual(observed, expected)
            self.assertNotIn("QD_lt_2", observed)
            self.assertNotIn("chrToy\t8", observed)

    def test_displayed_vaf_contract_rejects_two_samples_before_writing_output(self):
        bcftools = shutil.which("bcftools")
        if not bcftools:
            self.skipTest("bcftools unavailable; multisample integration contract skipped")
        block = find_block(lambda code: "bcftools query -f '%CHROM" in code
                           and "NA12878_pass.vcf.gz" in code)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "vcf").mkdir()
            lines = []
            for line in FIXTURE.read_text(encoding="utf-8").splitlines():
                if line.startswith("#CHROM"):
                    line += "\tTOY_SECOND_SAMPLE"
                elif line and not line.startswith("#"):
                    line += "\t" + line.split("\t")[-1]
                lines.append(line)
            source = root / "two-samples.vcf"
            source.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = subprocess.run(
                [bcftools, "view", "-Oz", "-o", str(root / "vcf/NA12878_pass.vcf.gz"), str(source)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run_bash(block, cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Expected exactly one VCF sample", result.stderr)
            self.assertFalse((root / "vcf/NA12878_pass.withVAF.tsv").exists())


if __name__ == "__main__":
    unittest.main()
