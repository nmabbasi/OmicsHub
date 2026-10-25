"""Static regression tests for long-form and Start Here text alignment."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def css_rule(css: str, selector: str) -> str:
    """Return a simple CSS rule body for an exact selector string."""
    clean_css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    match = re.search(re.escape(selector) + r"\s*\{([^{}]*)\}", clean_css)
    if not match:
        raise AssertionError(f"Missing CSS rule for {selector!r}")
    return match.group(1)


def declarations(rule: str) -> dict[str, str]:
    return {
        name.strip().lower(): value.strip().lower()
        for declaration in rule.split(";")
        if ":" in declaration
        for name, value in [declaration.split(":", 1)]
    }


class TextAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared_css = (ROOT / "style.css").read_text(encoding="utf-8")
        cls.start_here_css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        cls.tutorial_css = (ROOT / "tutorial-library.css").read_text(encoding="utf-8")

    def test_tutorial_paragraphs_and_lists_use_start_alignment_without_hyphenation(self):
        reading_rule = re.search(
            r"\.prose p\s*,\s*\.prose li\s*\{([^{}]*)\}",
            re.sub(r"/\*.*?\*/", "", self.shared_css, flags=re.DOTALL),
        )
        self.assertIsNotNone(reading_rule, "Expected a shared prose reading rule")
        props = declarations(reading_rule.group(1))
        self.assertEqual(props.get("text-align"), "start")
        self.assertEqual(props.get("hyphens"), "none")
        self.assertEqual(props.get("letter-spacing"), "normal")
        self.assertNotRegex(self.shared_css, r"text-align\s*:\s*justify\b")
        self.assertNotRegex(self.shared_css, r"text-justify\s*:")
        self.assertNotRegex(self.shared_css, r"hyphens\s*:\s*auto\b")

    def test_alignment_rule_covers_all_current_tutorial_articles(self):
        tutorial_pages = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(tutorial_pages), 58)
        for page in tutorial_pages:
            with self.subTest(page=page.name):
                self.assertRegex(
                    page.read_text(encoding="utf-8"),
                    r'class="[^\"]*\bprose\b',
                    "Tutorial should use the shared prose alignment scope",
                )

    def test_start_here_content_and_hero_remain_left_aligned(self):
        main_props = declarations(css_rule(self.start_here_css, "#main-content"))
        hero_props = declarations(css_rule(self.start_here_css, ".sh-hero"))
        # English document direction makes the default inline alignment left;
        # neither the content region nor the simplified hero may be centered.
        self.assertIn(main_props.get("text-align", "left"), {"left", "start"})
        self.assertIn(hero_props.get("text-align", "left"), {"left", "start"})
        # Only short circular-control labels may be centered, never reading copy.
        allowed_centered = {
            "#main-content .sh-orbit-stop",
            ".sh-enhanced .sh-orbit::after",
        }
        clean = re.sub(r"/\*.*?\*/", "", self.start_here_css, flags=re.DOTALL)
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", clean):
            if declarations(body).get("text-align") == "center":
                self.assertIn(selector.strip(), allowed_centered)

    def test_table_headers_remain_left_aligned_and_code_wrapping_stays_specialized(self):
        self.assertEqual(declarations(css_rule(self.shared_css, ".prose th")).get("text-align"), "left")
        pre_rule = declarations(css_rule(self.shared_css, "pre code"))
        self.assertNotIn("text-align", pre_rule)
        self.assertIn("overflow-x: auto", self.tutorial_css)
        self.assertIn(".lesson-page pre code", self.tutorial_css)
        self.assertIn(".lesson-page .lesson-table-wrap :is(th,td)", self.tutorial_css)


if __name__ == "__main__":
    unittest.main()
