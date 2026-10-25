"""Integrity of specifically reviewed, executed teaching figures, not biological validity."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import importlib.util
import json
import re
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'files/tutorial-examples/execution-evidence/2026-10-25.json'
EXPECTED={
 'images/tutorial-figures/visualization-fundamentals-r-qc_boxplot.png',
 'images/tutorial-figures/visualization-fundamentals-r-qc_histogram.png',
 'images/tutorial-figures/visualization-fundamentals-r-pca_plot.png',
 'images/tutorial-figures/visualization-fundamentals-r-umap_plot.png',
 'images/tutorial-figures/visualization-fundamentals-r-heatmap_topgenes.png',
 'images/tutorial-figures/visualization-fundamentals-r-volcano.png',
 'images/tutorial-figures/research-reporting-r-synthetic-qc.png',
 'images/tutorial-figures/tidyverse-r-supplied-count-totals.png',
 'images/tutorial-figures/quality-control-r-public-pbmc3k-violin.png',
 'images/tutorial-figures/scrna-seq-basics-r-pbmc3k-qc.png',
 'images/tutorial-figures/scrna-seq-basics-r-pbmc3k-elbow.png',
 'images/tutorial-figures/scrna-seq-basics-r-pbmc3k-umap.png',
}
sha=lambda data:hashlib.sha256(data).hexdigest()

class Facts(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.blocks=[];self.named={};self.images=[];self.ids=set();self.current=None;self.identifier=None;self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.add(attrs['id'])
        if tag=='img':self.images.append(attrs)
        if tag=='pre':self.current=[];self.identifier=attrs.get('id')
    def handle_data(self,data):
        if self.current is not None:self.current.append(data)
    def handle_endtag(self,tag):
        if tag=='pre' and self.current is not None:
            code=''.join(self.current);self.blocks.append(code)
            if self.identifier:self.named[self.identifier]=code
            self.current=None;self.identifier=None

class VerifiedAnalysisFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(EVIDENCE.read_text())
        cls.figures=[(slug,f) for slug,row in cls.data['tutorials'].items() for f in row.get('figures',[])]
    def test_exact_twelve_reviewed_pngs_match_fingerprints_and_dimensions(self):
        self.assertEqual(len(self.figures),12);self.assertEqual({f['path'] for _,f in self.figures},EXPECTED)
        for slug,f in self.figures:
            with self.subTest(slug=slug,path=f['path']):
                raw=(ROOT/f['path']).read_bytes();self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n');self.assertEqual(raw[12:16],b'IHDR')
                self.assertEqual(sha(raw),f['sha256']);self.assertEqual(struct.unpack('>II',raw[16:24]),(f['width'],f['height']));self.assertGreater(len(raw),1000)
    def test_every_figure_is_embedded_with_meaningful_alt_text(self):
        for slug,f in self.figures:
            facts=Facts((ROOT/'tutorials'/(slug+'.html')).read_text());images=[i for i in facts.images if i.get('src')=='../'+f['path']]
            self.assertEqual(len(images),1,(slug,f['path']));self.assertGreater(len(images[0].get('alt','')),20)
            self.assertEqual(images[0].get('loading'),'lazy')
    def test_capsule_has_no_raw_private_paths_secrets_or_knitted_reports(self):
        raw=EVIDENCE.read_text()
        for forbidden in ['/workspace/','/home/','{{secret:','OPENAI_API_KEY','file://','.rds','.h5ad']:
            self.assertNotIn(forbidden,raw)
        self.assertEqual(self.data['sourceCommit'],'122bd466feb11efd304769faff19e77bd40a98b4')
        for row in self.data['tutorials'].values():self.assertTrue(row['notExecuted'])
    def test_linked_source_and_teaching_input_hashes_are_current(self):
        for slug,row in self.data['tutorials'].items():
            for record in row.get('inputs',[]) if isinstance(row.get('inputs'),list) else [row.get('inputs',{})]:
                if record.get('path') and record.get('sha256'):self.assertEqual(sha((ROOT/record['path']).read_bytes()),record['sha256'])
            sources=([row['source']] if row.get('source') else [])+row.get('sources',[])+([row['summarySource']] if row.get('summarySource') else [])
            for source in sources:
                if source.get('path'):
                    self.assertEqual(sha((ROOT/source['path']).read_bytes()),source['sha256'])
                else:
                    facts=Facts((ROOT/source['page']).read_text())
                    if source.get('blockID'):code=facts.named[source['blockID']]
                    else:
                        matches=[code for code in facts.blocks if source['contains'] in code];self.assertEqual(len(matches),1,source);code=matches[0]
                    self.assertEqual(sha(code.encode()),source['codeSHA256'])
    def test_public_data_and_synthetic_boundaries_remain_explicit(self):
        for slug in ['data-visualization-fundamentals','research-reporting-interpretation','r-tidyverse-fundamentals']:
            self.assertIn('synthetic',self.data['tutorials'][slug]['status'])
        basics=self.data['tutorials']['scrna-seq-basics'];self.assertEqual(basics['inputs']['inputCells'],2700);self.assertFalse(basics['inputs']['extraSubsampling'])
        self.assertIn('2638',' '.join(basics['checks']))
        qc=self.data['tutorials']['scrna-seq-quality-control'];self.assertIn('LISI',qc['notExecuted']);self.assertIn('cell_type',qc['notExecuted'])
        self.assertEqual(self.data['tutorials']['wes-variant-calling-pipeline']['figures'],[])
    def test_new_result_sections_are_static_accessible_and_reader_facing(self):
        for slug in ['data-visualization-fundamentals','research-reporting-interpretation','r-tidyverse-fundamentals','quality-control-fundamentals']:
            text=(ROOT/'tutorials'/(slug+'.html')).read_text();self.assertEqual(text.count('class="lesson-results"'),1)
            section=text.split('<!-- Verified analysis outputs: 2026-10-25 -->',1)[1].split('<!-- /Verified analysis outputs -->',1)[0]
            self.assertIn('aria-labelledby="observed-analysis-results"',section);self.assertIn('<figcaption>',section);self.assertIn('Run details and limits',section);self.assertNotIn('\u2014',section)
            facts=Facts(text)
            for target in re.findall(r'href="#([^"]+)"',section):self.assertIn(target,facts.ids)
    def test_updated_code_data_uses_its_independent_version_only(self):
        spec=importlib.util.spec_from_file_location('execution_review_renderer',ROOT/'tools/generate_tutorial_ui.py');renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)
        self.assertEqual(renderer.CODE_DATA_VERSION,'20261025-executed-examples-v1');self.assertNotEqual(renderer.CODE_DATA_VERSION,renderer.VERSION)
        self.assertEqual(renderer.VERSION,'20261025-r-first-v1');self.assertEqual(renderer.NAVIGATION_CSS_VERSION,'20261025-learning-navigation-v2')
        for page in (ROOT/'tutorials').glob('*.html'):
            text=page.read_text();self.assertIn('tutorial-code-data.js?v='+renderer.CODE_DATA_VERSION,text);self.assertIn('tutorial-reader.css?v='+renderer.VERSION,text)

if __name__=='__main__':unittest.main()
