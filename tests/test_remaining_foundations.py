"""Run the actual bundled plotting data and bounded reference path mechanics."""
from pathlib import Path
import csv
import gzip
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_remaining_qc import DisplayedCode

ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'files/tutorial-examples/data-visualization-fundamentals'
SCIENCE=all(importlib.util.find_spec(module) is not None for module in ['numpy','pandas','sklearn','seaborn','umap'])


def ggplot_ready():
    rscript=shutil.which('Rscript')
    if not rscript or importlib.util.find_spec('PIL') is None:
        return False
    try:
        check=subprocess.run([rscript,'-e','quit(status=if(requireNamespace("ggplot2",quietly=TRUE)) 0L else 1L)'],
                             capture_output=True,text=True,timeout=20)
        return check.returncode==0
    except subprocess.TimeoutExpired:
        return False


def stages(slug):
    return DisplayedCode((ROOT/'tutorials'/f'{slug}.html').read_text(encoding='utf-8')).named


class FoundationSourceTests(unittest.TestCase):
    def test_plot_fixture_cutoff_and_handoff_remain_explicit(self):
        code=stages('data-visualization-fundamentals')
        self.assertIn('logcpm.var(axis=1) > 0.01',code['visualization-pca-stage'])
        self.assertIn('pca_full.tsv',code['visualization-pca-stage'])
        self.assertIn('pca_full.tsv',code['visualization-umap-stage'])
        self.assertIn('tiny synthetic fixture',code['visualization-pca-stage'])

    def test_r_volcano_export_explicitly_keeps_white_background(self):
        self.assertIn('bg = "white"',stages('data-visualization-fundamentals')['visualization-volcano-stage'])


@unittest.skipUnless(ggplot_ready(),'optional R/ggplot2 and Pillow required for real volcano PNG check')
class VolcanoWhiteBackgroundTests(unittest.TestCase):
    def test_exact_r_stage_writes_an_opaque_white_png(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            (directory/'results').mkdir()
            shutil.copyfile(FIXTURES/'deseq2_results.tsv',directory/'results/deseq2_results.tsv')
            script=directory/'volcano.R'
            script.write_text(stages('data-visualization-fundamentals')['visualization-volcano-stage']+'\n')
            run=subprocess.run(['Rscript',str(script)],cwd=directory,capture_output=True,text=True,timeout=45)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            image=Image.open(directory/'results/volcano.png').convert('RGBA')
            for xy in [(0,0),(image.width-1,0),(0,image.height-1),(image.width-1,image.height-1)]:
                self.assertEqual(image.getpixel(xy),(255,255,255,255))


@unittest.skipUnless(SCIENCE,'optional plotting stack (numpy, pandas, sklearn, seaborn and umap) required')
class VisualizationRealFixtureTests(unittest.TestCase):
    def test_fixture_retains_five_genes_not_zero(self):
        import numpy as np
        import pandas as pd
        counts=pd.read_csv(FIXTURES/'counts.tsv',sep='\t',index_col=0)
        variance=np.log2(counts.div(counts.sum(axis=0),axis=1)*1e6+1).var(axis=1)
        self.assertEqual(len(variance),10)
        self.assertEqual(int((variance>0.01).sum()),5)
        self.assertEqual(int((variance>0.5).sum()),0)

    def prepare(self,directory):
        (directory/'data').mkdir()
        for name in ['counts.tsv','qc_metrics.tsv','deseq2_results.tsv']:
            shutil.copyfile(FIXTURES/name,directory/'data'/name)

    def run_code(self,code,directory):
        env=dict(os.environ,MPLBACKEND='Agg',NUMBA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        return subprocess.run([sys.executable,'-c',code],cwd=directory,env=env,
                              capture_output=True,text=True,timeout=180)

    def test_exact_pca_then_umap_route_produces_aligned_coordinates_and_figures(self):
        import numpy as np
        import pandas as pd
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            self.prepare(directory)
            code=stages('data-visualization-fundamentals')
            for name in ['visualization-pca-stage','visualization-umap-stage']:
                run=self.run_code(code[name],directory)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            pca=pd.read_csv(directory/'results/pca_full.tsv',sep='\t',index_col='sample')
            umap=pd.read_csv(directory/'results/umap_coords.tsv',sep='\t',index_col='sample')
            counts=pd.read_csv(FIXTURES/'counts.tsv',sep='\t',index_col=0)
            self.assertEqual(list(pca.index),list(counts.columns))
            self.assertEqual(list(umap.index),list(counts.columns))
            self.assertEqual(pca.shape[1],5)
            self.assertEqual(umap.shape[1],2)
            self.assertTrue(np.isfinite(pca.to_numpy()).all())
            self.assertTrue(np.isfinite(umap.to_numpy()).all())
            for name in ['pca_plot.png','umap_plot.png']:
                self.assertGreater((directory/'results'/name).stat().st_size,1000)

    def test_constant_fixture_still_stops_instead_of_forcing_a_plot(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            self.prepare(directory)
            counts=pd.read_csv(directory/'data/counts.tsv',sep='\t',index_col=0)
            counts.iloc[:,:]=1
            counts.to_csv(directory/'data/counts.tsv',sep='\t')
            run=self.run_code(stages('data-visualization-fundamentals')['visualization-pca-stage'],directory)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('at least two samples and two retained genes',run.stderr)
            self.assertFalse((directory/'results/pca_full.tsv').exists())


@unittest.skipUnless(all(shutil.which(command) for command in ['bash','sha256sum','awk','gzip','sort']),
                     'reference shell utilities required')
class ReferenceHandoffRuntimeTests(unittest.TestCase):
    def prepare(self,directory):
        refs=directory/'refs';refs.mkdir()
        # Deliberately tiny artificial references: software/path tests, not human-reference validation.
        data={
            'GRCh38.p14.genome.fa.gz':b'>chr1\nACGT\n>chrM\nAA\n',
            'gencode.v46.chr_patch_hapl_scaff.annotation.gtf.gz':
                b'#synthetic fixture\nchr1\ttest\tgene\t1\t4\t.\t+\t.\tgene_id "test1";\nchrM\ttest\tgene\t1\t2\t.\t+\t.\tgene_id "test2";\n'
        }
        for name,content in data.items(): (refs/name).write_bytes(gzip.compress(content,mtime=0))
        return refs

    def test_manifest_runs_from_refs_and_hashes_the_actual_compressed_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);refs=self.prepare(directory)
            code=stages('reference-genomes-annotation')['reference-manifest-stage']
            run=subprocess.run(['bash','-c',code],cwd=refs,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stderr)
            with (refs/'reference_manifest.tsv').open(newline='') as handle:
                rows=list(csv.DictReader(handle,delimiter='\t'))
            self.assertEqual(len(rows),2)
            for row in rows:
                path=directory/row['file_path']
                self.assertTrue(path.is_file())
                self.assertEqual(row['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(row['region_scope'],'ALL')

    def test_missing_compressed_file_never_claims_complete_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);refs=self.prepare(directory)
            (refs/'GRCh38.p14.genome.fa.gz').unlink()
            run=subprocess.run(['bash','-c',stages('reference-genomes-annotation')['reference-manifest-stage']],
                               cwd=refs,capture_output=True,text=True,timeout=15)
            self.assertNotEqual(run.returncode,0)
            self.assertNotIn('look complete',run.stdout)

    def test_exact_gtf_pipeline_preserves_full_sequence_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);refs=self.prepare(directory)
            stage=stages('reference-genomes-annotation')['reference-index-stage']
            code='zcat '+stage.split('\nzcat ',1)[1]
            run=subprocess.run(['bash','-c',code],cwd=refs,capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual((refs/'gtf_contigs.txt').read_text().splitlines(),['chr1','chrM'])


if __name__=='__main__':
    unittest.main()
