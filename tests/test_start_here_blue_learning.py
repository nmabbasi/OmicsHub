"""Strict boundary and visual contracts for the Start Here lesson-first revision."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "19ec34c2227b9daeb4b32764d3ad32dafb17d87a"
LONG_FORM_BASELINE = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
CSS_VERSION = "20261025-lesson-first-v2"
FOUNDATION = (
    "tutorials/command-line-part1.html",
    "tutorials/computer-data-fundamentals.html",
)
LANGUAGE_CHOICES = (
    "tutorials/r-tidyverse-fundamentals.html",
    "tutorials/python-fundamentals-bioinformatics.html",
)
FOUNDATION_EVIDENCE = {
    "tutorials/command-line-part1.html": {"terminal", "location", "checking"},
    "tutorials/computer-data-fundamentals.html": {"project", "synthetic", "file"},
}
CAUTIONS = (
    "not a required course",
    "not a bulk RNA-seq tutorial",
    "replicated single-cell samples",
    "not substitutes for basic QC",
    "authorized institutional access",
    "not standardized on one Python or R version",
    "zero-byte placeholder files are not sequencing data",
)


def git_bytes(revision, path):
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def pinned_paths():
    return subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", PUBLISHED],
        cwd=ROOT, text=True,
    ).splitlines()


class PageFacts(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = []
        self.text = []
        self.stack = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if "id" in attrs:
            self.ids.append(attrs["id"])
        self.stack.append(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.text.append(data)


def main(markup):
    match = re.search(r"<main\b[^>]*>.*?</main\s*>", markup, re.S | re.I)
    if not match:
        raise AssertionError("Start Here page must contain one main element")
    return match.group(0)


def start_css_href(markup):
    matches = re.findall(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"[^>]*>', markup)
    if len(matches) != 1:
        raise AssertionError("expected exactly one versioned Start Here stylesheet link")
    return matches[0]


def css_rule(css, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css, re.I | re.S)
    if not match:
        raise AssertionError(f"missing CSS rule for {selector}")
    return re.sub(r"\s+", " ", match.group(1)).strip().lower()


class StartHereBlueLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.old = git_bytes(PUBLISHED, "start-here.html").decode("utf-8")
        cls.current_main = main(cls.source)
        cls.old_main = main(cls.old)
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")

    def test_home_catalogue_scientific_pages_and_shared_assets_are_unchanged(self):
        for relative in ("index.html", "tutorials.html"):
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git_bytes(PUBLISHED, relative))

        lessons = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(lessons), 58)
        for page in lessons:
            relative = page.relative_to(ROOT).as_posix()
            with self.subTest(path=relative):
                self.assertEqual(page.read_bytes(), git_bytes(PUBLISHED, relative))

        # The new Start Here stylesheet is the only permitted shared-code exception.
        protected = [
            path for path in pinned_paths()
            if path.endswith((".css", ".js")) and path != "start-here.css"
            or path.startswith(("fonts/", "images/", "assets/"))
            or path in {"ads.txt"}
        ]
        for relative in protected:
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git_bytes(PUBLISHED, relative))

    def test_only_main_and_the_named_stylesheet_version_change_in_start_here_html(self):
        old_href = start_css_href(self.old)
        new_href = start_css_href(self.source)
        expected = self.old.replace(main(self.old), self.current_main, 1)
        expected = expected.replace(old_href, new_href, 1)
        self.assertEqual(self.source, expected)
        self.assertEqual(new_href, f"start-here.css?v={CSS_VERSION}")

    def test_one_intro_cta_three_ordered_steps_and_all_32_destinations_remain(self):
        hero = re.search(r'<section class="sh-hero".*?</section>', self.current_main, re.S).group()
        self.assertEqual(len(re.findall(r"<a\b", hero)), 1)
        intro_href = 'href="tutorials/introduction-to-bioinformatics.html"'
        self.assertIn(intro_href, hero)
        self.assertEqual(self.current_main.count(intro_href), 1, "intro lesson is the hero CTA, not a repeated timeline item")
        self.assertIn('aria-describedby="sh-first-lesson-note"', hero)
        self.assertIn('id="sh-first-lesson-note"', hero)

        match = re.search(r'<ol class="sh-steps" start="2">(.*?)</ol>', self.current_main, re.S)
        self.assertIsNotNone(match, "the ordered basics must start at lesson 02")
        steps = match.group(1)
        items = re.findall(r"<li\b.*?</li>", steps, re.S)
        self.assertEqual(len(items), 3)
        self.assertEqual(
            re.findall(r'<h3><a href="([^"]+)"', steps),
            list(FOUNDATION),
        )
        self.assertLess(steps.index(FOUNDATION[0]), steps.index(FOUNDATION[1]))
        choice = re.search(r'<section class="sh-choice".*?</section>', steps, re.S).group()
        choice_links = re.findall(r'<a href="([^"]+)"', choice)
        self.assertEqual(tuple(choice_links), LANGUAGE_CHOICES)

        old_links = {url for url in PageFacts(self.old_main).links if url.startswith("tutorials/")}
        new_links = {url for url in PageFacts(self.current_main).links if url.startswith("tutorials/")}
        self.assertEqual(len(old_links), 32)
        self.assertEqual(new_links, old_links)
        self.assertTrue(all((ROOT / url.split("#", 1)[0]).is_file() for url in new_links))

    def test_software_setup_is_optional_and_bash_precedes_the_file_lab(self):
        steps = re.search(r'<ol class="sh-steps" start="2">(.*?)</ol>', self.current_main, re.S).group(1)
        self.assertLess(steps.index("command-line-part1.html"), steps.index("computer-data-fundamentals.html"))
        self.assertIn("Bash on Linux, macOS, or Windows Subsystem for Linux (WSL)", self.current_main)
        self.assertNotIn("conda-mamba-part1.html", steps)
        optional = re.search(r'<details\b[^>]*id="sh-optional-tools".*?</details>', self.current_main, re.S).group()
        self.assertIn("conda-mamba-part1.html", optional)
        self.assertEqual(self.current_main.count("conda-mamba-part1.html"), 1)

    def test_visible_start_here_copy_is_more_concise_than_the_published_page(self):
        long_form = git_bytes(LONG_FORM_BASELINE, "start-here.html").decode("utf-8")
        old_long_form_main = main(long_form)
        old_words = len(" ".join(PageFacts(old_long_form_main).text).split())
        new_words = len(" ".join(PageFacts(self.current_main).text).split())
        self.assertLess(new_words, old_words * 0.55)
        self.assertLess(new_words, 650)

    def test_hero_design_has_a_white_first_lesson_card_and_readable_call_to_action(self):
        hero = css_rule(self.css, ".sh-hero")
        self.assertRegex(hero, r"background(?:-image)?\s*:\s*linear-gradient\(")
        card = css_rule(self.css, ".sh-first-lesson")
        self.assertRegex(card, r"background\s*:\s*#fff(?:fff)?\b")
        self.assertRegex(card, r"border-radius\s*:")
        self.assertRegex(card, r"box-shadow\s*:")
        heading = css_rule(self.css, ".sh-hero h1")
        self.assertRegex(heading, r"color\s*:\s*(?:#123b5d|var\(--sh-navy\))")
        button = css_rule(self.css, "#main-content .sh-primary-link")
        self.assertRegex(button, r"background\s*:\s*#123b5d\b")
        self.assertRegex(button, r"color\s*:\s*#fff(?:fff)?\b")
        self.assertIn("min-height: 3.25rem", button)

    def test_outcomes_are_supported_and_cautions_and_disclosures_remain(self):
        step_markup = re.search(r'<ol class="sh-steps" start="2">(.*?)</ol>', self.current_main, re.S).group(1)
        items = re.findall(r"<li\b.*?</li>", step_markup, re.S)
        self.assertEqual(len(items), 3)
        for href, item in zip(FOUNDATION, items[:2]):
            with self.subTest(lesson=href):
                visible = " ".join(unescape(re.sub(r"<[^>]*>", " ", item)).split()).lower()
                self.assertGreaterEqual(len(visible.split()), 6)
                lesson_html = (ROOT / href).read_text(encoding="utf-8").lower()
                item_terms = {word for word in re.findall(r"[a-z][a-z0-9-]{3,}", visible)}
                lesson_terms = {word for word in re.findall(r"[a-z][a-z0-9-]{3,}", lesson_html)}
                self.assertTrue(
                    FOUNDATION_EVIDENCE[href] <= (item_terms & lesson_terms),
                    f"beginner outcomes must be supported by lesson-specific content in {href}",
                )

        text = unescape(" ".join(PageFacts(self.current_main).text)).lower()
        for phrase in CAUTIONS:
            with self.subTest(caution=phrase):
                self.assertIn(phrase.lower(), text)
        self.assertNotIn("\u2014", text)
        details = re.findall(r"<details\b[^>]*>", self.current_main)
        self.assertEqual(len(details), 6)
        self.assertTrue(all(not re.search(r"\bopen\b", tag) for tag in details))


if __name__ == "__main__":
    unittest.main()
