"""Content, boundary, and visual contracts for the circular Start Here path."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "45d660c5f53a0f4d8c2736057e2ab54fe7b8e718"
CSS_VERSION = "20261025-circular-banner-v2"
JS_VERSION = "20261025-circular-path-v1"
FOUNDATION = ("tutorials/command-line-part1.html", "tutorials/computer-data-fundamentals.html")
LANGUAGE_CHOICES = ("tutorials/r-tidyverse-fundamentals.html", "tutorials/python-fundamentals-bioinformatics.html")
EVIDENCE = {
    FOUNDATION[0]: {"terminal", "location", "checking"},
    FOUNDATION[1]: {"project", "synthetic", "file"},
}
CAUTIONS = (
    "not a required course", "not a bulk RNA-seq tutorial", "replicated single-cell samples",
    "not substitutes for basic QC", "authorized institutional access",
    "not standardized on one Python or R version", "zero-byte placeholder files are not sequencing data",
)
LEGACY_IDS = ("sh-foundation", "sh-language-choice", "sh-routes", "sh-curriculum", "sh-hpc")


def git_bytes(revision, path):
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, check=False)
    return result.stdout if result.returncode == 0 else None


def pinned_paths():
    return subprocess.check_output(["git", "ls-tree", "-r", "--name-only", PUBLISHED], cwd=ROOT, text=True).splitlines()


class Facts(HTMLParser):
    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.links, self.elements, self.text = [], [], []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_data(self, data):
        self.text.append(data)


def main(markup):
    match = re.search(r"<main\b[^>]*>.*?</main\s*>", markup, re.S | re.I)
    if not match:
        raise AssertionError("Start Here page must contain a main element")
    return match.group()


def panel(markup, number):
    match = re.search(rf'<article\b(?=[^>]*\bid="sh-step-{number}")[^>]*>.*?</article\s*>', markup, re.S | re.I)
    if not match:
        raise AssertionError(f"missing lesson panel sh-step-{number}")
    return match.group()


def tutorial_links(markup):
    return {url for url in Facts(markup).links if url.startswith("tutorials/")}


class StartHereBlueLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.old = git_bytes(PUBLISHED, "start-here.html").decode("utf-8")
        cls.current_main, cls.old_main = main(cls.source), main(cls.old)
        cls.css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "start-here.js").read_text(encoding="utf-8")

    def test_home_catalogue_lessons_and_shared_assets_are_unchanged(self):
        for relative in ("index.html", "tutorials.html"):
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git_bytes(PUBLISHED, relative))
        lessons = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(lessons), 58)
        for page in lessons:
            relative = page.relative_to(ROOT).as_posix()
            with self.subTest(path=relative):
                self.assertEqual(page.read_bytes(), git_bytes(PUBLISHED, relative))
        protected = [path for path in pinned_paths()
                     if (path.endswith((".css", ".js")) and path not in {"start-here.css", "start-here.js"})
                     or path.startswith(("fonts/", "images/", "assets/")) or path == "ads.txt"]
        for relative in protected:
            with self.subTest(path=relative):
                self.assertEqual((ROOT / relative).read_bytes(), git_bytes(PUBLISHED, relative))

    def test_html_changes_only_in_main_and_start_here_asset_versions(self):
        old_css = re.search(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"', self.old).group(1)
        new_css = re.search(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"', self.source).group(1)
        old_js = re.search(r'<script\b[^>]*src="(start-here\.js\?v=[^"]+)"', self.old).group(1)
        new_js = re.search(r'<script\b[^>]*src="(start-here\.js\?v=[^"]+)"', self.source).group(1)
        expected = self.old.replace(main(self.old), self.current_main, 1)
        expected = expected.replace(old_css, new_css, 1).replace(old_js, new_js, 1)
        self.assertEqual(self.source, expected)
        self.assertEqual(new_css, f"start-here.css?v={CSS_VERSION}")
        self.assertEqual(new_js, f"start-here.js?v={JS_VERSION}")

    def test_four_ordered_lesson_panels_and_orbit_anchors(self):
        facts = Facts(self.current_main)
        orbit = next(attrs for _, attrs in facts.elements if "sh-orbit" in attrs.get("class", "").split())
        self.assertIn("hidden", orbit, "the orbit is revealed by the enhancement script")
        orbit_anchors = [(tag, attrs) for tag, attrs in facts.elements
                         if tag == "a" and "sh-orbit-stop" in attrs.get("class", "").split()]
        self.assertEqual(len(orbit_anchors), 4)
        for step, (_, attrs) in enumerate(orbit_anchors, 1):
            self.assertEqual(attrs.get("data-sh-step"), str(step))
            self.assertEqual(attrs.get("href"), f"#sh-step-{step}")
            self.assertNotIn("hidden", attrs)
        panels = [panel(self.current_main, step) for step in range(1, 5)]
        self.assertIn("introduction-to-bioinformatics.html", panels[0])
        self.assertIn(FOUNDATION[0], panels[1])
        self.assertIn(FOUNDATION[1], panels[2])
        self.assertLess(self.current_main.index(FOUNDATION[0]), self.current_main.index(FOUNDATION[1]))
        self.assertIn('id="sh-language-choice"', panels[3])
        for url in LANGUAGE_CHOICES:
            self.assertIn(url, panels[3])
        self.assertIn("Bash on Linux, macOS, or Windows Subsystem for Linux (WSL)", self.current_main)

    def test_beginner_outcomes_are_supported_by_their_linked_lesson_content(self):
        for number, href in ((2, FOUNDATION[0]), (3, FOUNDATION[1])):
            item = " ".join(unescape(re.sub(r"<[^>]*>", " ", panel(self.current_main, number))).split()).lower()
            lesson = (ROOT / href).read_text(encoding="utf-8").lower()
            item_terms = set(re.findall(r"[a-z][a-z0-9-]{3,}", item))
            lesson_terms = set(re.findall(r"[a-z][a-z0-9-]{3,}", lesson))
            with self.subTest(lesson=href):
                self.assertGreaterEqual(len(item.split()), 6)
                self.assertTrue(EVIDENCE[href] <= item_terms & lesson_terms)

    def test_all_32_tutorial_destinations_disclosure_cautions_and_legacy_targets_remain(self):
        old_links, new_links = tutorial_links(self.old_main), tutorial_links(self.current_main)
        self.assertEqual(len(old_links), 32)
        self.assertEqual(new_links, old_links)
        for url in new_links:
            with self.subTest(destination=url):
                self.assertTrue((ROOT / url.split("#", 1)[0]).is_file())
        facts = Facts(self.current_main)
        ids = [attrs["id"] for _, attrs in facts.elements if "id" in attrs]
        for anchor in LEGACY_IDS:
            self.assertEqual(ids.count(anchor), 1, anchor)
        self.assertEqual(len(ids), len(set(ids)), "fragment targets are unique")
        details = [attrs for tag, attrs in facts.elements if tag == "details"]
        self.assertEqual(len(details), 6)
        self.assertTrue(all("open" not in attrs for attrs in details))
        text = " ".join(facts.text).lower()
        for phrase in CAUTIONS:
            with self.subTest(caution=phrase):
                self.assertIn(phrase.lower(), text)
        optional = re.search(r'<details\b[^>]*id="sh-optional-tools".*?</details\s*>', self.current_main, re.S)
        self.assertIsNotNone(optional)
        self.assertIn("tutorials/conda-mamba-part1.html", optional.group())
        self.assertNotIn("tutorials/conda-mamba-part1.html", "".join(panel(self.current_main, n) for n in range(1, 5)))

    def test_copy_is_concise_and_does_not_claim_completion_or_progress(self):
        text = " ".join(Facts(self.current_main).text)
        self.assertLess(len(text.split()), 650)
        self.assertNotIn("\u2014", unescape(self.current_main))
        self.assertNotRegex(text.lower(), r"\b(?:completed|completion|percent complete)\b")

    def test_real_fragment_navigation_and_script_enhancement_are_present(self):
        self.assertIn("data-sh-step", self.js)
        self.assertIn("hidden", self.js)
        self.assertIn("sh-step-", self.js)
        self.assertRegex(self.js, r"(?:addEventListener|onclick)")
        for step in range(1, 5):
            self.assertIn(f'href="#sh-step-{step}"', self.current_main)
            self.assertIn(f'data-sh-step="{step}"', self.current_main)


if __name__ == "__main__":
    unittest.main()
