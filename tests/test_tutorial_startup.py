"""Startup-only optimization contracts against the published PR #27 source."""
import copy
import hashlib
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest
from editorial_review_baseline import normalize_editorial_review, normalize_editorial_review_bytes
from start_here_desktop_baseline import normalize_start_here_desktop_html

ROOT=Path(__file__).resolve().parents[1]
BASE='93f06260550dbc91c0f020c24e1e2b00b7e017b5'
spec=importlib.util.spec_from_file_location('startup_ui_generator',ROOT/'tools/generate_tutorial_ui.py')
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)

class Tags(HTMLParser):
    def __init__(self,source):
        super().__init__();self.scripts=[];self.links=[];self.feed(source)
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.scripts.append(dict(attrs))
        if tag=='link':self.links.append(dict(attrs))
    handle_startendtag=handle_starttag

def base_bytes(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

def inline_payload(source):
    match=re.search(r'<script id="tutorial-code-data">\s*window\.OMICS_TUTORIAL_CODE = (.*?);\s*</script>',source,re.S)
    if not match:raise AssertionError('Missing unique generated lesson metadata')
    return json.loads(match.group(1))

class TutorialStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata=generator.load_metadata(ROOT)
        pages=sorted((ROOT/'tutorials').glob('*.html'))
        cls.sources={p.stem:p.read_text() for p in pages}
        cls.normalized_sources={p.stem:normalize_editorial_review('tutorials/'+p.name,p.read_text()) for p in pages}

    def test_all_58_lessons_receive_only_their_complete_reviewed_metadata(self):
        self.assertEqual(len(self.sources),58)
        for slug,source in self.sources.items():
            with self.subTest(slug=slug):
                self.assertEqual(source.count('id="tutorial-code-data"'),1)
                self.assertEqual(inline_payload(source),{'schema':1,'tutorials':{slug:self.metadata['tutorials'][slug]}})
                self.assertNotIn('src="../tutorial-code-data.js',source)
                self.assertEqual(generator.render_page(source,self.metadata,slug),source)

    def test_existing_small_mobile_helper_replaces_only_unused_spa_bundle(self):
        for slug,source in self.sources.items():
            with self.subTest(slug=slug):
                scripts=Tags(source).scripts
                self.assertFalse(any(re.search(r'/script\.js(?:\?|$)',s.get('src','')) for s in scripts))
                for path in ['mobile-navigation.js','assets/vendor/prism/prism-1.29.0.js','code-tabs.js','copy-code.js','subscribe-fab.js']:
                    matches=[s for s in scripts if s.get('src','').split('?')[0]=='../'+path]
                    self.assertEqual(len(matches),1,path)
                    if path=='mobile-navigation.js':self.assertIn('defer',matches[0],path)
                    else:self.assertNotIn('defer',matches[0],path)
                self.assertIn('onclick="toggleMobileMenu()"',source)
                self.assertIn('aria-current="page"',source)

    def test_articles_styles_and_existing_inline_behavior_are_byte_identical(self):
        for slug,source in self.sources.items():
            with self.subTest(slug=slug):
                before=base_bytes('tutorials/'+slug+'.html').decode()
                source=self.normalized_sources[slug]
                self.assertEqual(re.findall(r'<article\b.*?</article>',before,re.S),re.findall(r'<article\b.*?</article>',source,re.S))
                self.assertEqual(Tags(before).links,Tags(source).links)
                def original_inline(text):
                    return [match.group(0) for match in re.finditer(r'<script\b([^>]*)>.*?</script>',text,re.S) if not re.search(r'\bsrc=',match.group(1)) and 'id="tutorial-code-data"' not in match.group(1)]
                self.assertEqual(original_inline(before),original_inline(source))
                banner=r'<!-- Cookie Consent Banner -->.*?<!-- /Cookie Consent Banner -->'
                self.assertEqual(re.findall(banner,before,re.S),re.findall(banner,source,re.S))
                self.assertEqual([s for s in Tags(before).scripts if s.get('src','').startswith('https://')],[s for s in Tags(source).scripts if s.get('src','').startswith('https://')])

    def test_design_homepage_catalogue_privacy_and_vendor_assets_are_unchanged(self):
        for name in ['index.html','tutorials.html','start-here.html','style.css','tailwind.min.css','tutorial-reader.css','tutorial-navigation.css','back-to-top.css','mobile-navigation.js','script.js','analytics.js','cookie-consent.js','adsense-consent.js','assets/vendor/prism/prism-1.29.0.js','tutorial-code-data.js']:
            with self.subTest(path=name):
                current=normalize_editorial_review_bytes(name,(ROOT/name).read_bytes())
                if name=='start-here.html':
                    current=normalize_start_here_desktop_html(name,current.decode()).encode()
                self.assertEqual(current,base_bytes(name))

    def test_homepage_css_rules_are_identical_and_only_build_checksum_refreshes(self):
        before=base_bytes('home-page.min.css')
        current=(ROOT/'home-page.min.css').read_bytes()
        self.assertEqual(before.split(b'\n',1)[1],current.split(b'\n',1)[1])
        checksum=hashlib.sha256()
        for name in ['style.css','index.html','script.js','subscribe-fab.js','cookie-consent.js','mobile-navigation.js']:
            checksum.update((ROOT/name).read_bytes())
        self.assertIn(('Source SHA256: '+checksum.hexdigest()+' */').encode(),current.split(b'\n',1)[0])

    def test_metadata_cannot_end_its_script_element(self):
        slug='statistics-for-bioinformatics'
        changed=copy.deepcopy(self.metadata)
        title='</script><img src=x onerror=alert(1)>'
        changed['tutorials'][slug]['groups'][0]['title']=title
        rendered=generator.render_page(self.sources[slug],changed,slug)
        self.assertNotIn(title,rendered)
        self.assertEqual(inline_payload(rendered)['tutorials'][slug]['groups'][0]['title'],title)
        self.assertEqual(rendered.count('id="tutorial-code-data"'),1)

    def test_digest_reuse_safety_node_regressions(self):
        result=subprocess.run(['node','--test','tests/test_code_tabs_digest_memoization.js'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_layout_batching_node_regressions(self):
        result=subprocess.run(['node','--test','tests/test_reader_layout_batching.js'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
