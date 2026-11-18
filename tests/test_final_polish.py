"""Contract checks for the Nov 18, 2026 final tutorial polish."""
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

from final_polish_baseline import normalize_final_polish, pinned_paths

ROOT = Path(__file__).resolve().parents[1]
TUTORIALS = sorted((ROOT / "tutorials").glob("*.html"))
LINKEDIN = "https://www.linkedin.com/in/nmabbasi"
SCHEMA = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
ARTICLE = re.compile(r"<article\b.*?</article>", re.S)
STRIP = re.compile(r"<(pre|code|script|style)\b.*?</\1>", re.S)
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def prose(text):
    article = ARTICLE.search(text).group(0)
    return re.sub(r"<[^>]+>", " ", STRIP.sub(" ", article))


class FinalPolishTests(unittest.TestCase):
    def test_no_raw_latex_or_markdown_in_tutorial_prose(self):
        latex = re.compile(r"\$[^$\n]{1,60}\$|\\(?:alpha|beta|Delta|pi|times|text|langle|rangle)\b")
        markdown = re.compile(r"`[^`\n]{1,80}`|\*\*[^*\n]+\*\*|(?<![*\w])\*[A-Za-z][^*\n]{0,30}[A-Za-z0-9]\*(?![*\w])")
        for page in TUTORIALS:
            with self.subTest(page=page.name):
                body = prose(page.read_text(encoding="utf-8"))
                self.assertIsNone(latex.search(body))
                self.assertIsNone(markdown.search(body))

    def test_alphafold_and_python_pages_render_symbols_as_html(self):
        alpha = (ROOT / "tutorials/protein-structure-design-alphafold.html").read_text(encoding="utf-8")
        self.assertIn("&alpha;<sub>2</sub>&beta;<sub>2</sub> heterotetramer", alpha)
        self.assertIn("&Delta;&Delta;<i>G</i>", alpha)
        self.assertIn("O<sub>2</sub>", alpha)
        python = (ROOT / "tutorials/python-fundamentals-bioinformatics.html").read_text(encoding="utf-8")
        self.assertIn("<i>O</i>(1) average time", python)
        self.assertIn("<i>k</i>-mers", python)

    def test_author_schema_and_dates_align_with_sitemap(self):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        lastmod = {u.findtext("s:loc", namespaces=NS): u.findtext("s:lastmod", namespaces=NS)
                   for u in root.findall("s:url", NS)}
        for page in TUTORIALS:
            with self.subTest(page=page.name):
                entity = json.loads(SCHEMA.search(page.read_text(encoding="utf-8")).group(1))
                self.assertEqual(entity["author"]["name"], "Nasir Mahmood Abbasi, PhD")
                self.assertIn(LINKEDIN, entity["author"]["sameAs"])
                self.assertIn("https://orcid.org/0009-0005-0083-1984", entity["author"]["sameAs"])
                url = f"https://theomicshub.com/tutorials/{page.name}"
                self.assertEqual(entity["dateModified"], lastmod[url])

    def test_every_tutorial_has_a_visible_author_card_and_no_services_link(self):
        active_services = re.compile(r'(?<!Hidden commercial navigation link: )<a [^>]*href="\.\./services\.html"[^>]*>Services</a>')
        for page in TUTORIALS:
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertRegex(text, r'Author: <a [^>]*href="\.\./about\.html"[^>]*>Nasir Mahmood Abbasi, PhD</a>')
                self.assertIsNone(active_services.search(text))

    def test_cursor_aider_page_no_longer_repeats_the_faulty_proposal(self):
        text = (ROOT / "tutorials/ai-coding-cursor-aider.html").read_text(encoding="utf-8")
        self.assertEqual(text.count("Deliberately faulty proposal:"), 1)
        self.assertNotIn("were not installed or run", text)

    def test_normalizer_restores_exact_parent_and_preserves_mutations(self):
        self.assertEqual(len(pinned_paths()), 58)
        for rel in pinned_paths():
            with self.subTest(page=rel):
                current = (ROOT / rel).read_text(encoding="utf-8")
                restored = normalize_final_polish(rel, current)
                self.assertNotEqual(restored, current)
                self.assertEqual(normalize_final_polish(rel, restored), restored)
                mutated = current + "<!-- unreviewed -->"
                self.assertEqual(normalize_final_polish(rel, mutated), mutated)


if __name__ == "__main__":
    unittest.main()
