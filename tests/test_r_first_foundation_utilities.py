"""R-first foundation examples: real local execution on synthetic fixtures only."""
from html.parser import HTMLParser
from pathlib import Path
import gzip
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
R = shutil.which('Rscript')

class Blocks(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.blocks = {}
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.current = dict(attrs).get('id', '__unidentified__')
            self.blocks[self.current] = ''
    def handle_endtag(self, tag):
        if tag == 'pre': self.current = None
    def handle_data(self, data):
        if self.current: self.blocks[self.current] += data

def source(slug):
    return (ROOT / 'tutorials' / f'{slug}.html').read_text()

def block(slug, identifier):
    return Blocks(source(slug)).blocks[identifier]

@unittest.skipUnless(R, 'Rscript is required for real R example execution')
class RFoundationUtilityTests(unittest.TestCase):
    def run_r(self, script, args, cwd):
        path = Path(cwd) / 'example.R'
        path.write_text(script)
        return subprocess.run([R, '--vanilla', str(path), *map(str,args)], cwd=cwd,
                              text=True, capture_output=True, timeout=30)

    def test_git_tsv_parser_preserves_text_and_rejects_missing_headers(self):
        code = block('git-github-bioinformatics', 'git-tsv-parser-r')
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / 'samples.tsv'
            fixture.write_text('sample\treads\nsynthetic_A\t1200\nS002\t0007\n')
            result = self.run_r(code, [fixture], folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), ['synthetic_A 1200','S002 0007'])
            fixture.write_text('name\treads\nsynthetic_A\t1200\n')
            result = self.run_r(code, [fixture], folder)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Input must have 'sample' and 'reads' header columns", result.stderr)

    def test_streaming_fastq_checks_real_compressed_synthetic_records(self):
        code = block('biological-data-formats', 'fastq-mates-r')
        good1 = '@read_A/1 instrument\nACGT\n+\n!!!!\n'
        good2 = '@read_A/2 instrument\nTGCA\n+\n####\n'
        cases = [
            ('paired suffix normalization', good1, good2, True, '1 paired records'),
            ('both empty', '', '', False, 'FAIL: both files are empty'),
            ('different counts', good1, '', False, 'different record counts'),
            ('different identifiers', good1, good2.replace('read_A','read_B'), False, 'identifiers/order differ'),
            ('incomplete record', good1, '@read_A/2\nTGCA\n', False, 'incomplete four-line record'),
            ('wrong quality length', good1, good2.replace('####','###'), False, 'malformed record'),
            ('wrong plus line', good1, good2.replace('\n+\n','\n-\n'), False, 'malformed record'),
        ]
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder)/'r1.fastq.gz', Path(folder)/'r2.fastq.gz']
            for name, r1, r2, ok, expected in cases:
                with self.subTest(name=name):
                    for path, text in zip(paths,[r1,r2]):
                        with gzip.open(path,'wt') as handle: handle.write(text)
                    result = self.run_r(code, paths, folder)
                    self.assertEqual(result.returncode == 0, ok, result.stderr)
                    self.assertIn(expected, result.stdout + result.stderr)

class RFirstSourceContractTests(unittest.TestCase):
    def test_r_first_utility_routes_and_r_project_wrapper(self):
        for slug, r_id, py_id in [
            ('git-github-bioinformatics','git-parser-r-route','git-parser-python-route'),
            ('biological-data-formats','fastq-mates-r-route','fastq-mates-python-route'),
        ]:
            text = source(slug)
            self.assertLess(text.index(r_id), text.index(py_id))
        project = source('reproducible-project-structure')
        self.assertIn('qc_counts.R', project)
        self.assertNotIn('qc_counts.py', project)
        self.assertIn('reports/analysis.Rmd', project)
        self.assertNotIn('R: not installed (optional)', project)
        hpc = source('hpc-submission-part1')
        self.assertIn('srun Rscript --vanilla my_script.R', hpc)
        self.assertNotIn('python=3.8', hpc)

    def test_visualization_setup_list_is_explicitly_closed(self):
        text = source('data-visualization-fundamentals')
        setup = text[text.index('<h3>Run the R Markdown lab</h3>'):text.index('<h2>Inspect distributions')]
        self.assertEqual(len(re.findall(r'<ol\b',setup)),len(re.findall(r'</ol>',setup)))
        self.assertLess(setup.index('</ol>'),setup.index('<details'))

if __name__ == '__main__': unittest.main()
