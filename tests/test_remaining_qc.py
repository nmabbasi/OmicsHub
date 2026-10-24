"""Execute the QC guide's bounded integrity stages, not a biological pipeline."""
from html.parser import HTMLParser
from pathlib import Path
import gzip
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'tutorials/quality-control-fundamentals.html'


class DisplayedCode(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.named = {}
        self.blocks = []
        self.active = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.active = [dict(attrs).get('id'), []]

    def handle_data(self, data):
        if self.active is not None:
            self.active[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'pre' and self.active is not None:
            key, pieces = self.active
            code = ''.join(pieces)
            self.blocks.append(code)
            if key:
                self.named[key] = code
            self.active = None


def shown():
    return DisplayedCode(PAGE.read_text(encoding='utf-8'))


@unittest.skipUnless(shutil.which('bash'), 'Bash required for shown shell stages')
class QCIntegrityRuntimeTests(unittest.TestCase):
    def prepare(self, directory, algorithm='sha256'):
        raw = directory / 'raw'
        raw.mkdir()
        teaching_reads = (ROOT / 'files/text-processing-lesson/reads.fastq').read_bytes()
        for mate in ('R1', 'R2'):
            (raw / f'sample_{mate}.fastq.gz').write_bytes(gzip.compress(teaching_reads, mtime=0))
        if algorithm:
            self.manifest(directory, algorithm)

    def manifest(self, directory, algorithm):
        name = 'checksums.txt' if algorithm == 'sha256' else 'md5checksums.txt'
        rows = []
        for mate in ('R1', 'R2'):
            filename = f'sample_{mate}.fastq.gz'
            digest = hashlib.new(algorithm, (directory/'raw'/filename).read_bytes()).hexdigest()
            rows.append(f'{digest}  {filename}')
        (directory/'raw'/name).write_text('\n'.join(rows)+'\n', encoding='ascii')

    def run_stage(self, directory):
        return subprocess.run(['bash', '-c', shown().named['qc-integrity-stage']],
                              cwd=directory, capture_output=True, text=True, timeout=15)

    def test_sha256_only_provider_relative_names_succeed(self):
        self.check_success('sha256')

    def test_md5_only_provider_relative_names_succeed(self):
        self.check_success('md5')

    def check_success(self, algorithm):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory, algorithm)
            result = self.run_stage(directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('integrity checks passed', result.stdout)
            self.assertEqual(result.stdout.count(': OK'), 2)
            self.assertTrue((directory/'logs/checksum_validation.log').is_file())

    def test_missing_provider_manifest_stops(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory, None)
            result = self.run_stage(directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Missing provider', result.stderr)
            self.assertNotIn('checks passed', result.stdout)

    def test_checksum_mismatch_is_not_masked_by_valid_gzip(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            self.manifest(directory, 'md5')
            path = directory/'raw/sample_R1.fastq.gz'
            content = gzip.decompress(path.read_bytes())
            path.write_bytes(gzip.compress(content+b'\n', mtime=0))
            result = self.run_stage(directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('FAILED', result.stdout)
            self.assertNotIn('checks passed', result.stdout)

    def test_invalid_gzip_fails_even_when_checksum_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.prepare(directory)
            (directory/'raw/sample_R1.fastq.gz').write_bytes(b'not gzip\n')
            self.manifest(directory, 'sha256')
            result = self.run_stage(directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout.count(': OK'), 2)
            self.assertNotIn('checks passed', result.stdout)

    def test_each_shell_stage_has_its_own_failure_policy_and_valid_syntax(self):
        for code in shown().blocks[:6]:
            with self.subTest(start=code[:75]):
                self.assertTrue(code.startswith('set -euo pipefail\n'))
                result = subprocess.run(['bash', '-n'], input=code, capture_output=True,
                                        text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_failed_depth_command_cannot_publish_zero_as_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            executable = directory/'samtools'
            executable.write_text('#!/bin/sh\necho "intentional tool failure" >&2\nexit 7\n')
            executable.chmod(0o755)
            env = dict(os.environ, PATH=str(directory)+os.pathsep+os.environ['PATH'])
            code = shown().named['qc-depth-stage'].split('# Target breadth:')[0]
            result = subprocess.run(['bash', '-c', code], cwd=directory, env=env,
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotEqual((directory/'qc/coverage_mean_depth.txt').read_text().strip(), '0')

    def test_failed_aligner_stops_before_sorting_or_duplicate_marking(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            tools = {
                'bwa-mem2': '#!/bin/sh\nif [ "$1" = index ]; then exit 0; fi\necho "intentional alignment failure" >&2\nexit 9\n',
                'samtools': '#!/bin/sh\nif [ "$1" = view ]; then cat >/dev/null; exit 0; fi\nprintf "%s\\n" "$*" >> "$TEST_EVENTS"\n',
                'picard': '#!/bin/sh\necho picard >> "$TEST_EVENTS"\n',
            }
            for name, source in tools.items():
                executable = directory/name
                executable.write_text(source)
                executable.chmod(0o755)
            events = directory/'events.txt'
            env = dict(os.environ, PATH=str(directory)+os.pathsep+os.environ['PATH'],
                       TEST_EVENTS=str(events))
            code = next(code for code in shown().blocks if 'bwa-mem2 mem' in code)
            result = subprocess.run(['bash', '-c', code], cwd=directory, env=env,
                                    capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(events.exists(), 'sorting/indexing/marking must not run after alignment fails')


class QCScientificScopeTests(unittest.TestCase):
    def test_depth_explicitly_uses_the_whole_reference_denominator(self):
        code = shown().named['qc-depth-stage']
        self.assertIn('samtools depth -aa ', code)
        self.assertNotIn('else print 0', code)
        text = PAGE.read_text(encoding='utf-8')
        self.assertIn('contigs with no mapped reads', text)
        self.assertIn('it does not report mean depth', text)

    def test_verifybamid2_contract_is_not_legacy_vcf_syntax(self):
        blocks = [code for code in shown().blocks if '--SVDPrefix' in code]
        self.assertEqual(len(blocks), 1)
        code = blocks[0]
        self.assertIn('verifybamid2 --BamFile', code)
        self.assertIn('--Reference ../../reference/genome.fa', code)
        self.assertIn('cd qc/verifybamid2', code)
        self.assertIn('result.selfSM', code)
        self.assertNotIn('verifyBamID --bam', code)
        self.assertNotIn('--Output', code)
        self.assertIn('not an executed contamination analysis', PAGE.read_text(encoding='utf-8'))


@unittest.skipUnless(shutil.which('samtools') and shutil.which('bash'),
                     'optional real SAMtools required for the coverage denominator contract')
class QCDepthSamtoolsRuntimeTests(unittest.TestCase):
    def test_unused_reference_contig_remains_in_the_displayed_mean_denominator(self):
        # Artificial mapping of a public teaching read: a software contract only.
        read = (ROOT/'files/text-processing-lesson/reads.fastq').read_text().splitlines()
        sequence, quality = read[1], read[3]
        length = len(sequence)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory/'aligned').mkdir()
            sam = '\n'.join([
                '@HD\tVN:1.6\tSO:coordinate',
                f'@SQ\tSN:covered\tLN:{length*2}',
                f'@SQ\tSN:unused\tLN:{length*2}',
                f'contract_only\t0\tcovered\t1\t60\t{length}M\t*\t0\t0\t{sequence}\t{quality}',
            ])+'\n'
            (directory/'fixture.sam').write_text(sam)
            prepared = subprocess.run(
                ['samtools', 'view', '-b', '-o', 'aligned/sample.dedup.bam', 'fixture.sam'],
                cwd=directory, capture_output=True, text=True, timeout=15)
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            code = shown().named['qc-depth-stage'].split('# Target breadth:')[0]
            result = subprocess.run(['bash', '-c', code], cwd=directory,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            mean = float((directory/'qc/coverage_mean_depth.txt').read_text())
            self.assertAlmostEqual(mean, length/(length*4))
            original = subprocess.run(['samtools', 'depth', '-a', 'aligned/sample.dedup.bam'],
                                      cwd=directory, capture_output=True, text=True, timeout=15)
            self.assertEqual(original.returncode, 0, original.stderr)
            values = [int(row.split('\t')[2]) for row in original.stdout.splitlines()]
            self.assertGreater(sum(values)/len(values), mean)


if __name__ == '__main__':
    unittest.main()
