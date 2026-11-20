"""Bounded source/runtime contracts for the CITE-seq WNN tutorial."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

from test_remaining_qc import DisplayedCode

ROOT = Path(__file__).resolve().parents[1]
CITE = ROOT/'tutorials/cite-seq-wnn-multiomics.html'
CITE_STAGES = ['cite-build-stage', 'cite-rna-stage', 'cite-adt-stage',
               'cite-wnn-stage', 'cite-plots-stage']


def cite():
    return DisplayedCode(CITE.read_text(encoding='utf-8')).named


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
        code = full[full.index('# Bound each requested range'):full.index('# Find multi-modal')]
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


if __name__ == '__main__':
    unittest.main()
