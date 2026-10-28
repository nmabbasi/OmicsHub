"""Bounded source/runtime contracts; mock NanoPlot is not real long-read QC."""
from pathlib import Path
import gzip
import os
import shutil
import subprocess
import tempfile
import unittest

from test_remaining_qc import DisplayedCode

ROOT = Path(__file__).resolve().parents[1]
CITE = ROOT/'tutorials/cite-seq-wnn-multiomics.html'
LONGREAD = ROOT/'tutorials/long-read-pacbio-nanopore.html'
CITE_STAGES = ['cite-build-stage', 'cite-rna-stage', 'cite-adt-stage',
               'cite-wnn-stage', 'cite-plots-stage']


def cite():
    return DisplayedCode(CITE.read_text(encoding='utf-8')).named


def longread_stage():
    return DisplayedCode(LONGREAD.read_text(encoding='utf-8')).named['longread-nanoplot-stage']


class CITEWorkflowContractTests(unittest.TestCase):
    def test_named_species_preparation_precedes_seurat_name_normalization(self):
        code = cite()['cite-build-stage']
        self.assertLess(code.index('CollapseSpeciesExpressionMatrix('), code.index('CreateSeuratObject('))
        self.assertIn('prefix = "HUMAN_", controls = "MOUSE_"', code)
        self.assertIn('anyDuplicated(rownames(rna_mat))', code)

    def test_wnn_uses_available_reduction_dimensions(self):
        code = cite()['cite-wnn-stage']
        self.assertIn('ncol(Embeddings(seurat_obj, reduction = "pca"))', code)
        self.assertIn('ncol(Embeddings(seurat_obj, reduction = "apca"))', code)
        self.assertIn('seq_len(min(18L, adt_available))', code)
        self.assertIn('dims.list = list(rna_dims, adt_dims)', code)
        self.assertNotIn('1:18', code)
        self.assertIn('adt_npcs < 2L', cite()['cite-adt-stage'])

    def test_all_five_figures_explicitly_have_white_backgrounds(self):
        lines = [line for line in cite()['cite-plots-stage'].splitlines() if 'ggsave(' in line]
        self.assertEqual(len(lines), 5)
        self.assertTrue(all('bg = "white"' in line for line in lines))

    @unittest.skipUnless(shutil.which('Rscript'), 'Rscript optional for syntax and pure dimension logic')
    def test_all_displayed_stages_parse_as_one_r_script(self):
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary)/'cite_seq_wnn.R'
            script.write_text('\n\n'.join(cite()[name] for name in CITE_STAGES)+'\n')
            result = subprocess.run(['Rscript', '-e', 'invisible(parse(file=commandArgs(TRUE)[1]))', str(script)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('Rscript'), 'Rscript optional for pure dimension logic')
    def test_exact_dimension_logic_accepts_small_panels_and_rejects_too_few_pcs(self):
        full = cite()['cite-wnn-stage']
        code = full[full.index('rna_available <-'):full.index('# Find multi-modal')]
        for rna, adt, valid in [(50, 12, True), (10, 3, True), (30, 1, False), (0, 12, False)]:
            with self.subTest(rna=rna, adt=adt):
                setup = ('seurat_obj <- NULL\n'
                         f'Embeddings <- function(object,reduction) matrix(0,nrow=4,ncol=c(pca={rna}L,apca={adt}L)[[reduction]])\n')
                suffix = f'\nstopifnot(length(rna_dims)==min(30L,{rna}L),length(adt_dims)==min(18L,{adt}L))' if valid else ''
                result = subprocess.run(['Rscript', '-e', setup+code+suffix],
                                        capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode == 0, valid, result.stdout+result.stderr)
                if not valid:
                    self.assertIn('Need at least two PCs', result.stderr)

    @unittest.skipUnless(os.environ.get('CITESEQ_TEST_INPUT_DIR') and shutil.which('Rscript'),
                         'optional explicit public paired RDS input directory required for real Seurat run')
    def test_full_displayed_route_with_explicit_public_paired_inputs(self):
        inputs = Path(os.environ['CITESEQ_TEST_INPUT_DIR']).resolve()
        env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project/'data').mkdir()
            for name in ['rna_counts.rds', 'adt_counts.rds']:
                self.assertTrue((inputs/name).is_file())
                shutil.copyfile(inputs/name, project/'data'/name)
            script = project/'cite_seq_wnn.R'
            script.write_text('\n\n'.join(cite()[name] for name in CITE_STAGES)+'\n')
            run = subprocess.run(['Rscript', str(script)], cwd=project, env=env,
                                 capture_output=True, text=True, timeout=240)
            self.assertEqual(run.returncode, 0, run.stdout[-3000:]+run.stderr[-6000:])
            check = ('suppressPackageStartupMessages(library(Seurat));'
                     'x<-readRDS("results/seurat_wnn_integrated.rds");'
                     'stopifnot(all(c("RNA.weight","ADT.weight") %in% colnames(x[[]])), '
                     '"wnn.umap" %in% Reductions(x), "wsnn" %in% Graphs(x), '
                     'all(is.finite(x$RNA.weight)),all(is.finite(x$ADT.weight)));'
                     'cat(ncol(x),"cells",ncol(Embeddings(x,"apca")),"ADT PCs\\n")')
            verify = subprocess.run(['Rscript', '-e', check], cwd=project, env=env,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(verify.returncode, 0, verify.stderr)
            for name in ['wnn_umap.png','rna_weight.png','adt_weight.png','cd4_rna.png','cd4_adt.png']:
                self.assertGreater((project/'results'/name).stat().st_size, 0)
            try:
                from PIL import Image
            except ImportError:
                return  # R route and file existence still checked; Pillow is optional.
            for png in (project/'results').glob('*.png'):
                image = Image.open(png).convert('RGBA')
                for xy in [(0,0),(image.width-1,0),(0,image.height-1),(image.width-1,image.height-1)]:
                    self.assertEqual(image.getpixel(xy), (255,255,255,255), png.name)


@unittest.skipUnless(shutil.which('bash'), 'Bash required for the long-read stage contract')
class LongReadShellRuntimeTests(unittest.TestCase):
    def setup_project(self, project, mode='success', input_exists=True):
        if input_exists:
            source = (ROOT/'files/text-processing-lesson/reads.fastq').read_bytes()
            (project/'reads.fastq.gz').write_bytes(gzip.compress(source, mtime=0))
        tool = project/'NanoPlot'
        tool.write_text('''#!/bin/sh
# An explicit test double: no reads are analyzed and no scientific report is made.
echo called > "$TEST_CALL"
while [ "$#" -gt 0 ]; do
  if [ "$1" = --outdir ]; then outdir="$2"; shift 2; else shift; fi
done
mkdir -p "$outdir"
if [ "$TEST_MODE" = failure ]; then exit 7; fi
printf 'mock HTML report\\n' > "$outdir/NanoPlot-report.html"
if [ "$TEST_MODE" != missing_stats ]; then printf 'mock statistics\\n' > "$outdir/NanoStats.txt"; fi
if [ "$TEST_MODE" = empty_html ]; then : > "$outdir/NanoPlot-report.html"; fi
''')
        tool.chmod(0o755)
        return dict(os.environ, PATH=str(project)+os.pathsep+os.environ['PATH'],
                    TEST_CALL=str(project/'called.txt'), TEST_MODE=mode)

    def run_stage(self, project, env):
        return subprocess.run(['bash', '-c', longread_stage()], cwd=project, env=env,
                              capture_output=True, text=True, timeout=15)

    def test_mock_complete_reports_succeed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_stage(project, self.setup_project(project))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('both expected reports are non-empty', result.stdout)

    def test_missing_input_does_not_run_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            result = self.run_stage(project, self.setup_project(project, input_exists=False))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Missing or empty input', result.stderr)
            self.assertFalse((project/'called.txt').exists())

    def test_corrupt_gzip_does_not_run_tool(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            env = self.setup_project(project)
            (project/'reads.fastq.gz').write_bytes(b'not gzip\n')
            result = self.run_stage(project, env)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((project/'called.txt').exists())

    def test_existing_output_does_not_run_tool_or_reuse_old_reports(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            env = self.setup_project(project)
            (project/'nanoplot_qc').mkdir()
            (project/'nanoplot_qc/NanoPlot-report.html').write_text('old report\n')
            result = self.run_stage(project, env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('already exists', result.stderr)
            self.assertFalse((project/'called.txt').exists())

    def test_failed_tool_or_incomplete_reports_never_claim_success(self):
        for mode in ['failure','missing_stats','empty_html']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                result = self.run_stage(project, self.setup_project(project, mode))
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('both expected reports are non-empty', result.stdout)

    def test_displayed_stage_has_valid_bash_syntax(self):
        result = subprocess.run(['bash', '-n'], input=longread_stage(), capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
