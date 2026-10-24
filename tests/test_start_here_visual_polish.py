"""Visual and hierarchy requirements for the current Start Here design."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS_VERSION = 'start-here.css?v=20261025-hover-colours-v1'


class ReadingText(HTMLParser):
    """Collect reading text while excluding decorative art and section labels."""
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


def rule(css, selector):
    match = re.search(re.escape(selector) + r'\s*\{([^}]*)\}', css, re.S)
    if not match:
        raise AssertionError(f'missing CSS rule: {selector}')
    return re.sub(r'\s+', ' ', match.group(1)).strip().lower()


class StartHereVisualPolishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.after = (ROOT / 'start-here.html').read_text(encoding='utf-8')
        cls.main = main(cls.after)
        cls.css = (ROOT / 'start-here.css').read_text(encoding='utf-8')

    def test_single_hero_lesson_card_and_nonduplicated_intro(self):
        hero = re.search(r'<section class="sh-hero".*?</section>', self.main, re.S).group()
        card = re.search(r'<div class="sh-first-lesson".*?</div>', hero, re.S).group()
        self.assertIn('Bioinformatics', hero)
        self.assertEqual(len(re.findall(r'<a\b', hero)), 1)
        self.assertIn('href="tutorials/introduction-to-bioinformatics.html"', card)
        self.assertIn('aria-describedby="sh-first-lesson-note"', card)
        self.assertIn('id="sh-first-lesson-note"', card)
        self.assertEqual(self.main.count('href="tutorials/introduction-to-bioinformatics.html"'), 1)

    def test_foundation_sequence_is_terminal_files_then_language_choice(self):
        match = re.search(r'<ol class="sh-steps" start="2">(.*?)</ol>', self.main, re.S)
        self.assertIsNotNone(match)
        steps = match.group(1)
        items = re.findall(r'<li\b.*?</li>', steps, re.S)
        self.assertEqual(len(items), 3)
        self.assertIn('tutorials/command-line-part1.html', items[0])
        self.assertIn('tutorials/computer-data-fundamentals.html', items[1])
        self.assertIn('Choose one language', items[2])
        self.assertIn('tutorials/r-tidyverse-fundamentals.html', items[2])
        self.assertIn('tutorials/python-fundamentals-bioinformatics.html', items[2])
        self.assertNotIn('conda-mamba-part1.html', steps)
        optional = re.search(r'<details\b[^>]*id="sh-optional-tools".*?</details>', self.main, re.S).group()
        self.assertIn('conda-mamba-part1.html', optional)

    def test_copy_is_concise_and_all_32_tutorial_destinations_are_visible(self):
        facts = ReadingText(self.main)
        self.assertLess(len(facts.words), 650)
        self.assertEqual(len({url for url in facts.links if url and url.startswith('tutorials/')}), 32)
        self.assertNotIn('\u2014', self.main)

    def test_first_lesson_card_and_primary_action_have_clear_visual_hierarchy(self):
        hero = rule(self.css, '.sh-hero')
        self.assertRegex(hero, r'background(?:-image)?\s*:\s*linear-gradient\(')
        self.assertIn('#19546b', hero, 'the banner uses the site ocean tone')
        self.assertIn('#123b5d', hero, 'the banner finishes in the site navy')
        self.assertIn('#dff2ff', hero, 'the banner starts with a light-blue field')
        mobile_hero = re.search(
            r'@media\s*\(max-width:\s*640px\)\s*\{.*?\.sh-hero\s*\{([^}]*)\}',
            self.css, re.S,
        ).group(1).lower()
        self.assertIn('#19546b', mobile_hero, 'the mobile banner retains the site ocean tone')
        self.assertIn('#123b5d', mobile_hero, 'the mobile banner retains site navy')
        self.assertIn('color: #08696d', rule(self.css, '.sh-hero h1 span'))
        self.assertIn('background: #08696d', rule(self.css, '.sh-eyebrow::before'))
        card = rule(self.css, '.sh-first-lesson')
        self.assertRegex(card, r'background\s*:\s*#fff(?:fff)?\b')
        self.assertRegex(card, r'border-radius\s*:')
        self.assertRegex(card, r'box-shadow\s*:')
        button = rule(self.css, '#main-content .sh-primary-link')
        self.assertRegex(button, r'background\s*:\s*#123b5d\b')
        self.assertRegex(button, r'color\s*:\s*#fff(?:fff)?\b')
        self.assertRegex(button, r'min-height\s*:\s*(?:3\.25rem|52px)')
        self.assertIn('text-decoration: none', button)

    def test_connected_steps_and_language_choice_have_explicit_visual_structure(self):
        self.assertIn('.sh-step:not(:last-child)::after', self.css)
        self.assertIn('counter(shstep, decimal-leading-zero)', self.css)
        self.assertIn('.sh-choice-links { display: grid;', self.css)
        self.assertIn('content: "→"', self.css)
        self.assertNotIn('↗', self.css)

    def test_accessible_responsive_and_print_states_remain_explicit(self):
        for value in [':focus-visible', '@media (max-width: 960px)', '@media (max-width: 760px)',
                      '@media (max-width: 640px)', '@media (max-width: 350px)',
                      '@media (prefers-reduced-motion: reduce)', '@media print']:
            self.assertIn(value, self.css)
        focus = re.search(r'#main-content \.sh-hero :focus-visible\s*\{([^}]*)\}', self.css, re.S).group(1)
        self.assertIn('outline-color: #123b5d', focus)
        self.assertIn('0 0 0 2px #fff', focus)
        self.assertIn('text-align: left', self.css)
        self.assertNotIn('text-align: center', self.css)
        self.assertNotIn('url(', self.css)

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
