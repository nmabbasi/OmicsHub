"""Beginner navigation contracts, not scientific workflow validation."""
from pathlib import Path
from html import unescape
from html.parser import HTMLParser
import json
import re
import subprocess
import unittest

from start_here_baseline import (
    START_HERE_ASSET_PATHS, normalize_start_here, normalize_start_here_sitemap,
    page_patches, pre_review_bytes, verify_start_here_file,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = 'a4b6ead8251e0a3abcb748061a40155ae9523a82'
CSS_HREF = 'start-here.css?v=20261025-lesson-first-v2'
MAIN = re.compile(r'<main\b[^>]*>.*?</main>', re.S)

class Facts(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'a': self.links.append(a.get('href', ''))

def original(name):
    return subprocess.check_output(['git', 'show', f'{BASE}:{name}'], cwd=ROOT).decode()

class StartHereSimplificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'start-here.html').read_text()
        cls.main = MAIN.search(cls.source).group()
        cls.before = original('start-here.html')
        cls.old_main = MAIN.search(cls.before).group()
        cls.facts = Facts(cls.source)

    def test_reading_load_is_actually_reduced_not_just_hidden(self):
        def words(text):
            return len(unescape(re.sub('<[^>]*>', ' ', text)).split())
        self.assertLess(words(self.main), 650)
        self.assertLess(words(self.main), words(self.old_main) * .55)
        self.assertNotIn('\u2014', unescape(self.main))
        self.assertNotIn("Dr. Abbasi's Advice", self.main)
        self.assertNotIn('Software Stack', self.main)

    def test_one_intro_cta_then_three_ordered_foundation_steps(self):
        hero = re.search(r'<section class="sh-hero".*?</section>', self.main, re.S).group()
        self.assertEqual(hero.count('<a '), 1)
        self.assertIn('href="tutorials/introduction-to-bioinformatics.html"', hero)
        self.assertIn('aria-describedby="sh-first-lesson-note"', hero)
        self.assertIn('id="sh-first-lesson-note"', hero)
        self.assertEqual(self.main.count('href="tutorials/introduction-to-bioinformatics.html"'), 1)

        steps_match = re.search(r'<ol class="sh-steps" start="2">(.*?)</ol>', self.main, re.S)
        self.assertIsNotNone(steps_match, 'foundation sequence must continue at lesson 02')
        steps = steps_match.group(1)
        items = re.findall(r'<li\b.*?</li>', steps, re.S)
        self.assertEqual(len(items), 3)
        step_links = re.findall(r'<h3><a href="([^"]+)"', steps)
        self.assertEqual(step_links, [
            'tutorials/command-line-part1.html',
            'tutorials/computer-data-fundamentals.html',
        ])
        self.assertLess(steps.index('command-line-part1.html'), steps.index('computer-data-fundamentals.html'))
        self.assertIn('Bash on Linux, macOS, or Windows Subsystem for Linux (WSL)', self.main)
        choice = re.search(r'<section class="sh-choice".*?</section>', steps, re.S).group()
        self.assertIn('tutorials/r-tidyverse-fundamentals.html', choice)
        self.assertIn('tutorials/python-fundamentals-bioinformatics.html', choice)
        self.assertNotIn('introduction-to-bioinformatics.html', steps)
        self.assertNotIn('conda-mamba-part1.html', steps)

    def test_software_setup_is_optional_and_language_routes_are_choices(self):
        optional = re.search(r'<details\b[^>]*id="sh-optional-tools".*?</details>', self.main, re.S).group()
        self.assertIn('tutorials/conda-mamba-part1.html', optional)
        self.assertNotIn('conda-mamba-part1.html', self.main[:self.main.index('id="sh-routes"')])
        self.assertIn('Choose one language', self.main)
        self.assertIn('Learn one for now', self.main)
        self.assertIn('tutorials/statistics-for-bioinformatics.html', self.main)
        self.assertIn('tutorials/experimental-design-batch-effects.html', self.main)

    def test_every_existing_tutorial_destination_and_manifest_anchor_is_preserved(self):
        old_links = {u for u in Facts(self.old_main).links if u.startswith('tutorials/')}
        new_links = {u for u in self.facts.links if u.startswith('tutorials/')}
        self.assertEqual(len(old_links), 32)
        self.assertEqual(new_links, old_links)
        targets = json.loads((ROOT / 'tools/learning-paths.json').read_text())['start_targets']
        for anchor in targets:
            self.assertEqual(self.facts.ids.count(anchor), 1, anchor)
        self.assertEqual(len(self.facts.ids), len(set(self.facts.ids)))
        for link in self.facts.links:
            if link.startswith('tutorials/'):
                self.assertTrue((ROOT / link.split('#')[0]).is_file(), link)

    def test_six_optional_details_are_native_collapsed_and_cautions_remain(self):
        details = re.findall(r'<details\b[^>]*>', self.main)
        self.assertEqual(len(details), 6)
        self.assertTrue(all(not re.search(r'\bopen\b', d) for d in details))
        self.assertEqual(self.main.count('<summary>'), 6)
        for phrase in ['not a required course', 'not a bulk RNA-seq tutorial', 'replicated single-cell samples',
                       'not substitutes for basic QC', 'authorized institutional access',
                       'not standardized on one Python or R version', 'zero-byte placeholder files are not sequencing data']:
            self.assertIn(phrase, self.main)

    def test_outside_main_only_explicit_ui_wiring_and_date_changed(self):
        expected = self.before.replace(self.old_main, self.main, 1)
        expected = expected.replace('start-here.css?v=20261023-reader-typography', CSS_HREF, 1)
        css_line = f'<link href="{CSS_HREF}" rel="stylesheet"/>\n'
        expected = expected.replace(css_line, css_line + '<link href="back-to-top.css?v=20261024-reader-ui-v3" rel="stylesheet"/>\n<script defer="" src="start-here.js?v=20261024-start-simple"></script>\n', 1)
        expected = expected.replace('"dateModified": "2026-10-23"', '"dateModified": "2026-10-24"', 1)
        expected = expected.replace('subscribe-fab.js?v=20261022-reader-review', 'subscribe-fab.js?v=20261024-reader-ui-v3', 1)
        top = re.search(r'<!-- Start Here top link -->.*?<!-- /Start Here top link -->\n', self.source, re.S).group()
        expected = expected.replace('<!-- Footer -->', top + '<!-- Footer -->', 1)
        self.assertEqual(expected, self.source)
        self.assertIn('id="back-to-top" href="#sh-hero-title" aria-label="Back to top"', top)

    def test_exact_start_here_and_sitemap_restoration_and_mutation_detection(self):
        self.assertEqual(set(page_patches()), {'start-here.html', 'sitemap.xml'})
        self.assertEqual(normalize_start_here('start-here.html', self.source), self.before)
        self.assertEqual(normalize_start_here('start-here.html', self.before), self.before)
        current = (ROOT / 'sitemap.xml').read_bytes()
        self.assertEqual(normalize_start_here_sitemap(current), pre_review_bytes('sitemap.xml'))
        bad = self.source.replace('One step at a time.', 'Unsupported new learning claim.', 1)
        self.assertNotEqual(bad, self.source)
        self.assertNotEqual(normalize_start_here('start-here.html', bad), self.before)
        bad = self.source.replace('src="analytics.js"', 'src="unapproved.js"', 1)
        self.assertNotEqual(normalize_start_here('start-here.html', bad), self.before)
        badmap = current.replace(b'<priority>0.9</priority>', b'<priority>0.1</priority>', 1)
        self.assertNotEqual(normalize_start_here_sitemap(badmap), pre_review_bytes('sitemap.xml'))
        self.assertEqual(normalize_start_here('unknown.html', self.source), self.source)

    def test_standalone_start_assets_are_exactly_pinned(self):
        self.assertEqual(START_HERE_ASSET_PATHS, {'start-here.css', 'start-here.js'})
        for relative in START_HERE_ASSET_PATHS:
            data = (ROOT / relative).read_bytes()
            self.assertEqual(verify_start_here_file(relative, data), data)
            with self.assertRaisesRegex(AssertionError, 'fingerprint mismatch'):
                verify_start_here_file(relative, data + b'\n')
        with self.assertRaisesRegex(AssertionError, 'not an authorized'):
            verify_start_here_file('analytics.js', b'anything')

if __name__ == '__main__': unittest.main()
