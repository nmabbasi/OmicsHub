"""Strict boundary and visual contracts for the Start Here blue-learning revision."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "19ec34c2227b9daeb4b32764d3ad32dafb17d87a"
LONG_FORM_BASELINE = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
FOUNDATION = (
    "tutorials/introduction-to-bioinformatics.html",
    "tutorials/command-line-part1.html",
    "tutorials/computer-data-fundamentals.html",
    "tutorials/conda-mamba-part1.html",
)
FOUNDATION_EVIDENCE = {
    "tutorials/introduction-to-bioinformatics.html": {"question", "data", "plan"},
    "tutorials/command-line-part1.html": {"terminal", "location", "checking"},
    "tutorials/computer-data-fundamentals.html": {"project", "synthetic", "file"},
    "tutorials/conda-mamba-part1.html": {"micromamba", "permission", "packages"},
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
        expected = self.old.replace(self.old_main, self.current_main, 1)
        expected = expected.replace(old_href, new_href, 1)
        self.assertEqual(self.source, expected)
        self.assertRegex(new_href, r"^start-here\.css\?v=[A-Za-z0-9._-]+$")

    def test_four_foundation_steps_one_intro_cta_and_all_32_destinations_remain(self):
        hero = re.search(r'<section class="sh-hero".*?</section>', self.current_main, re.S).group()
        self.assertEqual(len(re.findall(r"<a\b", hero)), 1)
        self.assertIn('href="tutorials/introduction-to-bioinformatics.html"', hero)
        self.assertIn('aria-describedby="sh-first-lesson-note"', hero)
        self.assertIn('id="sh-first-lesson-note"', self.current_main)

        steps = re.search(r'<ol class="sh-steps">(.*?)</ol>', self.current_main, re.S).group(1)
        self.assertEqual(len(re.findall(r"<li\b", steps)), 4)
        step_links = re.findall(r'<h3><a href="([^"]+)"', steps)
        self.assertEqual(tuple(step_links), FOUNDATION)

        old_links = {url for url in PageFacts(self.old_main).links if url.startswith("tutorials/")}
        new_links = {url for url in PageFacts(self.current_main).links if url.startswith("tutorials/")}
        self.assertEqual(len(old_links), 32)
        self.assertEqual(new_links, old_links)
        self.assertTrue(all((ROOT / url.split("#", 1)[0]).is_file() for url in new_links))

    def test_visible_start_here_copy_is_more_concise_than_the_published_page(self):
        long_form = git_bytes(LONG_FORM_BASELINE, "start-here.html").decode("utf-8")
        old_long_form_main = main(long_form)
        old_words = len(" ".join(PageFacts(old_long_form_main).text).split())
        new_words = len(" ".join(PageFacts(self.current_main).text).split())
        self.assertLess(new_words, old_words * 0.55)
        self.assertLess(new_words, 650)

    def test_blue_banner_direction_readability_and_keyboard_focus(self):
        hero = css_rule(self.css, ".sh-hero")
        self.assertRegex(
            hero,
            r"background(?:-image)?\s*:\s*linear-gradient\(\s*90deg\s*,\s*#dff2ff\b[^)]*#123b5d",
        )
        heading = css_rule(self.css, ".sh-hero h1")
        self.assertRegex(heading, r"color\s*:\s*(?:#123b5d|var\(--sh-navy\))")
        body = css_rule(self.css, ".sh-hero p:not(.sh-eyebrow)")
        self.assertRegex(body, r"color\s*:\s*(?:#123b5d|var\(--sh-navy\))")
        button = css_rule(self.css, "#main-content .sh-primary-link")
        self.assertRegex(button, r"background\s*:\s*#123b5d\b")
        self.assertRegex(button, r"color\s*:\s*#fff(?:fff)?\b")
        focus = css_rule(self.css, "#main-content .sh-hero :focus-visible")
        self.assertRegex(focus, r"outline(?:-color)?\s*:[^;]*#123b5d")
        self.assertRegex(focus, r"box-shadow\s*:[^;]*#fff(?:fff)?")
        self.assertNotRegex(self.css.lower(), r"outline-color\s*:\s*#fff(?:fff)?\b")

    def test_outcomes_are_supported_by_linked_lessons_and_cautionary_copy_is_retained(self):
        step_markup = re.search(r'<ol class="sh-steps">(.*?)</ol>', self.current_main, re.S).group(1)
        items = re.findall(r"<li\b.*?</li>", step_markup, re.S)
        self.assertEqual(len(items), 4)
        for href, item in zip(FOUNDATION, items):
            with self.subTest(lesson=href):
                visible = " ".join(unescape(re.sub(r"<[^>]*>", " ", item)).split()).lower()
                self.assertGreaterEqual(len(visible.split()), 6)
                lesson_html = (ROOT / href).read_text(encoding="utf-8").lower()
                item_terms = {word for word in re.findall(r"[a-z][a-z0-9-]{3,}", visible)}
                lesson_terms = {word for word in re.findall(r"[a-z][a-z0-9-]{3,}", lesson_html)}
                overlap = item_terms & lesson_terms
                self.assertTrue(
                    FOUNDATION_EVIDENCE[href] <= overlap,
                    f"beginner outcomes must be supported by lesson-specific content in {href}",
                )

        text = unescape(" ".join(PageFacts(self.current_main).text)).lower()
        for phrase in CAUTIONS:
            with self.subTest(caution=phrase):
                self.assertIn(phrase.lower(), text)
        self.assertNotIn("\u2014", text)
        self.assertEqual(self.current_main.count("<details"), 6)
        self.assertTrue(all(not re.search(r"\bopen\b", tag) for tag in re.findall(r"<details\b[^>]*>", self.current_main)))


if __name__ == "__main__":
    unittest.main()
