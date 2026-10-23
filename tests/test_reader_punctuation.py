"""Protect the owner-requested reader-copy cleanup without masking scientific changes."""
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'c030bc62bf6e4a4ad21f9ff64cb630c152157692'
FIXTURE = ROOT / 'tests/fixtures/reader-copy-edits.json'
NAVIGATION = ['index.html', 'start-here.html', 'tutorials.html', 'about.html',
              'contact.html', 'services.html', 'success.html', '404.html']


def baseline(relative):
    return subprocess.check_output(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT).decode()


class LinkAndIdParser(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append((attrs.get('href'), attrs.get('target'), attrs.get('rel')))


class ReaderPunctuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(FIXTURE.read_text())
        cls.pages = NAVIGATION + sorted(str(p.relative_to(ROOT)) for p in (ROOT/'pages').glob('*.html'))
        cls.pages += sorted(str(p.relative_to(ROOT)) for p in (ROOT/'tutorials').glob('*.html'))
        cls.old = {path: baseline(path) for path in cls.pages}

    def test_all_70_public_reading_pages_have_no_literal_or_encoded_em_dashes(self):
        self.assertEqual(len(self.pages), 70)
        for relative in self.pages:
            with self.subTest(page=relative):
                text = (ROOT/relative).read_text()
                self.assertNotIn('\u2014', unescape(text))
                self.assertNotRegex(text, r'(?i)\\u2014')

    def test_edit_fixture_lists_only_public_pages_and_the_navigation_copy_source(self):
        self.assertEqual(self.manifest['schema_version'], 1)
        self.assertEqual(set(self.manifest['files']), set(self.pages) | {'tools/learning-paths.json'})
        for relative, changes in self.manifest['files'].items():
            for pair in changes['replacements']:
                with self.subTest(path=relative, before=pair['before'][:60]):
                    self.assertIn('\u2014', pair['before'])
                    self.assertNotIn('\u2014', pair['after'])
                    self.assertNotEqual(pair['before'], pair['after'])

    def test_every_source_change_matches_the_exact_recorded_copy_and_cache_edits(self):
        for relative, changes in self.manifest['files'].items():
            with self.subTest(path=relative):
                expected = self.old.get(relative) or baseline(relative)
                for pair in changes['replacements']:
                    self.assertIn(pair['before'], expected)
                    expected = expected.replace(pair['before'], pair['after'])
                for pair in self.manifest['stylesheet_versions']:
                    expected = expected.replace(pair['before'], pair['after'])
                self.assertEqual((ROOT/relative).read_text(), expected)

    def test_all_pre_inline_code_and_executable_script_blocks_remain_byte_identical(self):
        patterns = [r'<pre\b[^>]*>.*?</pre>', r'<code\b[^>]*>.*?</code>',
                    r'<script\b[^>]*>.*?</script>']
        for relative, before in self.old.items():
            after = (ROOT/relative).read_text()
            for pattern in patterns:
                with self.subTest(path=relative, pattern=pattern):
                    old_blocks, new_blocks = re.findall(pattern, before, re.S), re.findall(pattern, after, re.S)
                    if pattern.startswith('<script'):
                        # JSON-LD is reader/search metadata, not executable logic;
                        # its exact permitted copy edit is checked independently above.
                        old_blocks = [block for block in old_blocks if 'type="application/ld+json"' not in block]
                        new_blocks = [block for block in new_blocks if 'type="application/ld+json"' not in block]
                    self.assertEqual(old_blocks, new_blocks)

    def test_links_anchor_ids_and_modification_metadata_are_unchanged(self):
        for relative, before in self.old.items():
            with self.subTest(path=relative):
                after = (ROOT/relative).read_text()
                old, new = LinkAndIdParser(before), LinkAndIdParser(after)
                self.assertEqual(old.links, new.links)
                self.assertEqual(old.ids, new.ids)
                pattern = r'"dateModified"\s*:\s*"[^\"]+"'
                self.assertEqual(re.findall(pattern, before), re.findall(pattern, after))

    def test_analysis_downloads_research_examples_images_and_site_scripts_are_unchanged(self):
        changed = subprocess.check_output(
            ['git', 'diff', '--name-only', BASE, '--', 'files/', 'images/',
             'tutorials/examples/', '*.js', 'sitemap.xml'], cwd=ROOT, text=True).splitlines()
        self.assertEqual(changed, [], 'Reader-copy edits must not modify analysis/data artifacts or site-script behavior')

    def test_generated_navigation_copy_cannot_reintroduce_em_dashes(self):
        for relative in ['tools/learning-paths.json', 'tools/generate_learning_paths.py', 'script.js']:
            with self.subTest(path=relative):
                text = (ROOT/relative).read_text()
                self.assertNotIn('\u2014', unescape(text))
                self.assertNotRegex(text, r'(?i)\\u2014')

    def test_all_reading_pages_use_the_new_shared_stylesheet_version(self):
        for relative in self.pages:
            with self.subTest(path=relative):
                stylesheet = 'home-page.min.css' if relative == 'index.html' else 'style.css'
                self.assertIn(stylesheet+'?v=20261023-reader-typography', (ROOT/relative).read_text())
        self.assertIn('home-page.min.css?v=20261023-reader-typography', (ROOT/'index.html').read_text())
        self.assertIn('start-here.css?v=20261023-reader-typography', (ROOT/'start-here.html').read_text())


if __name__ == '__main__':
    unittest.main()
