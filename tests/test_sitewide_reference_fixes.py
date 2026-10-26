"""Scoped regressions for the review-only link, search, menu and newsletter fixes."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

from editorial_review_baseline import normalize_editorial_review
from coffee_removal_baseline import restore_coffee_removal_text
from start_here_desktop_baseline import (
    normalize_start_here_desktop_html,
    restore_start_here_desktop_asset,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '36bc46d'


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def by_id(self, ident):
        return next((attrs for _, attrs in self.tags if attrs.get('id') == ident), None)


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def baseline(path):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT, text=True)


class SitewideReferenceFixesTests(unittest.TestCase):
    def test_optional_python_links_have_real_source_targets(self):
        for slug, target in (
            ('single-cell-foundation-models', 'foundation-embedding-python-run-stage'),
            ('autonomous-research-orchestrator', 'python-alternative'),
        ):
            with self.subTest(slug=slug):
                markup = Markup(read(f'tutorials/{slug}.html'))
                self.assertIsNotNone(markup.by_id(target))
                self.assertTrue(any(a.get('href') == f'#{target}' for tag, a in markup.tags if tag == 'a'))

    def test_stale_integration_reference_is_absent(self):
        text = read('tutorials/scrna-seq-integration-strategies.html')
        self.assertNotIn('sc-best-practices.org/cellular_structure/integration/', text)
        self.assertIn('https://www.sc-best-practices.org/cellular-structure/integration/', text)

    def test_legal_visibility_is_controlled_by_expanded_state_not_hover_or_focus(self):
        css = read('style.css')
        self.assertIn('#legal-menu-button[aria-expanded="false"] + #legal-menu', css)
        self.assertIn('#legal-menu-button[aria-expanded="true"] + #legal-menu', css)
        self.assertNotIn('#legal-menu-button:hover + #legal-menu', css)
        self.assertNotIn('#legal-menu-button:focus-visible + #legal-menu', css)

    def test_newsletter_cannot_default_to_get_when_javascript_is_unavailable(self):
        text = read('services.html')
        markup = Markup(text)
        self.assertEqual(markup.by_id('newsletter-gs-form')['method'].lower(), 'post')
        self.assertEqual(markup.by_id('newsletter-gs-form')['action'], 'services.html#newsletter-title')
        self.assertIn('disabled', markup.by_id('nl-fields'))
        self.assertRegex(text, r'<noscript>[\s\S]*?Newsletter signup requires JavaScript[\s\S]*?</noscript>')
        self.assertLess(text.index("form.addEventListener('submit'"), text.index('fields.disabled = false'))

    def test_newsletter_announces_states_and_focuses_its_honest_completion_notice(self):
        text = read('services.html')
        markup = Markup(text)
        self.assertEqual(markup.by_id('nl-status')['role'], 'status')
        self.assertEqual(markup.by_id('nl-error')['role'], 'alert')
        success = markup.by_id('nl-success')
        self.assertEqual(success['tabindex'], '-1')
        self.assertIsNotNone(markup.by_id(success['aria-labelledby']))
        self.assertIsNotNone(markup.by_id(success['aria-describedby']))
        self.assertIn('success.focus()', text)
        self.assertIn('cannot confirm that the subscription was processed', text)

    def test_design_markup_is_byte_preserved_except_fresh_homepage_asset_versions(self):
        for path in ('index.html', 'start-here.html', 'start-here.css', 'start-here.js', 'home-catalogue.css'):
            with self.subTest(path=path):
                current = read(path)
                current = restore_coffee_removal_text(path, current)
                if path == 'index.html':
                    current = current.replace('script.js?v=20261025-reference-support-v1', 'script.js?v=20261022-reader-review')
                    current = current.replace('home-page.min.css?v=20261025-reference-support-v1', 'home-page.min.css?v=20261025-reader-colours-v1')
                elif path == 'start-here.html':
                    current = normalize_start_here_desktop_html(path, current)
                elif path == 'start-here.css':
                    current = restore_start_here_desktop_asset(
                        path, current.encode('utf-8')
                    ).decode('utf-8')
                self.assertEqual(current, baseline(path))

    def test_reference_edits_do_not_change_any_tutorial_code_or_approved_images(self):
        count = 0
        for page in sorted((ROOT / 'tutorials').glob('*.html')):
            relative = page.relative_to(ROOT).as_posix()
            before = baseline(relative)
            raw_after = page.read_text(encoding='utf-8')
            after = normalize_editorial_review(relative, raw_after)
            code = lambda html: [unescape(re.sub('<[^>]+>', '', block)) for block in re.findall(r'<pre\b[^>]*>(.*?)</pre>', html, re.S)]
            image_sources = lambda html: [attrs.get('src') for tag, attrs in Markup(html).tags if tag == 'img']
            with self.subTest(page=relative):
                self.assertEqual(code(after), code(before), 'Reference review must not silently edit runnable code')
                self.assertEqual(code(raw_after), code(before), 'Raw reviewed source must preserve runnable code')
                self.assertEqual(image_sources(raw_after), image_sources(before), 'Reference review must preserve approved image sources')
                self.assertEqual(re.findall(r'<img\b[^>]*>', after), re.findall(r'<img\b[^>]*>', before))
            count += 1
        self.assertEqual(count, 58)


if __name__ == '__main__':
    unittest.main()
