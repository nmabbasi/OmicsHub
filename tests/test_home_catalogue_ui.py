"""Landing-page usability and evidence contracts, not scientific workflow execution."""
from collections import Counter
from contextlib import redirect_stdout
from html import unescape
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE='fa26faa8d20a31de1211652e8ebffcf99534b9a6'


class Text(HTMLParser):
    def __init__(self,html):
        super().__init__(convert_charrefs=True)
        self.chunks=[]
        self.feed(html)
    def handle_data(self,data):self.chunks.append(data)
    @property
    def text(self):return ' '.join(' '.join(self.chunks).split())


def normalize(value):return ' '.join(unescape(value).split())


def read(relative):return (ROOT/relative).read_text(encoding='utf-8')


class HomeCatalogueUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=read('index.html')
        cls.catalogue=read('tutorials.html')
        cls.css=read('home-catalogue.css')
        cls.metadata=json.loads(read('tools/catalogue-learning.json'))

    def test_homepage_restores_reference_layout_and_only_improves_visible_copy(self):
        class LayoutSignature(HTMLParser):
            def __init__(self,markup):
                super().__init__(convert_charrefs=False)
                self.signature=[]
                self.stack=[]
                self.feed(markup)
            def handle_starttag(self,tag,attrs):
                self.signature.append(('start',self.get_starttag_text()))
                if tag not in {'img','input','br','hr','source','wbr','area','embed','link','meta'}:
                    self.stack.append(tag)
            def handle_startendtag(self,tag,attrs):
                self.signature.append(('empty',self.get_starttag_text()))
            def handle_endtag(self,tag):
                self.signature.append(('end',tag))
                if self.stack and self.stack[-1]==tag:self.stack.pop()
            def handle_comment(self,text):self.signature.append(('comment',text))
            def handle_data(self,text):
                if self.stack and self.stack[-1] in {'style','script'}:
                    self.signature.append(('executable-or-style-data',text))
        published=subprocess.check_output(['git','show',f'{BASE}:index.html'],cwd=ROOT,text=True)
        original_main=re.search(r'<main\b[^>]*>.*?</main>',published,re.S).group()
        current_main=re.search(r'<main\b[^>]*>.*?</main>',self.home,re.S).group()
        original_hero,original_after_hero=original_main.split('</section>',1)
        self.assertEqual(original_after_hero.count('text-center'),5)
        original_main=original_hero+'</section>'+original_after_hero.replace('text-center','text-left')
        self.assertEqual(LayoutSignature(current_main).signature,LayoutSignature(original_main).signature,
                         'Only visible copy and five written-section alignment utilities may change; the photographed hero stays exact')
        hero=re.search(r'<section class="hero-laptop-section\b.*?</section>',self.home,re.S).group()
        self.assertEqual(len(re.findall(r'<h1\b',self.home)),1)
        self.assertIn('Terminal prompt',hero)
        self.assertIn('Explore Tutorials →',hero)
        self.assertIn('Step by Step',hero)
        self.assertNotIn('home-catalogue.css',self.home)
        cards=re.findall(r'<article\b[^>]*class="[^"]*native-tutorial-card[^>]*>.*?</article>',self.home,re.S)
        self.assertEqual(len(cards),6)
        self.assertTrue(all('<strong>' in c and 'Read tutorial' in c for c in cards))
        for card in cards:
            slug=re.search(r'href="tutorials/([^"/]+)\.html"',card).group(1)
            self.assertIn(f'>{self.metadata["lessons"][slug]["level"].capitalize()}</span>',card)
        self.assertNotIn('id="tutorials-list"',self.home,'Search suggestions must not blank the curated lesson section')
        self.assertIn('not a raw-read processing pipeline or a clinical validation workflow',self.home)

    def test_all_metadata_has_actual_lesson_body_evidence(self):
        lessons=self.metadata['lessons']
        pages={p.stem for p in (ROOT/'tutorials').glob('*.html')}
        self.assertEqual(set(lessons),pages)
        self.assertEqual(len(lessons),58)
        for slug,item in lessons.items():
            with self.subTest(slug=slug):
                self.assertEqual(item['lessonPath'],f'tutorials/{slug}.html')
                self.assertIn(item['level'],{'beginner','intermediate','advanced'})
                self.assertTrue(item['prerequisiteSummary'].strip())
                self.assertLessEqual(len(item['prerequisiteSummary'].split()),45)
                self.assertNotIn('\u2014',item['prerequisiteSummary'])
                excerpt=normalize(item['sourceExcerpt'])
                self.assertGreater(len(excerpt),35)
                article=re.search(r'<article\b[^>]*>(.*?)</article>',read(item['lessonPath']),re.S).group(1)
                self.assertIn(excerpt,Text(article).text,'Evidence must quote the actual lesson body, not a catalogue caption')

    def test_all_58_cards_have_searchable_setup_and_experience_metadata(self):
        cards=re.findall(r'<article\b[^>]*class="[^"]*tutorial-grid-card[^>]*>.*?</article>',self.catalogue,re.S)
        self.assertEqual(len(cards),58)
        levels=[]
        for card in cards:
            slug=re.search(r'href="tutorials/([^"/]+)\.html"',card).group(1)
            metadata=self.metadata['lessons'][slug]
            level=re.search(r'data-level="([^"]+)"',card).group(1)
            self.assertEqual(level,metadata['level'])
            self.assertIn('hc-card-prerequisite',card)
            self.assertIn(normalize(metadata['prerequisiteSummary']),Text(card).text)
            self.assertIn('data-format=',card)
            levels.append(level)
        self.assertEqual(Counter(levels),Counter(i['level'] for i in self.metadata['lessons'].values()))

    def test_browsing_controls_are_native_labeled_and_have_recovery(self):
        for control in ('catalogue-category','catalogue-level','catalogue-format'):
            self.assertEqual(self.catalogue.count(f'id="{control}"'),1,control)
            self.assertRegex(self.catalogue,rf'<label\b[^>]*for="{control}"')
            self.assertRegex(self.catalogue,rf'<select\b[^>]*id="{control}"')
        for control in ('catalogue-reset','catalogue-clear-empty'):
            self.assertRegex(self.catalogue,rf'<button\b[^>]*id="{control}"')
        self.assertIn('role="status"',self.catalogue)
        self.assertIn('Experience levels are browsing guidance',Text(self.catalogue).text)
        self.assertIn('labels describe the learning format, not validation status',self.catalogue)
        self.assertIn('Not every biological workflow has been run end to end',self.catalogue)
        self.assertIn('<noscript',self.catalogue)

    def test_text_is_left_aligned_and_no_new_external_assets_or_em_dashes(self):
        for html in (self.home,self.catalogue):
            main=re.search(r'<main\b[^>]*>(.*?)</main>',html,re.S).group(1)
            self.assertNotIn('\u2014',Text(main).text)
            self.assertIn('subscribe-fab.js?v=',html)
        self.assertIn('home-catalogue.css?v=',self.catalogue)
        self.assertIn('back-to-top.css?v=',self.catalogue)
        self.assertIn('aria-label="Back to top"',self.catalogue)
        self.assertNotRegex(self.css,r'text-align\s*:\s*(?:center|justify)\b')
        self.assertNotIn('https://',self.css)
        self.assertIn('prefers-reduced-motion',self.css)
        self.assertIn('@media print',self.css)
        self.assertIn('min-height: 3rem',self.css)
        for selector in ('#home-page','#tutorials-page','.hc-card-prerequisite','.hc-filter-controls'):
            self.assertIn(selector,self.css)

    def test_generated_catalogue_metadata_and_home_css_are_current(self):
        result=subprocess.run([sys.executable,'tools/generate_catalogue_learning.py','--check'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for path in ('catalogue-browser.js','subscribe-fab.js'):
            result=subprocess.run(['node','--check',path],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_generator_check_mode_reports_stale_hooks_without_writing(self):
        spec=importlib.util.spec_from_file_location('catalogue_generator_review',ROOT/'tools/generate_catalogue_learning.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            stale=Path(folder)/'tutorials.html'
            content=self.catalogue.replace('>Beginner experience</span>','>Unapproved experience</span>',1)
            self.assertNotEqual(content,self.catalogue)
            stale.write_text(content)
            module.HTML_PATH=stale
            previous_argv=sys.argv
            try:
                sys.argv=['generate_catalogue_learning.py','--check']
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(),1)
                self.assertEqual(stale.read_text(),content)
                sys.argv=['generate_catalogue_learning.py']
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main(),0)
                self.assertEqual(stale.read_text(),self.catalogue)
            finally:
                sys.argv=previous_argv

    def test_shared_script_restores_exact_published_source_and_keeps_idempotent_category_guard(self):
        from sitewide_top_baseline import normalize_sitewide_top
        original=subprocess.check_output(['git','show',f'{BASE}:subscribe-fab.js'],cwd=ROOT,text=True)
        current=normalize_sitewide_top('subscribe-fab.js',read('subscribe-fab.js'))
        self.assertEqual(current,original)
        self.assertIn("if (!strip || document.getElementById('catalogue-category') || typeof window.filterTutorialsOnly !== 'function') return;",read('subscribe-fab.js'))


if __name__=='__main__':unittest.main()
