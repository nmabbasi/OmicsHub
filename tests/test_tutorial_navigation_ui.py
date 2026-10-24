"""UI contract tests for the generated tutorial navigation.

Run: python3 -m unittest tests/test_tutorial_navigation_ui.py
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
import generate_learning_paths as generator  # noqa: E402
from sitewide_top_baseline import normalize_sitewide_top  # noqa: E402


class Anchors(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, str | None]] = []
        self.feed(source)

    def handle_starttag(self, tag: str, attrs):
        if tag == "a":
            self.items.append(dict(attrs))


class TutorialNavigationMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.facts = generator.load_site(ROOT)

    def test_toolbar_keeps_three_native_links_and_navigation_hooks(self):
        for key, item in self.manifest["tutorials"].items():
            markup = generator.render_toolbar(key, item, self.manifest, self.facts)
            links = Anchors(markup).items
            with self.subTest(page=key):
                self.assertEqual(len(links), 3)
                self.assertTrue(all(link.get("href") for link in links))
                self.assertTrue(all("onclick" not in link for link in links))
                self.assertIn('class="reader-toolbar"', markup)
                self.assertIn('aria-label="Learning path navigation"', markup)
                self.assertIn('data-catalogue-return="" href="../tutorials.html"', markup)
                self.assertIn("reader-toolbar__previous", markup)
                self.assertIn("reader-toolbar__library", markup)
                self.assertIn("reader-toolbar__next", markup)
                self.assertIn("aria-hidden=\"true\" focusable=\"false\"", markup)
                if item.get("previous") and not item["previous"].startswith("@"):
                    self.assertEqual(links[0].get("rel"), "prev")
                if len(item["next"]) > 1:
                    self.assertEqual(links[-1]["href"], "#reader-course-navigation")
                elif item["next"]:
                    self.assertEqual(links[-1]["rel"], "next")
                    self.assertEqual(links[-1]["href"], generator.href_for(item["next"][0]["target"]))

    def test_continuation_cards_render_every_manifest_option_as_a_suggested_branch(self):
        branch_keys = [key for key, item in self.manifest["tutorials"].items()
                       if len(item["next"]) > 1]
        self.assertTrue(branch_keys, "manifest should exercise genuine multiple-choice branches")
        for key in branch_keys:
            item = self.manifest["tutorials"][key]
            markup = generator.render_continuation(key, item, self.manifest, self.facts)
            links = Anchors(markup).items
            suggested = [link for link in links
                         if "reader-path-card--suggested" in (link.get("class") or "")]
            with self.subTest(page=key):
                expected = [generator.href_for(edge["target"]) for edge in item["next"]]
                actual = [link["href"] for link in suggested]
                self.assertEqual(actual, expected)
                self.assertEqual([link["rel"] for link in suggested], ["next"] * len(expected))
                self.assertEqual(markup.count('class="reader-path-card__reason"'), len(expected))
                self.assertEqual(markup.count('class="reader-path-card__arrow"'), len(links))
                self.assertEqual(markup.count('class="reader-path-card reader-path-card--suggested"'), len(expected))
                self.assertIn('id="reader-course-navigation"', markup)
                self.assertIn("not a completion tracker", markup)
                self.assertIn('data-catalogue-return="" href="../tutorials.html"', markup)
                self.assertIn("reader-path-card--previous", markup)
                self.assertIn("reader-path-card--library", markup)
                self.assertLess(markup.index('class="reader-sequence-grid'),
                                markup.index('class="reader-sequence-utilities"'))
                self.assertLess(markup.index('reader-path-card--suggested'),
                                markup.index('class="reader-sequence-utilities"'))
                self.assertLess(markup.index('class="reader-sequence-utilities"'),
                                markup.index('reader-path-card--previous'))

    def test_editorial_heading_and_compact_footer_preserve_route_context(self):
        for key, item in self.manifest['tutorials'].items():
            markup = generator.render_continuation(key, item, self.manifest, self.facts)
            with self.subTest(page=key):
                self.assertIn('<h2>Keep exploring</h2>', markup)
                self.assertIn('class="reader-sequence-route-label">Learning route</span>', markup)
                self.assertIn('class="reader-sequence-footer"', markup)
                self.assertIn('class="reader-sequence-note"', markup)
                self.assertLess(markup.index('class="reader-sequence-utilities"'), markup.index('class="reader-sequence-note"'))
                self.assertNotIn('completed', markup.lower())

    def test_single_path_keeps_exact_previous_and_next_targets_and_relations(self):
        key = next(k for k, v in self.manifest["tutorials"].items()
                   if v.get("previous") and not v["previous"].startswith("@") and v["next"])
        item = self.manifest["tutorials"][key]
        markup = generator.render_continuation(key, item, self.manifest, self.facts)
        links = Anchors(markup).items
        by_href = {link["href"]: link for link in links}
        previous_href = generator.href_for(item["previous"])
        next_href = generator.href_for(item["next"][0]["target"])
        self.assertEqual(by_href[previous_href]["rel"], "prev")
        self.assertEqual(by_href[next_href]["rel"], "next")
        self.assertIn("Previous prerequisite", markup)
        self.assertIn(item["next"][0]["reason"], markup)
        self.assertNotIn("Tutorial 1 of 58", markup)

    def test_titles_and_reasons_are_escaped_inside_new_markup(self):
        manifest = {**self.manifest, "tutorials": dict(self.manifest["tutorials"])}
        item = dict(manifest["tutorials"]["computer-data-fundamentals"])
        item["next"] = [{**item["next"][0], "label": '<script>alert("x")</script>',
                          "reason": '<img src=x onerror="x">'}]
        manifest["tutorials"]["computer-data-fundamentals"] = item
        rendered = generator.render_continuation("computer-data-fundamentals", item,
                                                 manifest, self.facts)
        self.assertIn('&lt;script&gt;alert("x")&lt;/script&gt;', rendered)
        self.assertIn('&lt;img src=x onerror="x"&gt;', rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)


class TutorialNavigationStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "tutorial-navigation.css").read_text(encoding="utf-8")

    def test_standalone_css_has_responsive_mobile_layouts_and_touch_targets(self):
        self.assertIn("@media (max-width: 42rem)", self.css)
        self.assertIn("@media (max-width: 22rem)", self.css)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", self.css)
        self.assertIn("min-height: 3.25rem", self.css)
        self.assertIn("min-height: 4rem", self.css)
        self.assertIn("overflow-wrap: anywhere", self.css)

    def test_visible_focus_and_reduced_motion_are_explicit(self):
        self.assertIn(":focus-visible", self.css)
        self.assertIn("outline: 3px solid", self.css)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.css)
        self.assertIn("transition: none", self.css)

    def test_navigation_typography_is_left_aligned_and_hierarchy_is_styled(self):
        self.assertIn(".reader-path-card--suggested", self.css)
        self.assertIn(".reader-sequence .reader-sequence-utilities a.reader-path-card", self.css)
        self.assertIn(".reader-sequence-utilities .reader-path-card__eyebrow", self.css)
        self.assertIn("text-align: left", self.css)
        self.assertNotIn("text-align: center", self.css)

    def test_legacy_layout_overrides_are_reset_with_scoped_specificity(self):
        self.assertIn(".reader-sequence .reader-path-card", self.css)
        self.assertIn("flex-direction: row", self.css)
        self.assertIn(".reader-toolbar.reader-toolbar a.reader-toolbar__library", self.css)
        self.assertIn(".reader-toolbar.reader-toolbar a.reader-toolbar__next", self.css)
        self.assertIn(".reader-sequence-utilities", self.css)

    def test_no_oversized_suggested_rows_and_native_top_control_is_progressively_floating(self):
        self.assertNotIn('min-height: 9.5rem', self.css)
        self.assertIn('.reader-sequence-footer', self.css)
        self.assertIn('.reader-sequence-route-label', self.css)
        script = normalize_sitewide_top(
            'subscribe-fab.js', (ROOT / 'subscribe-fab.js').read_text()
        )
        self.assertIn("existing.matches('a[href=\"#tutorial-title\"], a[href=\"#sh-hero-title\"]')", script)
        self.assertIn('navigationFooter.appendChild(tools)', script)
        self.assertIn("tools.classList.add('is-floating')", script)
        self.assertIn('window.scrollY < 240', script)
        self.assertIn('control !== existing', script)
        circle = (ROOT / 'back-to-top.css').read_text()
        self.assertIn('border-radius: 50%', circle)
        self.assertIn('position: fixed', circle)
        self.assertIn('var(--reader-banner-space, 0px)', circle)
        self.assertIn('@media (prefers-reduced-motion: reduce)', circle)


if __name__ == "__main__":
    unittest.main()
