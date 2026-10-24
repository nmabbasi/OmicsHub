"""Visual-only refinement contracts, independent of the reviewed scope adapters."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRE_POLISH = '0dc6eec'


class ReadingText(HTMLParser):
    """Collect actual reading text, excluding decorative art and new section labels."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.words = []
        self.links = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = tag == 'svg' or attrs.get('class') == 'sh-section-kicker'
        self.stack.append((tag, skip or (self.stack[-1][1] if self.stack else False)))
        if tag == 'a':
            self.links.append(attrs.get('href'))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, text):
        if not self.stack or not self.stack[-1][1]:
            self.words.extend(text.split())


def main(source):
    return re.search(r'<main\b.*?</main>', source, re.S).group()


class StartHereVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = subprocess.check_output(['git', 'show', f'{PRE_POLISH}:start-here.html'], cwd=ROOT).decode()
        cls.after = (ROOT / 'start-here.html').read_text()
        cls.css = (ROOT / 'start-here.css').read_text()

    def test_all_existing_teaching_words_and_link_order_are_unchanged(self):
        old, new = ReadingText(main(self.before)), ReadingText(main(self.after))
        self.assertEqual(old.words, new.words)
        self.assertEqual(old.links, new.links)
        self.assertEqual(len({url for url in new.links if url.startswith('tutorials/')}), 32)
        self.assertNotIn('\u2014', main(self.after))

    def test_no_external_assets_tracking_or_outside_main_changes(self):
        self.assertEqual(self.before.replace(main(self.before), main(self.after), 1), self.after)
        self.assertNotIn('url(', self.css)
        self.assertIn('class="sh-hero-art" aria-hidden="true" focusable="false"', self.after)
        self.assertEqual(main(self.after).count('class="sh-section-kicker"'), 3)

    def test_connected_steps_and_internal_link_arrow_are_explicit(self):
        self.assertIn('.sh-step:not(:last-child)::after', self.css)
        self.assertIn('counter(shstep, decimal-leading-zero)', self.css)
        self.assertIn('content: "→"', self.css)
        self.assertNotIn('↗', self.css)
        self.assertIn('.sh-choice-links { display: grid;', self.css)

    def test_accessible_responsive_and_print_states_remain_explicit(self):
        for value in [':focus-visible', '@media (max-width: 960px)', '@media (max-width: 640px)',
                      '@media (max-width: 350px)', '@media (prefers-reduced-motion: reduce)', '@media print']:
            self.assertIn(value, self.css)
        self.assertIn('outline-color: #fff', self.css)
        self.assertIn('text-align: left', self.css)
        self.assertNotIn('text-align: center', self.css)

    def test_circle_stays_label_free_and_protects_reading_and_footer_actions(self):
        circle = (ROOT / 'back-to-top.css').read_text()
        script = (ROOT / 'subscribe-fab.js').read_text()
        self.assertRegex(circle, r'#back-to-top > span:last-child\s*\{\s*display: none;')
        self.assertIn('aria-label="Back to top"', self.after)
        self.assertIn('border-radius: 50%', circle)
        self.assertIn('range.getClientRects()', script)
        self.assertIn('body h1, body h2, body h3', script)
        self.assertIn('body a[href], body button', script)
        self.assertIn('if (block.contains(existing) || !block.getClientRects().length) return false;', script)


if __name__ == '__main__':
    unittest.main()
