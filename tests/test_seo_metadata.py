"""Regression checks for page-level SEO metadata and JSON-LD consolidation."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = re.compile(r'<script[^>]*type="application/ld\+json">(.*?)</script>', re.S)

class SeoMetadataTests(unittest.TestCase):
    def entity(self, page):
        blocks = SCHEMA.findall(page.read_text(encoding='utf-8'))
        self.assertEqual(len(blocks), 1, f'{page.relative_to(ROOT)} should have one primary structured entity')
        return json.loads(blocks[0])

    def test_tutorial_has_one_complete_tech_article_entity(self):
        page = ROOT / 'tutorials' / 'ai-prompt-engineering-seurat.html'
        entity = self.entity(page)
        self.assertEqual(entity['@type'], 'TechArticle')
        for field in ('headline', 'description', 'mainEntityOfPage', 'author', 'publisher', 'datePublished', 'dateModified', 'url', 'isPartOf'):
            with self.subTest(field=field):
                self.assertIn(field, entity)
        self.assertEqual(entity['author']['name'], 'Dr. Nasir Mahmood Abbasi, PhD')
        self.assertTrue(entity['mainEntityOfPage']['@id'].endswith('/tutorials/ai-prompt-engineering-seurat.html'))
        self.assertEqual(entity['dateModified'], '2026-10-22')

    def test_tutorial_catalogue_has_correct_open_graph_url(self):
        text = (ROOT / 'tutorials.html').read_text(encoding='utf-8')
        self.assertRegex(text, r'<meta content="https://theomicshub\.com/tutorials\.html" property="og:url"')

    def test_each_page_uses_one_structured_data_entity(self):
        pages = list(ROOT.glob('*.html')) + list((ROOT / 'pages').glob('*.html')) + list((ROOT / 'tutorials').glob('*.html'))
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                self.entity(page)

if __name__ == '__main__':
    unittest.main()
