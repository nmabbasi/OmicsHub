"""Exact runtime boundary and interaction-state contracts for Start Here."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "2ee199d3bdf3a876b9cb1f185f298f5fa8c4dcc7"
OLD_HREF = 'start-here.css?v=20261025-lesson-first-v2'
NEW_HREF = 'start-here.css?v=20261025-hover-colours-v1'
OLD_CHOICE = (
    '#main-content .sh-choice-links a { display: flex; align-items: center; '
    'justify-content: space-between; min-height: 3rem; gap: 1rem; padding: .7rem 1rem; '
    'border: 1px solid #d0e0e8; border-radius: .55rem; background: #f7fafc; '
    'color: var(--sh-navy); font-size: .85rem; font-weight: 700; text-decoration: none; '
    'transition: background-color 150ms ease, border-color 150ms ease; }\n'
)
NEW_CHOICE = (
    '#main-content .sh-choice-links a { display: flex; align-items: center; '
    'justify-content: space-between; min-height: 3rem; gap: 1rem; padding: .7rem 1rem; '
    'border: 1px solid #d0e0e8; border-radius: .55rem; background: #f7fafc; '
    'color: var(--sh-navy); font-size: .85rem; font-weight: 700; text-decoration: none; '
    'transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease, '
    'box-shadow 150ms ease; }\n'
)
OLD_HOVER = '#main-content .sh-choice-links a:hover { border-color: #4a8e9f; background: #edf6f9; }\n'
INTERACTION_CSS = '''/* Coloured feedback stays on the six learner choices, not the reading content. */
#sh-routes .sh-details { transition: border-color 150ms ease; }
#sh-routes .sh-details summary { border-radius: .65rem; transition: background-color 150ms ease, color 150ms ease, box-shadow 150ms ease; }
#sh-routes .sh-topic-icon { transition: background-color 150ms ease, color 150ms ease; }
#sh-routes .sh-details[open] { border-color: #65a9b7; }
#sh-routes .sh-details[open] summary { border-radius: .65rem .65rem 0 0; background: #e5f4f8; }
#main-content .sh-choice-links a:is(:focus-visible, :active),
#sh-routes .sh-details summary:is(:focus-visible, :active) { background: #123b5d; color: #fff; box-shadow: inset 0 0 0 1px #318b9b; }
#main-content .sh-choice-links a:is(:focus-visible, :active) { border-color: #318b9b; }
#main-content .sh-choice-links a:is(:focus-visible, :active) span,
#sh-routes .sh-details summary:is(:focus-visible, :active)::after { color: #9be4d8; }
#sh-routes .sh-details summary:is(:focus-visible, :active) .sh-topic-icon { background: #9be4d8; color: #123b5d; }
@media (hover: hover) and (pointer: fine) {
  #main-content .sh-choice-links a:hover,
  #sh-routes .sh-details summary:hover { background: #123b5d; color: #fff; box-shadow: inset 0 0 0 1px #318b9b; }
  #main-content .sh-choice-links a:hover { border-color: #318b9b; }
  #sh-routes .sh-details:has(> summary:hover) { border-color: #318b9b; }
  #main-content .sh-choice-links a:hover span,
  #sh-routes .sh-details summary:hover::after { color: #9be4d8; }
  #sh-routes .sh-details summary:hover .sh-topic-icon { background: #9be4d8; color: #123b5d; }
}
'''
PRINT_CSS = '''  #main-content .sh-choice-links a, #sh-routes .sh-details summary { background: #fff !important; color: #123b5d !important; box-shadow: none !important; }
  #main-content .sh-choice-links a span, #sh-routes .sh-details summary::after, #sh-routes .sh-topic-icon { color: #123b5d !important; }
  #sh-routes .sh-topic-icon { background: transparent !important; }
'''


def git_text(path):
    return subprocess.check_output(["git", "show", f"{PUBLISHED}:{path}"], cwd=ROOT).decode("utf-8")


def page_main(markup):
    match = re.search(r"<main\b[^>]*>.*?</main\s*>", markup, re.S | re.I)
    if not match:
        raise AssertionError("expected one Start Here main element")
    return match.group(0)


class StartHereHoverBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published_html = git_text("start-here.html")
        cls.current_html = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.published_css = git_text("start-here.css")
        cls.current_css = (ROOT / "start-here.css").read_text(encoding="utf-8")

    def test_html_is_exactly_published_page_except_the_named_stylesheet_cache_version(self):
        self.assertEqual(self.published_html.count(OLD_HREF), 1)
        expected = self.published_html.replace(OLD_HREF, NEW_HREF, 1)
        self.assertEqual(self.current_html, expected)
        self.assertEqual(page_main(self.current_html), page_main(self.published_html))
        old_hero = re.search(r'<section class="sh-hero".*?</section>', page_main(self.published_html), re.S).group()
        new_hero = re.search(r'<section class="sh-hero".*?</section>', page_main(self.current_html), re.S).group()
        self.assertEqual(new_hero, old_hero)
        destinations = re.findall(r'<a\b[^>]*href="(tutorials/[^"#]+(?:#[^"]*)?)"', page_main(self.current_html))
        old_destinations = re.findall(r'<a\b[^>]*href="(tutorials/[^"#]+(?:#[^"]*)?)"', page_main(self.published_html))
        self.assertEqual(len(set(destinations)), 32)
        self.assertEqual(destinations, old_destinations)

    def test_css_diff_is_only_the_scoped_interaction_rules_and_print_reset(self):
        expected = self.published_css
        self.assertEqual(expected.count(OLD_CHOICE), 1)
        expected = expected.replace(OLD_CHOICE, NEW_CHOICE, 1)
        self.assertEqual(expected.count(OLD_HOVER), 1)
        expected = expected.replace(OLD_HOVER, "", 1)
        insertion_point = '.sh-details-body a { font-weight: 600; text-decoration: underline; }\n'
        self.assertEqual(expected.count(insertion_point), 1)
        expected = expected.replace(insertion_point, insertion_point + INTERACTION_CSS, 1)
        print_anchor = '  .sh-details { margin-bottom: .75rem; }\n'
        self.assertEqual(expected.count(print_anchor), 1)
        expected = expected.replace(print_anchor, print_anchor + PRINT_CSS, 1)
        self.assertEqual(self.current_css, expected)

    def test_six_choices_receive_focus_active_and_mouse_only_states(self):
        main = page_main(self.current_html)
        choice_match = re.search(r'<div class="sh-choice-links">(.*?)</div>', main, re.S)
        self.assertIsNotNone(choice_match)
        self.assertEqual(len(re.findall(r'<a\b', choice_match.group(1))), 2)
        route_match = re.search(r'<section[^>]*id="sh-routes".*?</section>', main, re.S)
        self.assertIsNotNone(route_match)
        route = route_match.group(0)
        self.assertEqual(len(re.findall(r'<details\b[^>]*class="sh-details"', route)), 4)
        self.assertEqual(len(re.findall(r'<summary>', route)), 4)
        self.assertIn('#main-content .sh-choice-links a:is(:focus-visible, :active)', INTERACTION_CSS)
        self.assertIn('#sh-routes .sh-details summary:is(:focus-visible, :active)', INTERACTION_CSS)
        self.assertIn('@media (hover: hover) and (pointer: fine) {', INTERACTION_CSS)
        gated = INTERACTION_CSS.split('@media (hover: hover) and (pointer: fine) {', 1)[1]
        self.assertEqual(gated.count('.sh-choice-links a:hover'), 3)
        self.assertEqual(gated.count('.sh-details summary:hover'), 3)
        self.assertIn('color: #fff', gated)
        self.assertIn('color: #9be4d8', gated)
        self.assertIn('#sh-routes .sh-details[open] summary { border-radius: .65rem .65rem 0 0; background: #e5f4f8; }', INTERACTION_CSS)
        self.assertNotIn(':hover', INTERACTION_CSS.split('@media (hover: hover) and (pointer: fine) {', 1)[0])

    def test_print_keeps_foreground_and_decorative_icons_ink_safe(self):
        self.assertIn('summary { background: #fff !important; color: #123b5d !important; box-shadow: none !important; }', PRINT_CSS)
        self.assertIn('summary::after, #sh-routes .sh-topic-icon { color: #123b5d !important; }', PRINT_CSS)
        self.assertIn('#sh-routes .sh-topic-icon { background: transparent !important; }', PRINT_CSS)


if __name__ == "__main__":
    unittest.main()
