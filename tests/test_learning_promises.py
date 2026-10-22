#!/usr/bin/env python3
"""Checks learning-format promises, not scientific workflow execution."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.descriptions = []
        self.in_json = False
        self.json_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and (attrs.get('name') in ('description', 'twitter:description')
                              or attrs.get('property') == 'og:description'):
            self.descriptions.append(attrs['content'])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json = True
            self.json_text = []

    def handle_data(self, data):
        if self.in_json:
            self.json_text.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.in_json:
            data = json.loads(''.join(self.json_text))
            if 'description' in data:
                self.descriptions.append(data['description'])
            self.in_json = False

class LearningPromiseTests(unittest.TestCase):
    def setUp(self):
        self.home = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.start = (ROOT / 'start-here.html').read_text(encoding='utf-8')
        self.catalogue = (ROOT / 'tutorials.html').read_text(encoding='utf-8')

    def test_all_58_tutorials_and_format_counts_remain(self):
        labels = re.findall(r'<span[^>]*data-tutorial-format="([^"]+)"', self.catalogue)
        self.assertEqual(Counter(labels), {
            'hands-on-lab': 19, 'conceptual-guide': 21,
            'advanced-template': 16, 'reference': 2,
        })
        self.assertEqual(len(list((ROOT / 'tutorials').glob('*.html'))), 58)
        self.assertIn('aria-label="58 tutorials"', self.catalogue)

    def test_homepage_description_fields_agree(self):
        parser = DescriptionParser()
        parser.feed(self.home)
        self.assertEqual(len(parser.descriptions), 5)
        self.assertEqual(len(set(parser.descriptions)), 1)
        for word in ('hands-on labs', 'conceptual guides', 'advanced templates', 'references'):
            self.assertIn(word, parser.descriptions[0])

    def test_featured_cards_state_existing_lesson_formats(self):
        cards = re.findall(r'<article\b[^>]*>.*?</article>', self.home, re.S)
        expected = {
            'computer-data-fundamentals': 'Hands-on lab',
            'conda-mamba-part1': 'Hands-on lab',
            'hpc-connection': 'Conceptual guide',
            'scrna-seq-basics': 'Hands-on lab',
            'metagenomics-kraken2-bracken': 'Advanced template',
            'advanced-ai-orchestration-bioinformatics': 'Conceptual guide',
        }
        for slug, label in expected.items():
            with self.subTest(slug=slug):
                matches = [c for c in cards if f'href="tutorials/{slug}.html"' in c]
                self.assertEqual(len(matches), 1)
                self.assertIn(f'<strong>{label}:</strong>', matches[0])

    def test_pbmc_link_matches_scoped_lab(self):
        self.assertIn('Explore the PBMC QC-to-clustering lab →', self.home)
        self.assertIn('not a raw-read processing pipeline or a clinical validation workflow', self.home)
        self.assertNotIn('See the full workflow', self.home)
        self.assertNotIn('Worked Example: CTCL', self.home)

    def test_format_is_not_mistaken_for_validation(self):
        for text in (self.home, self.catalogue):
            self.assertIn('Not every biological workflow has been run end to end', text)
        self.assertIn('labels describe the learning format, not validation status', self.catalogue)

    def test_learning_path_uses_lesson_specific_versions(self):
        self.assertIn('not standardized on one Python or R version', self.start)
        self.assertNotIn('All tutorials are standardized', self.start)
        self.assertNotIn('guarantee that someone', self.start)
        self.assertNotIn('Never break your system', self.start)
        self.assertNotIn('Each route is a complete guided learning track', self.start)

    def test_homepage_has_no_blanket_execution_promise(self):
        self.assertNotIn('Each guide explains the biological context, the required inputs, the commands', self.home)
        self.assertNotIn('every guide is designed to be followed hands-on', self.home.lower())
        self.assertNotIn('so you never skip a critical concept', self.home)

if __name__ == '__main__':
    unittest.main()
