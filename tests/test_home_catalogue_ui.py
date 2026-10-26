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
PUBLISHED='911a5f0'
from reader_text_colour_baseline import normalize_reader_text
from startup_performance_baseline import restore_startup_performance_asset
from editorial_review_baseline import normalize_editorial_review
from route_migration_baseline import historical_route_path, published_tutorial_paths


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

def published(relative):
    return subprocess.check_output(['git','show',f'{PUBLISHED}:{relative}'],cwd=ROOT,text=True)

def attr(tag,name):
    match=re.search(r'\b'+re.escape(name)+r'\s*=\s*([\'\"])(.*?)\1',tag,re.I|re.S)
    return unescape(match.group(2)) if match else None

def preserved_title_markup(title_markup,expected_href):
    anchors=list(re.finditer(r'<a\b[^>]*>(.*?)</a\s*>',title_markup,re.I|re.S))
    if not anchors:return title_markup
    if len(anchors)!=1:raise AssertionError('A card title may contain only its one canonical lesson link')
    anchor=anchors[0]
    opening=re.match(r'<a\b[^>]*>',anchor.group(0),re.I|re.S).group()
    if 'hc-card-link' not in (attr(opening,'class') or '').split():
        raise AssertionError('The only title anchor must be the canonical hc-card-link')
    if attr(opening,'href')!=expected_href:
        raise AssertionError('The title anchor must retain the card lesson destination')
    return title_markup[:anchor.start()]+anchor.group(1)+title_markup[anchor.end():]

def catalogue_records(markup):
    cards=re.findall(r'<article\b(?=[^>]*\btutorial-grid-card\b)[\s\S]*?</article>',markup,re.I)
    records={}
    for card in cards:
        link=re.search(r'<a\b[^>]*>',card,re.I).group()
        href=attr(link,'href')
        title=preserved_title_markup(re.search(r'<h3\b[^>]*>(.*?)</h3>',card,re.I|re.S).group(1),href)
        description=Text(re.search(r'<p\b[^>]*>(.*?)</p>',card,re.I|re.S).group(1)).text
        image=re.search(r'<img\b[^>]*>',card,re.I).group()
        records[href]=(title,description,attr(image,'src'),attr(image,'alt'))
    return records


class HomeCatalogueUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home=read('index.html')
        cls.catalogue=read('tutorials.html')
        cls.css=read('home-catalogue.css')
        cls.metadata=json.loads(read('tools/catalogue-learning.json'))

    def test_homepage_is_byte_identical_to_published_version(self):
        self.assertEqual(normalize_reader_text('index.html',self.home),published('index.html'))
        self.assertNotIn('home-catalogue.css',self.home)
        cards=re.findall(r'<article\b[^>]*class="[^"]*native-tutorial-card[^>]*>.*?</article>',self.home,re.S)
        self.assertEqual(len(cards),6)
        self.assertTrue(all('<strong>' in c and 'Read tutorial' in c for c in cards))

    def test_all_58_scientific_lesson_files_are_byte_identical_to_published_version(self):
        pages=published_tutorial_paths(ROOT)
        self.assertEqual(len(pages),58)
        for page in pages:
            relative=page.relative_to(ROOT).as_posix()
            with self.subTest(page=relative):
                restored=normalize_reader_text(relative,page.read_text(encoding='utf-8'))
                self.assertEqual(restored.encode('utf-8'),subprocess.check_output(['git','show',f'{PUBLISHED}:{historical_route_path(relative)}'],cwd=ROOT))

    def test_catalogue_preserves_every_original_title_description_image_and_destination(self):
        original=catalogue_records(published('tutorials.html'))
        current=catalogue_records(normalize_editorial_review('tutorials.html',self.catalogue))
        self.assertEqual(len(original),58)
        self.assertEqual(len(current),58)
        self.assertEqual(current,original)
        self.assertTrue(all(href.startswith('tutorials/') and all(record) for href,record in current.items()))

    def test_each_catalogue_card_has_one_native_title_link_and_no_open_lesson_label(self):
        cards=re.findall(r'<article\b(?=[^>]*\btutorial-grid-card\b)[\s\S]*?</article>',self.catalogue,re.I)
        self.assertEqual(len(cards),58)
        for card in cards:
            with self.subTest(card=card[:120]):
                href=attr(re.search(r'<a\b[^>]*>',card,re.I).group(),'href')
                title=re.search(r'<h3\b[^>]*>(.*?)</h3>',card,re.I|re.S)
                self.assertIsNotNone(title)
                self.assertRegex(title.group(1),r'^\s*<a\b')
                self.assertRegex(title.group(1),r'</a\s*>\s*$')
                links=re.findall(r'<a\b[^>]*>',card,re.I)
                self.assertEqual(len(links),1,'The card should expose exactly one native lesson link')
                link=links[0]
                self.assertIn('hc-card-link',(attr(link,'class') or '').split())
                self.assertEqual(attr(link,'href'),href)
                self.assertEqual(href,f'tutorials/{Path(href).stem}.html')
                title_link=re.search(r'<a\b[^>]*>(.*?)</a\s*>',title.group(1),re.I|re.S)
                self.assertIsNotNone(title_link)
                self.assertEqual(Text(title_link.group(1)).text,Text(title.group(1)).text)
                self.assertNotRegex(Text(card).text,r'\bOpen lesson\b')

    def test_all_metadata_has_actual_lesson_body_evidence(self):
        lessons=self.metadata['lessons']
        pages={p.stem for p in published_tutorial_paths(ROOT)}
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

    def test_all_58_cards_keep_metadata_and_have_prominent_16_by_9_images(self):
        cards=re.findall(r'<article\b(?=[^>]*\btutorial-grid-card\b)[\s\S]*?</article>',self.catalogue,re.I)
        self.assertEqual(len(cards),58)
        levels=[]
        for card in cards:
            href=attr(re.search(r'<a\b[^>]*>',card,re.I).group(),'href')
            slug=Path(href).stem
            metadata=self.metadata['lessons'][slug]
            opening=re.search(r'<article\b[^>]*>',card,re.I).group()
            body=card[len(opening):]
            level=attr(opening,'data-level')
            self.assertEqual(level,metadata['level'])
            learning_format=attr(opening,'data-format')
            self.assertIn(learning_format,{'hands-on-lab','conceptual-guide','advanced-template','reference'})
            format_label=re.search(r'<span\b[^>]*data-tutorial-format="([^"]+)"',card,re.I)
            self.assertIsNotNone(format_label)
            self.assertEqual(format_label.group(1),learning_format)
            self.assertEqual(attr(opening,'data-search'),attr(opening,'data-search-base'))
            self.assertNotIn('hc-card-prerequisite',card)
            self.assertNotIn('hc-card-level',card)
            self.assertNotRegex(body,r'<[^>]+\bdata-level\s*=')
            self.assertNotRegex(body,r'<[^>]+\bdata-format\s*=')
            image=re.search(r'<img\b[^>]*>',card,re.I)
            self.assertIsNotNone(image)
            self.assertTrue(attr(image.group(),'src'))
            self.assertTrue(attr(image.group(),'alt'))
            self.assertRegex(card,r'<div\b[^>]*class="[^"]*\baspect-video\b[^"]*"[^>]*>\s*<img\b')
            levels.append(level)
        self.assertEqual(Counter(levels),Counter(i['level'] for i in self.metadata['lessons'].values()))
        self.assertNotIn('Before you begin',Text(self.catalogue).text)

    def test_browsing_controls_are_only_labeled_search_topic_and_reset(self):
        self.assertEqual(self.catalogue.count('id="search-input"'),1)
        self.assertRegex(self.catalogue,r'<label\b[^>]*for="search-input"')
        self.assertEqual(self.catalogue.count('id="catalogue-category"'),1)
        self.assertRegex(self.catalogue,r'<label\b[^>]*for="catalogue-category"')
        self.assertRegex(self.catalogue,r'<select\b[^>]*id="catalogue-category"')
        for removed in ('catalogue-level','catalogue-format'):
            self.assertNotIn(f'id="{removed}"',self.catalogue)
        for control in ('catalogue-reset','catalogue-clear-empty'):
            self.assertRegex(self.catalogue,rf'<button\b[^>]*id="{control}"')
        self.assertIn('role="status"',self.catalogue)
        self.assertIn('<noscript',self.catalogue)
        self.assertIn('id="learning-formats"',self.catalogue)
        self.assertIn('What do the learning-format labels mean?',Text(self.catalogue).text)
        self.assertIn('labels describe the learning format, not validation status',Text(self.catalogue).text)
        self.assertIn('Not every biological workflow has been run end to end',Text(self.catalogue).text)

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

    def test_generated_catalogue_metadata_and_home_css_are_current(self):
        result=subprocess.run([sys.executable,'tools/generate_catalogue_learning.py','--check'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        for path in ('catalogue-browser.js','subscribe-fab.js'):
            result=subprocess.run(['node','--check',path],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_generator_check_mode_reports_stale_metadata_without_writing(self):
        spec=importlib.util.spec_from_file_location('catalogue_generator_review',ROOT/'tools/generate_catalogue_learning.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            stale=Path(folder)/'tutorials.html'
            slug=next(iter(self.metadata['lessons']))
            original_level=self.metadata['lessons'][slug]['level']
            changed_level=next(level for level in ('beginner','intermediate','advanced') if level!=original_level)
            cards=re.findall(r'<article\b(?=[^>]*\btutorial-grid-card\b)[\s\S]*?</article>',self.catalogue,re.I)
            card=next(card for card in cards if f'href="tutorials/{slug}.html"' in card)
            mutated=re.sub(r'(data-level=")[^"]+',rf'\g<1>{changed_level}',card,count=1)
            content=self.catalogue.replace(card,mutated,1)
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

    def test_shared_script_is_published_identical_and_keeps_idempotent_category_guard(self):
        original=published('subscribe-fab.js')
        current=read('subscribe-fab.js')
        current=restore_startup_performance_asset('subscribe-fab.js',current.encode()).decode()
        self.assertEqual(current,original)
        self.assertIn("if (!strip || document.getElementById('catalogue-category') || typeof window.filterTutorialsOnly !== 'function') return;",read('subscribe-fab.js'))


if __name__=='__main__':unittest.main()
