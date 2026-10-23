"""Exercise the lesson's displayed commands on invented inputs, never research files."""
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT/'tutorials/command-line-part2.html'
FIXTURE = ROOT/'files/text-processing-lesson'
SEQKIT = os.environ.get('SEQKIT_EXECUTABLE') or shutil.which('seqkit')

class CodeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks=[]; self.named={}; self.current=None; self.name=None
        self.feed(PAGE.read_text())
    def handle_starttag(self,tag,attrs):
        if tag=='pre':self.current=[]; self.name=dict(attrs).get('id')
    def handle_data(self,data):
        if self.current is not None:self.current.append(data)
    def handle_endtag(self,tag):
        if tag=='pre' and self.current is not None:
            code=''.join(self.current);self.blocks.append(code)
            if self.name:self.named[self.name]=code
            self.current=None

class TextProcessingBase:
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.parent=Path(self.temp.name)
        self.parser=CodeParser()
        self.run_code(self.parser.named['cli-part2-setup'],cwd=self.parent)
        self.work=self.parent/'cli-part2-practice'
    def tearDown(self):self.temp.cleanup()
    def run_code(self,code,cwd=None,check=True):
        env=os.environ.copy()
        if SEQKIT:env['PATH']=str(Path(SEQKIT).resolve().parent)+os.pathsep+env['PATH']
        result=subprocess.run(['bash','-c',code],cwd=cwd or self.work,env=env,text=True,capture_output=True)
        if check:self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return result

@unittest.skipUnless(shutil.which('bash'),'Bash is required for these displayed shell examples')
class TextProcessingOfflineTests(TextProcessingBase,unittest.TestCase):
    def test_displayed_setup_reproduces_every_downloadable_input_exactly(self):
        for name in ['sequences.fasta','reads.fastq','malformed.fastq','data.tsv','genes_of_interest.txt']:
            with self.subTest(name=name):self.assertEqual((self.work/name).read_bytes(),(FIXTURE/name).read_bytes())
    def test_all_displayed_shell_examples_have_valid_bash_syntax(self):
        for number,code in enumerate(self.parser.blocks):
            with self.subTest(block=number):
                result=subprocess.run(['bash','-n'],input=code,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)
    def test_header_count_and_header_extraction_match_the_wrapped_fixture(self):
        count=next(code for code in self.parser.blocks if "grep -c '^>'" in code)
        self.assertEqual(self.run_code(count).stdout.strip(),'3')
        headers=next(code for code in self.parser.blocks if 'headers.txt' in code)
        self.run_code(headers)
        self.assertEqual([line.split()[0] for line in (self.work/'headers.txt').read_text().splitlines()],
                         ['gene_A_unwrapped','gene_B_wrapped','gene_C_negative'])
    def test_table_filters_and_gene_frequencies_match_the_displayed_feedback(self):
        self.run_code(self.parser.named['cli-part2-tables'])
        self.assertEqual((self.work/'filtered_counts.tsv').read_text(),
                         'gene_id\tsample\tcount\nGENE_A\tS1\t120\nGENE_C\tS2\t200\n')
        frequencies={parts[1]:int(parts[0]) for line in (self.work/'gene_counts.txt').read_text().splitlines() if (parts:=line.split())}
        self.assertEqual(frequencies,{'GENE_A':2,'GENE_B':1,'GENE_C':1})
    def test_exact_id_matching_handles_match_no_match_and_empty_list(self):
        for ids,expected in [('GENE_A\nGENE_C\n',['GENE_A','GENE_A','GENE_C']),('NOT_PRESENT\n',[]),('',[])]:
            with self.subTest(ids=ids):
                (self.work/'genes_of_interest.txt').write_text(ids)
                self.run_code(self.parser.named['cli-part2-gene-ids'])
                actual=[line.split('\t')[0] for line in (self.work/'genes_subset.tsv').read_text().splitlines()]
                self.assertEqual(actual,expected)
    def test_toy_awk_conversion_is_successful_but_not_input_validation(self):
        code=self.parser.named['cli-part2-fastq-toy']
        self.run_code(code)
        self.assertEqual((self.work/'reads.toy.fasta').read_text(),'>read_1\nATGCGTAA\n>read_2\nCCATGCGT\n')
        self.run_code(code.replace('reads.fastq','malformed.fastq'))
        self.assertEqual((self.work/'reads.toy.fasta').read_text(),'>bad_length\nATGC\n')
    def test_lesson_explains_limits_and_links_only_invented_inputs(self):
        text=PAGE.read_text()
        for phrase in ['invented','not a validator','only after a successful exit','not biological observations','other operating systems']:
            self.assertIn(phrase,text)
        self.assertIn('first run <code>cd ..</code> to return to its parent directory',text)
        self.assertIn('otherwise the setup creates a nested practice directory',text)
        self.assertNotIn('\u2014',text)
        for name in ['sequences.fasta','reads.fastq','malformed.fastq','data.tsv','genes_of_interest.txt']:
            self.assertIn('href="../files/text-processing-lesson/'+name+'"',text)

@unittest.skipUnless(SEQKIT and shutil.which('bash'),'Set SEQKIT_EXECUTABLE for optional real SeqKit fixture checks')
class TextProcessingSeqKitTests(TextProcessingBase,unittest.TestCase):
    def test_record_search_finds_the_cross_line_motif_and_the_variation(self):
        result=self.run_code(self.parser.named['cli-part2-motif'])
        self.assertEqual(result.stdout.splitlines(),['gene_A_unwrapped','gene_B_wrapped'])
        self.assertIn('2:ATGCGTAA',(self.work/'matching_lines.txt').read_text())
        self.assertIn('3->gene_B_wrapped',(self.work/'matching_lines.txt').read_text())
        varied=self.run_code("seqkit grep -s -P -p TTTT sequences.fasta | seqkit seq -n -i")
        self.assertEqual(varied.stdout.strip(),'gene_C_negative')
    def test_record_parser_matches_valid_toy_conversion(self):
        self.run_code(self.parser.named['cli-part2-fastq-toy'])
        self.run_code(self.parser.named['cli-part2-fastq-record-aware'])
        self.assertEqual((self.work/'reads.checked.fasta').read_bytes(),(self.work/'reads.toy.fasta').read_bytes())
        self.assertEqual(list(self.work.glob('reads.checked.fasta.tmp.*')),[])
    def test_malformed_record_rejection_and_no_partial_publication(self):
        result=self.run_code(self.parser.named['cli-part2-malformed'])
        self.assertIn('Rejected the malformed FASTQ as expected.',result.stdout)
        self.assertEqual((self.work/'misleading.fasta').read_text(),'>bad_length\nATGC\n')
        self.assertFalse((self.work/'rejected.fasta.tmp').exists())
        code=self.parser.named['cli-part2-fastq-record-aware'].replace('input=reads.fastq','input=malformed.fastq').replace('output=reads.checked.fasta','output=must-not-publish.fasta')
        result=self.run_code(code,check=False)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.work/'must-not-publish.fasta').exists())
        self.assertEqual(list(self.work.glob('must-not-publish.fasta.tmp.*')),[])

if __name__=='__main__':unittest.main()
