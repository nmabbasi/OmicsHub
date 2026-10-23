#!/usr/bin/env python3
"""Guards for the narrowly reviewed public PBMC worked example; stdlib only."""
from pathlib import Path
import hashlib
import html
import json
import re
import struct
import subprocess
import unittest
import xml.etree.ElementTree as ET
import zipfile

from reviewed_tutorial_baseline import normalize_learner_revision
from reader_typography_baseline import normalize_reader_typography

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'd10ec616cae67437db90427bee4e156dd2bfb7d7'
SECTION_SHA256 = '4a9afadf530d9ad205c8c418cbf9ed73f108df6b79493fe91359003da2a08b57'
SCRIPT_SHA256 = 'ae3d41dec12b09a51865e692381014f813a0df8d30db29115be2d269e03df81a'
OLD_VALIDITY = '<li>Good-looking UMAPs are necessary but not sufficient evidence of biological validity: batch effects, normalization artifacts, or inappropriate gene selection can create misleading visual separation.</li>'
NEW_VALIDITY = '<li>A visually separated UMAP is neither necessary nor sufficient evidence of biological validity: batch effects, normalization artifacts, or inappropriate gene selection can create misleading visual separation. Validate the analysis with markers, technical-covariate checks, and relevant biological evidence.</li>'
OLD_RANDOM = '<li>UMAP is non-deterministic by default; set random seeds for reproducible embeddings when necessary (Seurat and Scanpy allow RNG control).</li>'
NEW_RANDOM = '<li>UMAP uses a stochastic algorithm. Record random seeds, toolkit versions, and graph parameters; the tested Scanpy 1.11.5 workflow uses the default random state of 0. Identical seeds do not guarantee matching embeddings across software versions or platforms.</li>'


def restore_only_reviewed_pbmc_changes(data):
    """Reverse only the exact new section, two corrections and one metadata date."""
    text = data.decode()
    matches = re.findall(r'<section id="pbmc3k-tested-worked-example"[\s\S]*?</section>\n', text)
    if len(matches) != 1 or hashlib.sha256(matches[0].encode()).hexdigest() != SECTION_SHA256:
        raise AssertionError('PBMC example differs from the exact reviewed section')
    text = text.replace(matches[0], '', 1)
    for new, old in [(NEW_VALIDITY, OLD_VALIDITY), (NEW_RANDOM, OLD_RANDOM),
                     ('"dateModified": "2026-10-22"', '"dateModified": "2026-10-21"')]:
        if text.count(new) != 1:
            raise AssertionError('Expected one narrowly reviewed PBMC correction: ' + new)
        text = text.replace(new, old, 1)
    return text.encode()


class PbmcWorkedExampleTests(unittest.TestCase):
    def test_surrounding_lesson_and_both_analysis_scripts_are_preserved(self):
        data = (ROOT / 'tutorials/scrna-seq-basics.html').read_bytes()
        relative = 'tutorials/scrna-seq-basics.html'
        result = subprocess.run(['git', 'show', BASELINE + ':tutorials/scrna-seq-basics.html'],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        typography_restored = normalize_reader_typography(relative, data.decode('utf-8')).encode('utf-8')
        normalized = restore_only_reviewed_pbmc_changes(typography_restored)
        if result.returncode == 0:
            self.assertEqual(normalize_learner_revision(relative, normalized.decode()),
                             normalize_learner_revision(relative, result.stdout.decode()))
        # The Python code itself has an independently recorded pre-edit fingerprint.
        blocks = re.findall(r'<pre><code>([\s\S]*?)</code></pre>', data.decode())
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
        expected = {'pbmc3k-tested-qc.png': (1508, 489), 'pbmc3k-tested-pca.png': (559, 468),
                    'pbmc3k-tested-umap.png': (605, 440)}
        text = (ROOT / 'tutorials/scrna-seq-basics.html').read_text()
        for name, size in expected.items():
            data = (ROOT / 'images/tutorial-figures' / name).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', data[16:24]), size)
            tag = re.search(r'<img[^>]+src="../images/tutorial-figures/' + re.escape(name) + r'"[^>]+>', text).group()
            self.assertIn('width="' + str(size[0]) + '"', tag)
            self.assertIn('height="' + str(size[1]) + '"', tag)
            self.assertIn('loading="lazy"', tag)
            self.assertIn('height:auto', tag)

    def test_claims_distinguish_execution_from_biological_validation(self):
        relative = 'tutorials/scrna-seq-basics.html'
        text = normalize_reader_typography(relative, (ROOT / relative).read_text(encoding='utf-8'))
        for phrase in ['only the Scanpy/Python route was executed', 'The Seurat/R route has not been run',
                       'No cell-type annotation, doublet calling, or clinical validation was performed',
                       'No thesis data or tumor results were used',
                       '97.70% retained', '.raw</code> is not untransformed counts']:
            self.assertIn(phrase, text)
        self.assertNotIn(OLD_VALIDITY, text)
        self.assertNotIn(OLD_RANDOM, text)

    def test_sitemap_dates_match_reviewed_updates_and_historical_baseline(self):
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        current_root = ET.parse(ROOT / 'sitemap.xml').getroot()
        current_entries = current_root.findall('s:url', ns)
        current_by_url = {entry.find('s:loc', ns).text: entry for entry in current_entries}
        self.assertEqual(len(current_by_url), len(current_entries))

        site = 'https://theomicshub.com/'
        approved_updated_paths = {
            'tutorials/cell-type-annotation-methods.html',
            'tutorials/scrna-seq-integration-strategies.html',
            'tutorials/advanced-visualization-packages.html',
            'tutorials/ai-prompt-engineering-seurat.html',
            'tutorials/command-line-part3.html',
            'tutorials/deterministic-retrieval-gget-ai.html',
            'tutorials/mcp-zotero.html',
            'tutorials/modern-bioinformatics-methods-2026.html',
            'tutorials/single-cell-foundation-models.html',
            'tutorials/spatial-transcriptomics-r-python.html',
            'tutorials/wes-variant-calling-pipeline.html',
            'tutorials/hpc-submission-part1.html',
            'tutorials/reproducible-workflows-snakemake-nextflow.html',
            'tutorials/command-line-part2.html',
            'tutorials/conda-mamba-part1.html',
            'tutorials/hpc-basic-commands.html',
            'tutorials/scrna-seq-trajectory-inference.html',
            'tutorials/advanced-ai-single-cell.html',
            'tutorials/ai-coding-cursor-aider.html',
            'tutorials/computer-data-fundamentals.html',
            'tutorials/statistics-for-bioinformatics.html',
            'tutorials/experimental-design-batch-effects.html',
            'tutorials/r-tidyverse-fundamentals.html',
            'start-here.html',
            'about.html',
            'tutorials.html',
            'pages/privacy.html',
            'pages/cookie.html',
        }
        self.assertEqual(
            {url for url, entry in current_by_url.items()
             if entry.find('s:lastmod', ns).text == '2026-10-23'},
            {site + path for path in approved_updated_paths},
        )
        for path in approved_updated_paths:
            self.assertEqual(current_by_url[site + path].find('s:lastmod', ns).text, '2026-10-23')
        pbmc_url = site + 'tutorials/scrna-seq-basics.html'
        self.assertEqual(current_by_url[pbmc_url].find('s:lastmod', ns).text, '2026-10-22')

        result = subprocess.run(['git', 'show', BASELINE + ':sitemap.xml'], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            baseline_root = ET.fromstring(result.stdout)
            baseline_entries = baseline_root.findall('s:url', ns)
            baseline_by_url = {entry.find('s:loc', ns).text: entry for entry in baseline_entries}
            self.assertEqual(len(baseline_by_url), len(baseline_entries))
            self.assertEqual(current_root.tag, baseline_root.tag)
            self.assertEqual(current_root.attrib, baseline_root.attrib)
            self.assertEqual(
                [entry.find('s:loc', ns).text for entry in current_entries],
                [entry.find('s:loc', ns).text for entry in baseline_entries],
            )

            allowed_date_urls = {site + path for path in approved_updated_paths} | {pbmc_url}
            self.assertEqual(set(current_by_url), set(baseline_by_url))
            for url, current in current_by_url.items():
                baseline = baseline_by_url[url]
                current_fields = [(child.tag, child.attrib, (child.text or '').strip())
                                  for child in current]
                baseline_fields = [(child.tag, child.attrib, (child.text or '').strip())
                                   for child in baseline]
                self.assertEqual(current.tag, baseline.tag, url)
                self.assertEqual(current.attrib, baseline.attrib, url)
                self.assertEqual([field[:2] for field in current_fields],
                                 [field[:2] for field in baseline_fields], url)
                if url in allowed_date_urls:
                    lastmod_tag = '{' + ns['s'] + '}lastmod'
                    self.assertEqual(
                        [field[2] for field in current_fields if field[0] != lastmod_tag],
                        [field[2] for field in baseline_fields if field[0] != lastmod_tag],
                        url,
                    )
                else:
                    self.assertEqual(current_fields, baseline_fields, url)

    def test_public_plant_figure_and_all_58_tutorials_remain(self):
        relative = 'tutorials/scrna-seq-basics.html'
        text = normalize_reader_typography(relative, (ROOT / relative).read_text(encoding='utf-8'))
        for phrase in ['scrna-basics-public-arabidopsis-umap', 'public-plant-clusters.png',
                       'GSE123818', 'CC BY 4.0', 'image unchanged']:
            self.assertIn(phrase, text)
        self.assertEqual(len(list((ROOT / 'tutorials').glob('*.html'))), 58)


if __name__ == '__main__':
    unittest.main()
