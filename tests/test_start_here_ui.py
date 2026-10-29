"""Accessible navigation contracts for the learner-first Start Here page."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
PUBLISHED = "45d660c5f53a0f4d8c2736057e2ab54fe7b8e718"
MAIN = re.compile(r"<main\b[^>]*>.*?</main\s*>", re.S | re.I)


class Facts(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.elements, self.text = [], [], [], []
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


def original(revision, path):
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT).decode("utf-8")


def page_main(source):
    match = MAIN.search(source)
    if not match:
        raise AssertionError("Start Here page must contain a main element")
    return match.group()


def redesigned_region(source):
    start_marker = "<!-- ── FOUNDATION ── -->"
    end_marker = "</main>"
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


class StartHereJourneyUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.main = page_main(cls.source)
        cls.historical_main = page_main(original(HISTORICAL, "start-here.html"))
        cls.published_main = page_main(original(PUBLISHED, "start-here.html"))
        cls.facts = Facts(cls.main)

    def test_main_preserves_the_historical_page_shell_outside_redesigned_sections(self):
        current = self.main.replace(
            redesigned_region(self.main), redesigned_region(self.historical_main), 1
        )
        self.assertEqual(current, self.historical_main)
        self.assertIn("images/sh-three-laptop-learner-banner-with-copy.webp", self.main)
        self.assertEqual(sum(tag == "img" for tag, _ in self.facts.elements), 5)
        self.assertEqual(sum("sh-route-card" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "a"), 4)

    def test_setup_cards_and_tracks_keep_all_original_lesson_destinations(self):
        current_region = redesigned_region(self.main)
        historical_region = redesigned_region(self.historical_main)
        current_links = {url for url in Facts(current_region).links if url.startswith("tutorials/")}
        historical_links = {url for url in Facts(historical_region).links if url.startswith("tutorials/")}
        self.assertEqual(current_links, historical_links | {"tutorials/research-reporting-interpretation.html"})
        self.assertEqual(sum("sh-ready-card" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "article"), 3)
        self.assertEqual(sum("sh-ready-more" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "details"), 3)
        self.assertEqual(sum("sh-track-card" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "article"), 3)
        for phrase in ("Pseudobulk differential expression", "not bulk RNA-seq",
                       "not a single-cell route", "authorized access",
                       "zero-byte placeholders", "what it cannot establish"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), current_region.lower())

    def test_all_tutorial_destinations_and_manifest_anchors_are_preserved(self):
        published_links = {url for url in Facts(self.published_main).links if url.startswith("tutorials/")}
        current_links = {url for url in self.facts.links if url.startswith("tutorials/")}
        self.assertEqual(len(published_links), 32)
        self.assertEqual(current_links, published_links | {"tutorials/research-reporting-interpretation.html"})
        self.assertEqual(len(current_links), 33)
        targets = json.loads((ROOT / "tools/learning-paths.json").read_text(encoding="utf-8"))["start_targets"]
        for anchor in targets:
            with self.subTest(anchor=anchor):
                self.assertEqual(self.facts.ids.count(anchor), 1)
        self.assertEqual(len(self.facts.ids), len(set(self.facts.ids)))
        for link in self.facts.links:
            if link.startswith("tutorials/"):
                self.assertTrue((ROOT / link.split("#", 1)[0]).is_file(), link)

    def test_four_visual_routes_are_native_links_without_page_specific_javascript(self):
        cards = re.findall(
            r'<a\b(?=[^>]*\bclass="[^"]*\bsh-route-card\b)[^>]*>.*?</a\s*>',
            self.main, re.S | re.I,
        )
        self.assertEqual(len(cards), 4)
        for card in cards:
            href = re.search(r'\bhref="([^"]+)"', card)
            self.assertIsNotNone(href)
            self.assertTrue((ROOT / href.group(1)).is_file())
        self.assertEqual(sum("sh-step" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "a"), 4)
        self.assertNotRegex(self.source, r"start-here\.js\?v=")
        self.assertNotIn("sh-orbit", self.main)
        self.assertNotIn("data-sh-step", self.main)

    def test_foundation_language_choice_and_optional_hpc_sections_remain_available(self):
        required_ids = {
            "sh-foundation", "sh-language-choice", "sh-hpc", "sh-routes",
            "sh-curriculum", "sh-hpc-track", "sh-optional-tools",
        }
        self.assertTrue(required_ids.issubset(set(self.facts.ids)))
        self.assertIn("HPC is not required to begin", " ".join(self.facts.text))
        self.assertIn("Already comfortable with the basics?", " ".join(self.facts.text))
        self.assertEqual(sum(tag == "details" for tag, _ in self.facts.elements), 6)
        self.assertEqual(sum("sh-track-details" in attrs.get("class", "").split()
                             for tag, attrs in self.facts.elements if tag == "details"), 3)

    def test_page_copy_has_no_completion_claim_or_em_dash(self):
        text = " ".join(self.facts.text)
        self.assertNotIn("\u2014", self.main)
        self.assertNotRegex(text.lower(), r"\b(?:completed|completion|percent complete)\b")


if __name__ == "__main__":
    unittest.main()
