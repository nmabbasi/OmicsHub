"""Regression tests for the Option 1A laptop homepage redesign and site-wide icon footer consistency."""
from pathlib import Path
import re
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ROOT_PAGES = (
    "index.html", "start-here.html", "tutorials.html", "about.html",
    "contact.html", "services.html", "success.html", "404.html",
)


def canonical_pages() -> list[Path]:
    return [
        *(ROOT / name for name in ROOT_PAGES),
        *sorted((ROOT / "pages").glob("*.html")),
        *sorted((ROOT / "tutorials").glob("*.html")),
    ]


class HomepageAndFooterConsistencyTests(unittest.TestCase):
    def test_homepage_uses_option1a_laptop_keyboard_and_valid_category_filters(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        tutorials = (ROOT / "tutorials.html").read_text(encoding="utf-8")
        valid_categories = set(re.findall(r'data-category="([^"]+)"', tutorials))
        valid_categories = {c.replace("&amp;", "&") for c in valid_categories}

        self.assertIn('class="oh-laptop-lid"', home)
        self.assertIn('class="oh-laptop-base-svg"', home)
        self.assertIn('id="search-input"', home)
        self.assertIn('id="search-clear"', home)
        self.assertIn('id="search-suggestions"', home)
        self.assertIn("Explore Tutorials →", home)
        self.assertIn("Start Here Path →", home)
        self.assertIn("Browse all tutorials →", home)
        self.assertNotIn("\u2014", home)

        # Ensure zero white gap above homepage footer
        self.assertIn('<footer class="bg-gray-900 text-white">', home)
        self.assertNotIn('<footer class="bg-gray-900 text-white mt-16">', home)

        # Ensure all 4 Explore-the-library topic links target real tutorials.html categories
        topic_links = re.findall(r'class="v1-tcard"\s+href="([^"]+)"', home)
        self.assertEqual(len(topic_links), 4)
        for href in topic_links:
            parsed = urlsplit(href)
            self.assertEqual(parsed.path, "tutorials.html")
            cat = parse_qs(parsed.query).get("category", [None])[0]
            self.assertIn(cat, valid_categories, f"Invalid category filter in homepage card: {href}")

    def test_all_36_canonical_pages_share_consistent_footer_with_social_icons(self):
        pages = canonical_pages()
        self.assertEqual(len(pages), 36)
        for page in pages:
            rel = page.relative_to(ROOT).as_posix()
            text = page.read_text(encoding="utf-8")
            with self.subTest(page=rel):
                match = re.search(r"<footer\b.*?</footer>", text, re.S)
                self.assertIsNotNone(match, f"{rel} missing <footer>")
                footer = match.group(0)
                # Brand mark & heading structure
                self.assertIn("The Omics Hub", footer)
                self.assertIn("footer-grid", footer)
                self.assertRegex(footer, r"<h2\b[^>]*>Explore</h2>")
                self.assertRegex(footer, r"<h2\b[^>]*>Policies</h2>")
                # Core links including Start Here and Subscribe
                for label in ("Home", "Start Here", "Tutorials", "About", "Contact",
                              "Privacy Policy", "Terms of Service", "Disclaimer", "Cookie Policy",
                              "Subscribe &amp; Get Cheat Sheet"):
                    self.assertIn(label, footer, f"{rel} footer missing {label}")
                # LinkedIn, ORCID, and GitHub SVG icons
                for url, title in (
                    ("https://www.linkedin.com/in/nmabbasi", 'title="LinkedIn"'),
                    ("https://orcid.org/0009-0005-0083-1984", 'title="ORCID"'),
                    ("https://github.com/nmabbasi", 'title="GitHub"'),
                ):
                    self.assertIn(url, footer, f"{rel} footer missing {url}")
                    self.assertIn(title, footer, f"{rel} footer missing {title}")
                self.assertEqual(footer.count('<svg class="w-6 h-6"'), 3, f"{rel} footer should have 3 social SVG icons")
                self.assertIn("© 2026 The Omics Hub. All rights reserved.", footer)
                self.assertIn("cookie-consent.js", text, f"{rel} missing cookie-consent.js for footer consent controls")

    def test_shared_stylesheet_unifies_footer_consent_and_social_icon_polish(self):
        css = (ROOT / "style.css").read_text(encoding="utf-8")
        home_css = (ROOT / "home-page.min.css").read_text(encoding="utf-8")
        self.assertIn("footer .subscribe-community-button { margin-left: auto; }", css)
        self.assertIn('footer #advertising-consent-status[data-consent-state="ready"]', css)
        self.assertIn('footer #advertising-consent-status[data-consent-state="error"]', css)
        self.assertIn("data-consent-state=ready", home_css)
        self.assertIn("data-consent-state=error", home_css)
        self.assertIn("cookie-preferences-link:before", home_css)


if __name__ == "__main__":
    unittest.main()
