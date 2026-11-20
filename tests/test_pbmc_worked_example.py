#!/usr/bin/env python3
"""Guards for the narrowly reviewed public PBMC worked example; stdlib only."""
from pathlib import Path
import hashlib
import html
import json
import re
import struct
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_SHA256 = 'ae3d41dec12b09a51865e692381014f813a0df8d30db29115be2d269e03df81a'
OLD_VALIDITY = '<li>Good-looking UMAPs are necessary but not sufficient evidence of biological validity: batch effects, normalization artifacts, or inappropriate gene selection can create misleading visual separation.</li>'
OLD_RANDOM = '<li>UMAP is non-deterministic by default; set random seeds for reproducible embeddings when necessary (Seurat and Scanpy allow RNG control).</li>'


class PbmcWorkedExampleTests(unittest.TestCase):
    def test_python_analysis_script_fingerprint_is_preserved(self):
        data = (ROOT / 'tutorials/scrna-seq-basics.html').read_bytes()
        blocks = re.findall(r'<pre><code>([\s\S]*?)</code></pre>', data.decode('utf-8'))
        script = next(html.unescape(b) for b in blocks if b.startswith('# Python script:'))
        self.assertEqual(hashlib.sha256((script.rstrip() + '\n').encode()).hexdigest(), SCRIPT_SHA256)

    def test_download_contains_verbatim_script_lock_and_real_run_evidence(self):
        with zipfile.ZipFile(ROOT / 'downloads/pbmc3k-tested-scanpy.zip') as z:
            self.assertIsNone(z.testzip())
            self.assertEqual(hashlib.sha256(z.read('scripts/01_scanpy_qc_clustering.py')).hexdigest(), SCRIPT_SHA256)
            lock = z.read('requirements-tested.txt').decode()
            for requirement in ['scanpy==1.11.5', 'scikit-misc==0.5.2', 'igraph==0.11.9', 'leidenalg==0.10.2']:
                self.assertIn(requirement, lock)
            s = json.loads(z.read('run-summary.json'))
            self.assertEqual(s['input_shape'], [2700, 32738])
            self.assertEqual(s['output_shape'], [2638, 2000])
            self.assertEqual(list(s['checkpoints'].values()), [2700, 2700, 2695, 2638])
            self.assertEqual(sum(s['cluster_sizes'].values()), 2638)
            self.assertEqual(s['n_clusters'], 9)
            repeat = json.loads(z.read('repeat-comparison.json'))
            self.assertTrue(repeat['same_leiden_labels'])
            self.assertEqual(repeat['adjusted_rand_index'], 1.0)
            self.assertEqual(repeat['umap_max_absolute_difference'], 0.0)
            self.assertFalse(any('/data/' in name or name.endswith(('.h5ad', '.rds')) for name in z.namelist()))

    def test_real_figures_have_matching_intrinsic_dimensions(self):
        expected = {
            'scrna-seq-basics-r-pbmc3k-qc.png': (1200, 400),
            'scrna-seq-basics-r-pbmc3k-elbow.png': (800, 600),
            'scrna-seq-basics-r-pbmc3k-umap.png': (800, 600),
        }
        text = (ROOT / 'tutorials/scrna-seq-basics.html').read_text()
        for name, size in expected.items():
            data = (ROOT / 'images/tutorial-figures' / name).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', data[16:24]), size)
            match = re.search(r'<img[^>]+src="../images/tutorial-figures/' + re.escape(name) + r'"[^>]+>', text)
            self.assertIsNotNone(match, 'current R figure must remain embedded: ' + name)
            tag = match.group()
            self.assertIn('width="' + str(size[0]) + '"', tag)
            self.assertIn('height="' + str(size[1]) + '"', tag)
            self.assertIn('loading="lazy"', tag)
            self.assertIn('height:auto', tag)

    def test_claims_distinguish_execution_from_biological_validation(self):
        relative = 'tutorials/scrna-seq-basics.html'
        text = (ROOT / relative).read_text(encoding='utf-8')
        for phrase in ['The R/Seurat workflow above was executed on the public 10x Genomics PBMC 3k filtered matrix.',
                       '<strong>Scope of verification:</strong> this execution verifies the displayed R/Seurat route',
                       'The optional Scanpy route was not run as part of this execution.',
                       'No cell-type annotation, doublet calling, or clinical validation was performed',
                       'No thesis data or tumor results were used',
                       '97.70% retained',
                       'adata.raw = adata.copy()  # log-normalized expression before restricting to HVGs']:
            self.assertIn(phrase, text)
        self.assertNotIn(OLD_VALIDITY, text)
        self.assertNotIn(OLD_RANDOM, text)

    def test_public_plant_figure_and_all_27_tutorials_remain(self):
        relative = 'tutorials/scrna-seq-basics.html'
        text = (ROOT / relative).read_text(encoding='utf-8')
        for phrase in ['scrna-basics-public-arabidopsis-umap', 'public-plant-clusters.png',
                       'GSE123818', 'CC BY 4.0', 'image unchanged']:
            self.assertIn(phrase, text)
        self.assertEqual(len(list((ROOT / 'tutorials').glob('*.html'))), 27)


if __name__ == '__main__':
    unittest.main()
