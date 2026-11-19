"""Regression tests for the 7-item visual design polish audit."""
from html import unescape
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VisualDesignPolishTests(unittest.TestCase):
    def test_item1_tutorial_tables_wrap_inline_code_and_pin_mobile_captions(self):
        css = (ROOT / "tutorial-library.css").read_text(encoding="utf-8")
        self.assertIn(".lesson-page .lesson-table-wrap :not(pre) > code", css)
        self.assertIn("word-break: normal; overflow-wrap: anywhere;", css)
        self.assertIn("position: sticky;", css)
        self.assertIn("max-width: calc(100vw - 3rem);", css)
        self.assertIn(".lesson-page .lesson-table-wrap caption", css)

    def test_item2_404_page_has_canonical_header_and_equal_height_actions(self):
        html = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertNotIn("adsbygoogle.js", html)
        for token in (
            'id="nav-desktop-starthere"',
            'id="nav-mobile-starthere"',
            'href="/start-here.html"',
            'href="/tutorials.html"',
            'href="/about.html"',
            'href="/contact.html"',
            'aria-label="LinkedIn Profile"',
            'aria-label="ORCID Profile"',
            'aria-label="GitHub Profile"',
            ".error-actions",
            "min-height: 46px;",
        ):
            self.assertIn(token, html, f"404.html missing {token}")

    def test_item2_success_page_has_no_wrong_active_tab_or_typo_and_mobile_button_polish(self):
        html = (ROOT / "success.html").read_text(encoding="utf-8")
        self.assertNotIn("adsbygoogle.js", html)
        self.assertNotIn('aria-current="page"', html)
        self.assertNotIn("the The", html)
        self.assertIn('<h2 class="text-lg font-bold text-gray-900 mb-2">Command Line &amp; Bioinformatics Cheat Sheet</h2>', html)
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn('id="success-page-responsive-styles"', html)
        self.assertIn(".success-download-btn", html)

    def test_item3_mobile_search_cookie_modal_and_mobile_menu_polish(self):
        js = (ROOT / "script.js").read_text(encoding="utf-8")
        mob_js = (ROOT / "mobile-navigation.js").read_text(encoding="utf-8")
        css = (ROOT / "style.css").read_text(encoding="utf-8")
        home_css = (ROOT / "home-page.min.css").read_text(encoding="utf-8")
        self.assertIn("oh-search-sublabel", js)
        self.assertIn("cookie-preferences-heading", js)
        self.assertIn("cookie-preferences-heading", mob_js)
        for token in (
            ".oh-search-sublabel",
            ".cookie-preferences-dialog h2:focus { outline: none; }",
            ".cookie-preferences-dialog a:focus:not(:focus-visible)",
            "@media (max-width: 520px)",
            "order: -1;",
            "#mobile-menu a {",
            "gap: .45rem;",
        ):
            self.assertIn(token, css, f"style.css missing {token}")
        for token in (
            "oh-search-sublabel",
            "cookie-preferences-dialog h2:focus",
            "max-width:520px",
            "gap:.45rem",
            "aria-current=page",
        ):
            self.assertIn(token, home_css, f"home-page.min.css missing {token}")

    def test_item4_tutorials_catalogue_badges_stack_cleanly(self):
        css = (ROOT / "home-catalogue.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"#tutorials-page\s+\.hc-card-meta\s*\{[^}]*flex-direction:\s*column;[^}]*align-items:\s*flex-start;",
        )

    def test_item5_start_here_cta_alignment_and_mobile_pills(self):
        css = (ROOT / "start-here.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.o3-fcard\s+a\s*\{[^}]*margin-top:\s*auto;")
        self.assertIn(".o3-hpc-btns { width: 100%; flex-direction: column; }", css)

    def test_item6_amber_callout_border_and_code_header_mobile_dot_gap(self):
        style_css = (ROOT / "style.css").read_text(encoding="utf-8")
        reader_css = (ROOT / "tutorial-reader.css").read_text(encoding="utf-8")
        self.assertIn(".border-amber-300 { border-color: #fcd34d !important; }", style_css)
        self.assertIn("padding: .3rem .65rem .3rem 4.55rem;", reader_css)
        self.assertIn("padding-left: 4.55rem;", reader_css)

    def test_item7_cookie_contact_about_and_services_polish(self):
        cookie_html = (ROOT / "pages/cookie.html").read_text(encoding="utf-8")
        contact_html = (ROOT / "contact.html").read_text(encoding="utf-8")
        about_html = (ROOT / "about.html").read_text(encoding="utf-8")
        services_html = (ROOT / "services.html").read_text(encoding="utf-8")
        self.assertIn(".legal-content code {", cookie_html)
        self.assertIn("word-break: normal;", cookie_html)
        self.assertIn('id="contact-form-polish"', contact_html)
        self.assertIn("#topic-select", contact_html)
        self.assertIn("#contact-attachment::file-selector-button", contact_html)
        self.assertIn('style="padding-bottom:0;"', contact_html)
        self.assertIn('style="padding-top:2rem;padding-bottom:0;"', about_html)
        self.assertIn('style="padding-bottom:0;"', services_html)

    def test_all_70_public_pages_have_zero_em_dashes(self):
        root_pages = (
            "index.html", "start-here.html", "tutorials.html", "about.html",
            "contact.html", "services.html", "success.html", "404.html",
        )
        all_pages = [
            *(ROOT / name for name in root_pages),
            *sorted((ROOT / "pages").glob("*.html")),
            *sorted((ROOT / "tutorials").glob("*.html")),
        ]
        self.assertEqual(len(all_pages), 70)
        for page in all_pages:
            rel = page.relative_to(ROOT).as_posix()
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", unescape(text), f"em-dash found in {rel}")


if __name__ == "__main__":
    unittest.main()
