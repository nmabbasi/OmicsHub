"""Accessible beginner-navigation contracts for the four-step Start Here journey."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED = "45d660c5f53a0f4d8c2736057e2ab54fe7b8e718"
MAIN = re.compile(r"<main\b[^>]*>.*?</main\s*>", re.S | re.I)


class Facts(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.elements = []
        self.text = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))

    def handle_data(self, data):
        self.text.append(data)


def original(path):
    return subprocess.check_output(["git", "show", f"{PUBLISHED}:{path}"], cwd=ROOT).decode("utf-8")


def page_main(source):
    match = MAIN.search(source)
    if not match:
        raise AssertionError("Start Here page must contain a main element")
    return match.group()


def panel(main, number):
    match = re.search(
        rf'<article\b(?=[^>]*\bid="sh-step-{number}")[^>]*>.*?</article\s*>',
        main, re.S | re.I,
    )
    if not match:
        raise AssertionError(f"missing lesson panel sh-step-{number}")
    return match.group()


class StartHereJourneyUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.main = page_main(cls.source)
        cls.before = original("start-here.html")
        cls.old_main = page_main(cls.before)
        cls.facts = Facts(cls.main)
        cls.js = (ROOT / "start-here.js").read_text(encoding="utf-8")

    def test_hero_is_compact_and_has_no_call_to_action(self):
        hero = re.search(r'<section\b[^>]*class="[^"]*\bsh-hero\b[^"]*".*?</section\s*>', self.main, re.S)
        self.assertIsNotNone(hero)
        hero_markup = hero.group()
        self.assertTrue(re.search(r"<h1\b", hero_markup))
        self.assertTrue(re.search(r"bioinformatics", hero_markup, re.I))
        self.assertEqual(len(re.findall(r"<a\b", hero_markup)), 0, "the updated hero is deliberately CTA-free")
        self.assertNotIn("sh-primary-link", hero_markup)

    def test_journey_has_four_articles_and_the_expected_learning_sequence(self):
        panels = [panel(self.main, number) for number in range(1, 5)]
        self.assertIn("introduction-to-bioinformatics.html", panels[0])
        self.assertIn("command-line-part1.html", panels[1])
        self.assertIn("computer-data-fundamentals.html", panels[2])
        self.assertLess(panels[1].index("command-line-part1.html"), len(panels[1]))
        self.assertLess(self.main.index("command-line-part1.html"), self.main.index("computer-data-fundamentals.html"))
        self.assertIn('id="sh-language-choice"', panels[3])
        self.assertIn("tutorials/r-tidyverse-fundamentals.html", panels[3])
        self.assertIn("tutorials/python-fundamentals-bioinformatics.html", panels[3])
        self.assertNotIn("conda-mamba-part1.html", "".join(panels))
        self.assertIn("Bash on Linux, macOS, or Windows Subsystem for Linux (WSL)", self.main)

    def test_orbit_and_sidebar_have_matching_real_fragment_navigation(self):
        orbit_attrs = next(attrs for tag, attrs in self.facts.elements
                           if "sh-orbit" in attrs.get("class", "").split())
        self.assertIn("hidden", orbit_attrs, "the orbit container is revealed after enhancement")
        orbit_anchors = [attrs for tag, attrs in self.facts.elements
                         if tag == "a" and "sh-orbit-stop" in attrs.get("class", "").split()]
        self.assertEqual(len(orbit_anchors), 4)
        self.assertEqual([attrs.get("data-sh-step") for attrs in orbit_anchors], ["1", "2", "3", "4"])
        for step, attrs in enumerate(orbit_anchors, 1):
            with self.subTest(orbit_step=step):
                self.assertEqual(attrs.get("href"), f"#sh-step-{step}")
                self.assertNotIn("hidden", attrs)

        guide_match = re.search(r'<aside\b[^>]*class="[^"]*\bsh-guide\b[^"]*".*?</aside\s*>', self.main, re.S)
        self.assertIsNotNone(guide_match, "the page provides a guide sidebar")
        guide = Facts(guide_match.group())
        nav_list = next(attrs for tag, attrs in guide.elements
                        if tag == "ol" and "sh-step-nav" in attrs.get("class", "").split())
        self.assertTrue(nav_list)
        step_links = [attrs for tag, attrs in guide.elements if tag == "a" and attrs.get("data-sh-step")]
        self.assertEqual(len(step_links), 4)
        self.assertEqual([attrs.get("data-sh-step") for attrs in step_links], ["1", "2", "3", "4"])
        for step in range(1, 5):
            self.assertIn(f'href="#sh-step-{step}"', guide_match.group())
        buttons = [attrs for tag, attrs in guide.elements if tag == "button"]
        self.assertGreaterEqual(len(buttons), 2)
        labels = " ".join(attrs.get("aria-label", "") for attrs in buttons).lower()
        button_text = " ".join(guide.text).lower()
        self.assertTrue("prev" in labels + button_text or "previous" in labels + button_text)
        self.assertIn("next", labels + button_text)
        self.assertRegex(guide_match.group(), r'aria-live="polite"')

    def test_panels_are_available_without_javascript_and_script_enhances_navigation(self):
        for step in range(1, 5):
            markup = panel(self.main, step)
            self.assertNotRegex(markup.split(">", 1)[0], r"\bhidden(?:=|\s|>)")
        self.assertIn("data-sh-step", self.js)
        self.assertIn("hidden", self.js)
        self.assertIn("aria-current", self.js)
        self.assertRegex(self.js, r"(?s)(?:addEventListener|onclick)")

    def test_all_32_tutorial_destinations_and_manifest_anchors_are_preserved(self):
        old_links = {url for url in Facts(self.old_main).links if url.startswith("tutorials/")}
        new_links = {url for url in self.facts.links if url.startswith("tutorials/")}
        self.assertEqual(len(old_links), 32)
        self.assertEqual(new_links, old_links)
        targets = json.loads((ROOT / "tools/learning-paths.json").read_text(encoding="utf-8"))["start_targets"]
        for anchor in targets:
            with self.subTest(anchor=anchor):
                self.assertEqual(self.facts.ids.count(anchor), 1)
        self.assertEqual(len(self.facts.ids), len(set(self.facts.ids)))
        for link in self.facts.links:
            if link.startswith("tutorials/"):
                self.assertTrue((ROOT / link.split("#", 1)[0]).is_file(), link)

    def test_six_native_disclosures_stay_collapsed_with_cautions_and_optional_setup(self):
        details = [attrs for tag, attrs in self.facts.elements if tag == "details"]
        self.assertEqual(len(details), 6)
        self.assertTrue(all("open" not in attrs for attrs in details))
        self.assertEqual(sum(tag == "summary" for tag, _ in self.facts.elements), 6)
        text = " ".join(self.facts.text).lower()
        for phrase in (
            "not a required course", "not a bulk RNA-seq tutorial", "replicated single-cell samples",
            "not substitutes for basic QC", "authorized institutional access",
            "not standardized on one Python or R version", "zero-byte placeholder files are not sequencing data",
        ):
            with self.subTest(caution=phrase):
                self.assertIn(phrase.lower(), text)
        optional = re.search(r'<details\b[^>]*id="sh-optional-tools".*?</details\s*>', self.main, re.S)
        self.assertIsNotNone(optional)
        self.assertIn("tutorials/conda-mamba-part1.html", optional.group())
        self.assertIn("choose one language", text)
        self.assertIn("learn one for now", text)
        self.assertIn("tutorials/statistics-for-bioinformatics.html", self.main)
        self.assertIn("tutorials/experimental-design-batch-effects.html", self.main)

    def test_visible_page_copy_remains_concise_without_em_dash_or_completion_promise(self):
        text = " ".join(self.facts.text)
        self.assertLess(len(unescape(text).split()), 650)
        self.assertNotIn("\u2014", unescape(self.main))
        self.assertNotRegex(text.lower(), r"\b(?:completed|completion|percent complete)\b")


if __name__ == "__main__":
    unittest.main()
