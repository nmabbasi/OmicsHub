#!/usr/bin/env python3
"""Regression checks for tutorial prose and literal code HTML.

Run: python3 -m unittest discover -s tests -p 'test_*.py'
Uses the standard library; does not execute scientific examples.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REDIRECT_MANIFEST = json.loads((ROOT / 'tools' / 'legacy-redirects.json').read_text(encoding='utf-8'))
REDIRECT_PATHS = set(REDIRECT_MANIFEST['migration_root_urls']) | set(REDIRECT_MANIFEST['historical_aliases'])
CODE_BLOCK = re.compile(
    r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S
)
BARE_AMPERSAND = re.compile(r'&(?!#\d+;|#x[0-9a-fA-F]+;|[A-Za-z][A-Za-z0-9]+;)')


class TutorialMarkupTests(unittest.TestCase):
    def test_no_duplicate_paragraph_tags(self):
        for page in sorted((ROOT / 'tutorials').glob('*.html')):
            with self.subTest(page=page.name):
                text = page.read_text(encoding='utf-8')
                self.assertIsNone(re.search(r'<p>\s*<p>|</p>\s*</p>', text))

    def test_code_uses_escaped_less_than(self):
        for page in sorted((ROOT / 'tutorials').glob('*.html')):
            for index, code in enumerate(CODE_BLOCK.findall(page.read_text(encoding='utf-8')), 1):
                with self.subTest(page=page.name, block=index):
                    self.assertNotIn('<', code, 'Escape literal less-than operators as &lt;')

    def test_phylogeny_shell_ampersands_are_escaped(self):
        page = ROOT / 'tutorials' / 'evolutionary-phylogeny-analysis.html'
        for index, code in enumerate(CODE_BLOCK.findall(page.read_text(encoding='utf-8')), 1):
            with self.subTest(block=index):
                self.assertIsNone(BARE_AMPERSAND.search(code))


class NavigationMarkupTests(unittest.TestCase):
    def test_every_tutorial_has_global_navigation(self):
        for page in sorted((ROOT / 'tutorials').glob('*.html')):
            with self.subTest(page=page.name):
                text = page.read_text(encoding='utf-8')
                self.assertIn('id="mobile-menu"', text)
                self.assertIn('id="nav-desktop-tutorials"', text)
                self.assertRegex(text, r'<button[^>]*aria-controls="mobile-menu"')
                self.assertRegex(text, r'<a[^>]*href="(?:/|\.\./index\.html)"[^>]*>')

    def test_standalone_pages_load_menu_handlers(self):
        pages = sorted(ROOT.glob('*.html')) + sorted((ROOT / 'pages').glob('*.html'))
        for page in pages:
            if '/' + page.relative_to(ROOT).as_posix() in REDIRECT_PATHS:
                continue
            with self.subTest(page=page.name):
                text = page.read_text(encoding='utf-8')
                if not re.search(r'<script[^>]*src="(?:\.\./)?script\.js', text):
                    self.assertRegex(text, r'<script[^>]*src="(?:\.\./)?mobile-navigation\.js"')


if __name__ == '__main__':
    unittest.main()
