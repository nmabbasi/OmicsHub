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
        self.assertIn(".o3-spine { padding: 0; scroll-margin-top: 5.5rem; }", css)
        self.assertIn(".o3-stepper {", css)
        self.assertIn(".o3-pillars-sec { padding: 0.25rem 0 4rem; scroll-margin-top: 5rem; }", css)
        self.assertIn("line-height: 1.15;", css)

    def test_homepage_laptop_hero_fills_initial_viewport_cleanly(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("min-height: calc(100svh - 73px);", html)
        self.assertIn("align-items: center;", html)
        self.assertIn("@media (min-width: 961px) and (max-height: 780px)", html)
        self.assertIn(".oh-laptop-hero::before {", html)
        self.assertIn("width: 87.0000%;", html)
        self.assertIn('src="images/hero-laptop-keyboard.svg"', html)
        self.assertNotIn('<svg aria-hidden="true" class="oh-laptop-base-svg"', html)
        svg = (ROOT / "images/hero-laptop-keyboard.svg").read_text(encoding="utf-8")
        self.assertIn('viewBox="0 0 1200 268"', svg)
        self.assertNotIn("\u2014", svg)

    def test_item6_amber_callout_border_and_code_header_mobile_dot_gap(self):
        style_css = (ROOT / "style.css").read_text(encoding="utf-8")
        reader_css = (ROOT / "tutorial-reader.css").read_text(encoding="utf-8")
        self.assertIn(".border-amber-300 { border-color: #fcd34d !important; }", style_css)
        self.assertNotIn(".code-block-toolbar::before", reader_css)
        for token in (
            ".code-block-language",
            ".code-wrap-button",
            ".code-line-gutter",
            ".is-output-frame",
            ".code-expand-button",
        ):
            self.assertIn(token, reader_css, f"tutorial-reader.css missing {token}")

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

    def test_all_39_public_pages_have_zero_em_dashes(self):
        root_pages = (
            "index.html", "start-here.html", "tutorials.html", "about.html",
            "contact.html", "services.html", "success.html", "404.html",
        )
        all_pages = [
            *(ROOT / name for name in root_pages),
            *sorted((ROOT / "pages").glob("*.html")),
            *sorted((ROOT / "tutorials").glob("*.html")),
        ]
        self.assertEqual(len(all_pages), 39)
        for page in all_pages:
            rel = page.relative_to(ROOT).as_posix()
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", unescape(text), f"em-dash found in {rel}")

    def test_removed_thesis_pdf_figures_and_examples_are_absent(self):
        removed_paths = (
            "images/figures/trajectory-1.webp",
            "images/figures/dataviz-2.webp",
            "tutorials/examples/Combined_LIANA_Analysis_Conserved_Specific_Signaling.html",
            "tutorials/examples/Benchmark_cell_Prediction_Methods_5_012_2025_on_Clusters_v2.html",
            "tutorials/examples/TCR_Analysis_v2.html",
            "tutorials/examples/CyteTypeR_Annotation_using_AI_Finalized.html",
            "tutorials/examples/inferCNV_analysis.html",
            "tutorials/examples/Integration_by_CCA_Harmony.html",
            "tutorials/examples/mLLM_Annotatin_of_all_clusters.html",
            "tutorials/examples/scASSIST_AI_METHOD.html",
            "tutorials/examples/Trajectory_inference_using_Slingshot.html",
            "tutorials/examples/WNN_analysis_of_CITE_seq_RNA_ADT.html",
        )
        for rel in removed_paths:
            self.assertFalse((ROOT / rel).exists(), f"Thesis PDF figure asset must stay removed: {rel}")
        downstream = (ROOT / "tutorials/scrna-seq-downstream-analysis.html").read_text(encoding="utf-8")
        self.assertNotIn("Combined_LIANA_Analysis_Conserved_Specific_Signaling.html", downstream)
        self.assertNotIn("TCR_Analysis_v2.html", downstream)
        self.assertNotIn("examples/WNN_analysis_of_CITE_seq_RNA_ADT.html", downstream)
        self.assertNotIn("examples/inferCNV_analysis.html", downstream)
        self.assertIn('href="cite-seq-wnn-multiomics.html"', downstream)
        self.assertIn('href="infercnv-copy-number-variation.html"', downstream)

    def test_featured_and_tutorial_cards_have_elevated_shadow_and_hover_popout(self):
        home_html = (ROOT / "index.html").read_text(encoding="utf-8")
        cat_css = (ROOT / "home-catalogue.css").read_text(encoding="utf-8")
        for token in (
            "transform: translateY(-8px) scale(1.018);",
            "border-color: #38BDF8;",
            "0 22px 44px -10px rgba(11, 39, 65, 0.28)",
            "transform: scale(1.045);",
        ):
            self.assertIn(token, home_html, f"index.html missing {token}")
            self.assertIn(token, cat_css, f"home-catalogue.css missing {token}")

    def test_all_27_tutorials_have_figures_and_valid_svgs(self):
        tuts = sorted((ROOT / "tutorials").glob("*.html"))
        self.assertEqual(len(tuts), 27)
        for page in tuts:
            html = page.read_text(encoding="utf-8")
            article_m = re.search(r"<article\b[^>]*>(.*?)</article>", html, re.S)
            self.assertIsNotNone(article_m, page.name)
            article = article_m.group(1)
            self.assertIn("<figure", article, f"Missing figure in {page.name}")
            for svg_rel in re.findall(r'src="\.\./(images/tutorial-figures/[^"]+\.svg)"', article):
                svg_path = ROOT / svg_rel
                self.assertTrue(svg_path.is_file(), f"Missing SVG {svg_rel}")
                svg_txt = svg_path.read_text(encoding="utf-8").strip()
                self.assertTrue(svg_txt.startswith("<svg"), svg_rel)
                self.assertTrue(svg_txt.endswith("</svg>"), svg_rel)
                self.assertNotIn("\u2014", svg_txt, f"em-dash in {svg_rel}")

    def test_reader_ux_and_code_display_contracts(self):
        reader_css = (ROOT / "tutorial-reader.css").read_text(encoding="utf-8")
        copy_js = (ROOT / "copy-code.js").read_text(encoding="utf-8")
        self.assertNotIn("position: fixed", reader_css)
        for token in (
            "code-wrap-button",
            "code-line-gutter",
            "code-expand-button",
            "tutorial-toc",
            "tutorial-reading-progress",
            "tutorial-meta-strip",
            "tutorial-lightbox",
        ):
            self.assertIn(token, reader_css, f"tutorial-reader.css missing {token}")
            self.assertIn(token, copy_js, f"copy-code.js missing {token}")

    def test_tutorials_hero_shows_all_active_format_and_topic_counts(self):
        catalogue = (ROOT / "tutorials.html").read_text(encoding="utf-8")
        for token in (
            "<strong>12</strong> Hands-on labs",
            "<strong>7</strong> Conceptual guides",
            "<strong>7</strong> Templates",
            "<strong>1</strong> Reference",
            "<strong>10</strong> Topics",
        ):
            self.assertIn(token, catalogue)

    def test_live_ux_friction_polish_contracts(self):
        cat_css = (ROOT / "home-catalogue.css").read_text(encoding="utf-8")
        self.assertRegex(
            cat_css,
            re.compile(r"@media\s*\(max-width:\s*760px\).*?#tutorials-page\s+\.hc-quick-pills\s*\{[^}]*flex-wrap:\s*wrap;", re.S),
            msg="Mobile quick pills should wrap cleanly without hidden horizontal clipping",
        )

        code_tabs_js = (ROOT / "code-tabs.js").read_text(encoding="utf-8")
        reader_css = (ROOT / "tutorial-reader.css").read_text(encoding="utf-8")
        self.assertIn("code-tab-heading-sr", code_tabs_js)
        self.assertIn("code-tab-heading-sr", reader_css)
        self.assertIn("word-break: normal;\n  overflow-wrap: normal;", reader_css)

        copy_js = (ROOT / "copy-code.js").read_text(encoding="utf-8")
        self.assertIn("'advanced-template': 'Advanced template'", copy_js)
        self.assertIn("'reference': 'Reference'", copy_js)

        micromamba = (ROOT / "tutorials/conda-mamba-part1.html").read_text(encoding="utf-8")
        self.assertIn("<span>2026-08-30</span>", micromamba)
        self.assertIn("<span>Updated 20 November 2026</span>", micromamba)
        self.assertLess(
            micromamba.index('class="lesson-lead"'),
            micromamba.index('class="lesson-summary tutorial-learning-contract"'),
        )

        home_html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('alt="Micromamba Environments for Bioinformatics"', home_html)

        for page in sorted((ROOT / "tutorials").glob("*.html")):
            html = page.read_text(encoding="utf-8")
            for figure in re.findall(r"<figure\b[^>]*>.*?</figure>", html, re.S):
                for img in re.findall(r'<img\b[^>]*loading="lazy"[^>]*>', figure):
                    self.assertRegex(img, r'\bwidth="\d+"', page.name)
                    self.assertRegex(img, r'\bheight="\d+"', page.name)
                    self.assertIn("aspect-ratio:", img, page.name)


if __name__ == "__main__":
    unittest.main()
