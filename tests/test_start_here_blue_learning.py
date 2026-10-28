"""Regression contracts for the restored pre-circular, image-led Start Here page."""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

from reader_text_colour_baseline import (
    READER_TEXT_ASSET_PATHS, normalize_reader_text, restore_reader_text_asset,
)
from r_first_revision_baseline import R_FIRST_ASSET_PATHS, restore_r_first_asset
from latest_review_baseline import restore_latest_review_asset
from start_here_desktop_baseline import DESKTOP_CSS_HREF, restore_start_here_desktop_asset
from coffee_removal_baseline import restore_coffee_removal_text
from startup_performance_baseline import ASSET_PATHS as STARTUP_ASSET_PATHS, restore_startup_performance_asset
from startup_generated_asset_baseline import restore_startup_generated_asset

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = "a4b6ead8251e0a3abcb748061a40155ae9523a82"
PR_BASE = "e846ce3fb6053ed611dc87fc62748865499913d0"
PUBLISHED = "45d660c5f53a0f4d8c2736057e2ab54fe7b8e718"
EXPECTED_IMAGES = {
    "images/sh-three-laptop-learner-banner-with-copy.webp",
    "images/sh-route-single-cell-laptop-v3.webp",
    "images/sh-route-genomics-laptop-v3.webp",
    "images/sh-route-microbial-laptop-v3.webp",
    "images/sh-route-evolution-laptop-v3.webp",
}


def git_bytes(revision, path):
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout if result.returncode == 0 else None


def pinned_paths():
    return subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", PUBLISHED], cwd=ROOT, text=True
    ).splitlines()


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


def curriculum_region(markup):
    start = markup.index("<!-- ── CURRICULUM ROADMAP & PREREQUISITES ── -->")
    end = markup.index("<!-- ── CATALOGUE ── -->", start)
    return markup[start:end]


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class StartHereImageLedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "start-here.html").read_text(encoding="utf-8")
        cls.current_main = main(cls.source)
        cls.css = (ROOT / "start-here.css").read_bytes()
        cls.historical = git_bytes(HISTORICAL, "start-here.html").decode("utf-8")
        cls.historical_main = main(cls.historical)
        cls.base = git_bytes(PR_BASE, "start-here.html").decode("utf-8")

    def test_only_the_reviewed_start_here_design_changes_in_the_current_page_shell(self):
        expected = self.base.replace(main(self.base), self.historical_main, 1)
        expected = expected.replace(
            curriculum_region(self.historical_main),
            curriculum_region(self.current_main),
            1,
        )
        old_css = re.findall(r'<link\b[^>]*href="(start-here\.css\?v=[^"]+)"[^>]*>', expected)
        self.assertEqual(len(old_css), 1)
        expected = expected.replace(old_css[0], DESKTOP_CSS_HREF, 1)
        expected, removed = re.subn(
            r'<script\b[^>]*\bsrc="start-here\.js\?v=[^"]+"[^>]*></script>\s*',
            "", expected, count=1, flags=re.I,
        )
        self.assertEqual(removed, 1)
        self.assertEqual(restore_coffee_removal_text("start-here.html", self.source), expected)
        unchanged = self.current_main.replace(
            curriculum_region(self.current_main),
            curriculum_region(self.historical_main),
            1,
        )
        self.assertEqual(unchanged, self.historical_main)
        self.assertEqual(
            restore_start_here_desktop_asset("start-here.css", self.css),
            git_bytes(PR_BASE, "start-here.css"),
        )
        self.assertEqual(
            (ROOT / "start-here.js").read_bytes(),
            git_bytes(PR_BASE, "start-here.js"),
            "the existing script remains untouched but is no longer loaded by this page",
        )

    def test_original_banner_and_four_illustrated_route_cards_are_preserved(self):
        facts = Facts(self.current_main)
        images = [attrs for tag, attrs in facts.elements if tag == "img"]
        image_sources = {attrs.get("src") for attrs in images}
        self.assertEqual(image_sources, EXPECTED_IMAGES)
        self.assertEqual(len(images), 5)
        self.assertTrue(all(attrs.get("alt", "").strip() for attrs in images))
        for src in EXPECTED_IMAGES:
            with self.subTest(image=src):
                self.assertTrue((ROOT / src).is_file())

        cards = re.findall(
            r'<a\b(?=[^>]*\bclass="[^"]*\bsh-route-card\b)[^>]*>.*?</a\s*>',
            self.current_main, re.S | re.I,
        )
        self.assertEqual(len(cards), 4)
        card_images = set()
        for card in cards:
            href = re.search(r'\bhref="([^"]+)"', card)
            image = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', card)
            self.assertIsNotNone(href)
            self.assertIsNotNone(image)
            self.assertTrue((ROOT / href.group(1)).is_file())
            card_images.add(image.group(1))
        self.assertEqual(card_images, EXPECTED_IMAGES - {"images/sh-three-laptop-learner-banner-with-copy.webp"})

    def test_historical_learning_links_remain_valid_and_no_circular_path_is_loaded(self):
        facts = Facts(self.current_main)
        lesson_links = {href for href in facts.links if href.startswith("tutorials/")}
        self.assertEqual(len(lesson_links), 32)
        for href in lesson_links:
            with self.subTest(destination=href):
                self.assertTrue((ROOT / href.split("#", 1)[0]).is_file())
        self.assertEqual(sum("sh-step" in attrs.get("class", "").split()
                             for tag, attrs in facts.elements if tag == "a"), 4)
        self.assertNotIn("sh-orbit", self.current_main)
        self.assertNotIn("data-sh-step", self.current_main)
        self.assertNotRegex(self.source, r"start-here\.js\?v=")

    def test_home_tutorials_shared_styles_and_images_are_unchanged(self):
        for relative in ("index.html", "tutorials.html"):
            with self.subTest(path=relative):
                restored = normalize_reader_text(relative, (ROOT / relative).read_text()).encode()
                self.assertEqual(restored, git_bytes(PUBLISHED, relative))
        lessons = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(lessons), 58)
        for page in lessons:
            relative = page.relative_to(ROOT).as_posix()
            with self.subTest(path=relative):
                restored = normalize_reader_text(relative, page.read_text()).encode()
                self.assertEqual(restored, git_bytes(PUBLISHED, relative))
        protected = [
            path for path in pinned_paths()
            if (path.endswith((".css", ".js")) and path not in {"start-here.css", "start-here.js"})
            or path.startswith(("fonts/", "images/", "assets/")) or path == "ads.txt"
        ]
        for relative in protected:
            with self.subTest(path=relative):
                current = (ROOT / relative).read_bytes()
                if relative in STARTUP_ASSET_PATHS:
                    current = restore_startup_performance_asset(relative, current)
                current = restore_startup_generated_asset(relative, current, "reader-text")
                current = restore_latest_review_asset(relative, current)
                if relative in READER_TEXT_ASSET_PATHS:
                    current = restore_reader_text_asset(relative, current)
                elif relative in R_FIRST_ASSET_PATHS:
                    current = restore_r_first_asset(relative, current)
                self.assertEqual(current, git_bytes(PUBLISHED, relative))


if __name__ == "__main__":
    unittest.main()
