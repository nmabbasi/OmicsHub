"""Visual-only refinement contracts, independent of the reviewed scope adapters."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = '19ec34c2227b9daeb4b32764d3ad32dafb17d87a'
OLD_CSS_VERSION = 'start-here.css?v=20261024-start-simple'
NEW_CSS_VERSION = 'start-here.css?v=20261024-blue-learning-v1'

# Exact, auditor-reviewed source fragments only. This deliberately does not
# strip or ignore reading text: every permitted copy edit is spelled out here.
COPY_REPLACEMENTS = {
    '<p>Bioinformatics can begin with a biological question and a few basic computer skills. You do not need to choose a specialty or learn every tool today.</p>':
    '<p>Start with the big picture. Then build the computer skills to work with biological data.</p>',
    '''      <a class="sh-primary-link" href="tutorials/introduction-to-bioinformatics.html">Begin: Introduction to Bioinformatics <span aria-hidden="true">→</span></a>
      <p class="sh-note">Suggested routes, not a required course or a complete analysis pipeline.</p>''':
    '''      <a class="sh-primary-link" href="tutorials/introduction-to-bioinformatics.html" aria-describedby="sh-first-lesson-note">Start the first lesson <span aria-hidden="true">→</span></a>
      <p class="sh-note" id="sh-first-lesson-note">Introduction to Bioinformatics: a conceptual guide and planning exercise.</p>''',
    '<p class="sh-section-intro">Start at the beginning, or skip what you already know. Check each lesson\'s prerequisites, software, and practice inputs before you begin.</p>':
    '<p class="sh-section-intro">Follow the steps in order. If you already know a skill, move to the next one. Set up project software only when you need it.</p>',
    '''        <li class="sh-step">
          <div><h3><a href="tutorials/introduction-to-bioinformatics.html">Get oriented</a></h3>
            <p class="sh-step-meta">See how biological questions, data, and tools fit together. No installation needed.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/computer-data-fundamentals.html">Understand files and computers</a></h3>
            <p class="sh-step-meta">Learn files, folders, and basic computing with a small practice exercise.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/command-line-part1.html">Try the command line</a></h3>
            <p class="sh-step-meta">Practice safe navigation in a terminal. Continue with <a href="tutorials/command-line-part2.html">Part 2</a> or <a href="tutorials/command-line-part3.html">Part 3</a> when you need those skills.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/conda-mamba-part1.html">Learn about software environments</a></h3>
            <p class="sh-step-meta">Keep the software for one project separate from another.</p></div>
        </li>''':
    '''        <li class="sh-step">
          <div><h3><a href="tutorials/introduction-to-bioinformatics.html">Get the big picture</a></h3>
            <p class="sh-step-meta">Connect a biological question to data and methods. Draft a one-page analysis plan.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/command-line-part1.html">Find your way in the terminal</a></h3>
            <p class="sh-step-meta">Practice checking your location and moving between folders. Keep <a href="tutorials/command-line-part2.html">Part 2</a> and <a href="tutorials/command-line-part3.html">Part 3</a> for later.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/computer-data-fundamentals.html">Work with files and data</a></h3>
            <p class="sh-step-meta">Create a project folder and check a tiny synthetic practice file. Use the terminal skills from step 2.</p></div>
        </li>
        <li class="sh-step">
          <div><h3><a href="tutorials/conda-mamba-part1.html">Set up software when you need it</a></h3>
            <p class="sh-step-meta">Use Micromamba to isolate a project\'s software. This needs terminal comfort and permission to install packages.</p></div>
        </li>''',
    '<p>You do not need both. Pick the language that fits your project or collaborators.</p>':
    '<p>Use your team\'s language, or choose either route. Learn one for now and follow its setup notes.</p>',
    '<p class="sh-bridge">Both routes continue to <a href="tutorials/statistics-for-bioinformatics.html">statistics</a> and <a href="tutorials/experimental-design-batch-effects.html">study design and batch effects</a>.</p>':
    '<p class="sh-bridge">When needed, use <a href="tutorials/statistics-for-bioinformatics.html">statistics for independent two-group comparisons</a> or <a href="tutorials/experimental-design-batch-effects.html">study design and batch effects</a>.</p>',
    '<h2 id="sh-routes-title">Choose a research topic when you are ready</h2>':
    '<h2 id="sh-routes-title">Explore a topic when you are ready</h2>',
    '<p class="sh-section-intro">These optional starting points are not extra prerequisites. Open only the topic that matches your work.</p>':
    '<p class="sh-section-intro">These routes are optional, not extra prerequisites. Open only the topic that matches your biological question.</p>',
    '<p class="sh-section-intro">You can start without a cluster, workflow engine, or container. Check each lesson for its own software, input, and prerequisite details.</p>':
    '<p class="sh-section-intro">You do not need a cluster to begin. Use these guides only when a project needs them, and follow each lesson\'s setup notes.</p>',
    '<p>Browse the full catalogue and check each lesson\'s format and requirements.</p>':
    '<p>Browse the full catalogue and check each lesson\'s format and requirements. Suggested routes, not a required course or a complete analysis pipeline.</p>',
}


def apply_reviewed_copy(source):
    """Apply each exact approved replacement once; reject missing/duplicate chunks."""
    for before, after in COPY_REPLACEMENTS.items():
        count = source.count(before)
        if count != 1:
            raise AssertionError(f"reviewed copy chunk must occur once: {before[:80]!r}")
        source = source.replace(before, after, 1)
    return source


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
        cls.before = subprocess.check_output(['git', 'show', f'{PUBLISHED}:start-here.html'], cwd=ROOT).decode()
        cls.after = (ROOT / 'start-here.html').read_text()
        cls.css = (ROOT / 'start-here.css').read_text()

    def test_only_exact_reviewed_copy_changes_and_all_original_destinations_remain(self):
        reviewed = apply_reviewed_copy(self.before)
        old_css = 'start-here.css?v=20261024-start-simple'
        self.assertEqual(reviewed.count(old_css), 1)
        reviewed = reviewed.replace(old_css, NEW_CSS_VERSION, 1)
        self.assertEqual(reviewed, self.after)
        old, new = ReadingText(main(reviewed)), ReadingText(main(self.after))
        self.assertEqual(old.words, new.words)
        self.assertEqual(set(old.links), set(new.links))
        self.assertEqual(len({url for url in new.links if url.startswith('tutorials/')}), 32)
        self.assertNotIn('\u2014', main(self.after))

    def test_no_external_assets_tracking_or_outside_main_changes(self):
        expected = apply_reviewed_copy(self.before)
        self.assertEqual(expected.replace(OLD_CSS_VERSION, NEW_CSS_VERSION, 1), self.after)
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
        focus = re.search(r'#main-content \.sh-hero :focus-visible\s*\{([^}]*)\}', self.css, re.S).group(1)
        self.assertIn('outline-color: #123b5d', focus)
        self.assertIn('0 0 0 2px #fff', focus)
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
