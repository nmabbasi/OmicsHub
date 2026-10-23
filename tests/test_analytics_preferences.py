#!/usr/bin/env python3
"""Regression checks for analytics preferences in tutorial pages.

Run with: python3 -m unittest discover -s tests -p 'test_*.py'
Uses only the Python standard library; does not execute page scripts.
"""
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import unittest

from reviewed_tutorial_baseline import (
    APPROVED_MAIN,
    normalize_learner_revision,
    normalize_reviewed_content,
    strip_cookie_banner,
)

ROOT = Path(__file__).resolve().parents[1]
TUTORIALS = ROOT / "tutorials"
BASELINE = "9782b635269171240c65abb942bd9bdf400e03d0"
COOKIE_CONSENT_BASELINE = "65e1c470355e1f8ba8a30faba7167e1bf2e8e081"
UPDATED_PAGES = {
    "advanced-ai-orchestration-bioinformatics.html",
    "ai-prompt-engineering-seurat.html",
    "deterministic-retrieval-gget-ai.html",
    "mcp-zotero.html",
    "notebooklm-research-brain.html",
    "protein-structure-design-alphafold.html",
    "single-cell-foundation-models.html",
}
BANNER_BLOCK = re.compile(
    r"\n[ \t]*<!-- Cookie Consent Banner -->.*?<!-- /Cookie Consent Banner -->",
    re.S,
)


class PageParser(HTMLParser):
    """Collect ids, script tags, banner controls, and relevant footer markup."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.scripts = []
        self.banner_depth = 0
        self.banner_count = 0
        self.banner_buttons = []
        self.banner_links = []
        self.banner_close_position = None
        self.body_close_position = None
        self.in_footer = False
        self.footer_depth = 0
        self.footer_parts = []
        self.raw = ""

    def feed(self, data):
        self.raw = data
        super().feed(data)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script":
            self.scripts.append(attrs)
        if attrs.get("id") == "cookie-consent-banner":
            self.banner_count += 1
            self.banner_depth = 1
        elif self.banner_depth:
            self.banner_depth += 1
        if self.banner_depth and tag == "button":
            self.banner_buttons.append((attrs.get("data-cookie-choice"), []))
        if self.banner_depth and tag == "a":
            self.banner_links.append(attrs.get("href"))
        if tag == "footer":
            self.in_footer = True
            self.footer_depth = 1
        elif self.in_footer:
            self.footer_depth += 1
        if self.in_footer:
            self.footer_parts.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.in_footer:
            self.footer_parts.append(f"</{tag}>")
            self.footer_depth -= 1
            if self.footer_depth <= 0:
                self.in_footer = False
        if self.banner_depth:
            self.banner_depth -= 1
            if self.banner_depth == 0:
                self.banner_close_position = self.getpos()

    def handle_data(self, data):
        if self.banner_depth and self.banner_buttons:
            choice, text = self.banner_buttons[-1]
            if choice:
                text.append(data)
        if self.in_footer:
            self.footer_parts.append(data)


def git_file(revision, path):
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return result.stdout.decode("utf-8") if result.returncode == 0 else None


class AnalyticsPreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(TUTORIALS.glob("*.html"))
        cls.baseline_available = git_file(BASELINE, "analytics.js") is not None

    def parse(self, text):
        parser = PageParser()
        parser.feed(text)
        return parser

    def test_every_tutorial_has_analytics_and_deferred_consent_once(self):
        self.assertEqual(58, len(self.pages), "Expected exactly 58 tutorial HTML files")
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertEqual(1, len(re.findall(r'<script\b(?=[^>]*\bsrc=[\'\"](?:\.\./)?analytics\.js[\'\"])[^>]*>', text, re.I)))
                self.assertEqual(1, len(re.findall(r'<script\b(?=[^>]*\bsrc=[\'\"]\.\./cookie-consent\.js[\'\"])[^>]*>', text, re.I)))
                scripts = [s for s in self.parse(text).scripts if s.get("src") == "../cookie-consent.js"]
                self.assertEqual(1, len(scripts))
                self.assertIn("defer", scripts[0])

    def test_every_tutorial_has_one_preferences_banner(self):
        self.assertEqual(58, len(self.pages), "Expected exactly 58 tutorial HTML files")
        for page in self.pages:
            with self.subTest(page=page.name):
                parsed = self.parse(page.read_text(encoding="utf-8"))
                self.assertEqual(1, parsed.ids.count("cookie-consent-banner"))

    def test_updated_preferences_banner_contract_and_body_bottom(self):
        # Other existing variants are normalized by cookie-consent.js at runtime.
        # This patch repairs only the seven pages, not their historical templates.
        self.assertEqual(7, len(UPDATED_PAGES))
        for name in sorted(UPDATED_PAGES):
            page = TUTORIALS / name
            text = page.read_text(encoding="utf-8")
            parsed = self.parse(text)
            with self.subTest(page=page.name):
                self.assertEqual(1, parsed.ids.count("cookie-consent-banner"))
                self.assertEqual(1, text.count("<!-- Cookie Consent Banner -->"))
                self.assertEqual(1, text.count("<!-- /Cookie Consent Banner -->"))
                banner_match = BANNER_BLOCK.search(text)
                self.assertIsNotNone(banner_match, "banner must use the existing marked component block")
                choices = {}
                for choice, pieces in parsed.banner_buttons:
                    if choice:
                        choices[choice] = " ".join("".join(pieces).split())
                self.assertEqual(
                    {"accepted": "Allow analytics", "declined": "Decline analytics"},
                    choices,
                )
                self.assertIn("../pages/cookie.html", parsed.banner_links)
                self.assertRegex(
                    text,
                    r'<script\b(?=[^>]*\bsrc=[\'\"]\.\./cookie-consent\.js[\'\"])(?=[^>]*\bdefer(?:\s|=|/|>))[^>]*>\s*</script>\s*<!-- /Cookie Consent Banner -->\s*</body>',
                )
                ids = parsed.ids
                self.assertEqual(len(ids), len(set(ids)), "duplicate id on tutorial")

    def test_existing_shared_scripts_unchanged_and_analytics_not_ad_grants(self):
        if self.baseline_available:
            baseline = git_file(BASELINE, "analytics.js")
            self.assertIsNotNone(baseline)
            self.assertEqual(baseline, (ROOT / "analytics.js").read_text(encoding="utf-8"), "analytics.js changed")
        analytics = (ROOT / "analytics.js").read_text(encoding="utf-8")
        self.assertNotRegex(analytics, r"ad_storage\s*[:=]")
        self.assertNotRegex(analytics, r"ad_user_data\s*[:=]")
        self.assertNotRegex(analytics, r"ad_personalization\s*[:=]")
        self.assertNotRegex(analytics, r"'ads(?:_storage|_user_data|_personalization)'\s*:\s*'granted'")
        consent_bytes = (ROOT / "cookie-consent.js").read_bytes()
        original_analytics_iife = git_file(COOKIE_CONSENT_BASELINE, "cookie-consent.js")
        self.assertIsNotNone(original_analytics_iife, "origin/main cookie-consent.js baseline is required")
        original_analytics_iife_bytes = original_analytics_iife.encode("utf-8")
        self.assertTrue(
            consent_bytes.startswith(original_analytics_iife_bytes),
            "the original analytics IIFE must remain byte-identical to origin/main",
        )
        advertising_append = consent_bytes[len(original_analytics_iife_bytes):].decode("utf-8")
        self.assertRegex(
            advertising_append,
            r"(?s:\A\n// BEGIN ADVERTISING CONSENT MODULE — independent from the analytics IIFE\.\n\(function \(\) \{.*\n\}\)\(\);\n// END ADVERTISING CONSENT MODULE\n)\Z",
            "only one explicitly marked advertising module may follow the unchanged analytics IIFE",
        )
        consent = consent_bytes.decode("utf-8")
        self.assertNotRegex(consent, r"['\"]?ad_(?:storage|user_data|personalization)['\"]?\s*:\s*['\"]granted")

    def test_seven_page_changes_preserve_all_baseline_content(self):
        if git_file(APPROVED_MAIN, "analytics.js") is None:
            self.skipTest(f"approved-main baseline {APPROVED_MAIN} unavailable")
        self.assertEqual(7, len(UPDATED_PAGES))
        for name in sorted(UPDATED_PAGES):
            relative_path = f"tutorials/{name}"
            baseline = git_file(APPROVED_MAIN, relative_path)
            if baseline is None:
                self.skipTest(f"approved-main tutorial {relative_path} unavailable")
            current = (TUTORIALS / name).read_text(encoding="utf-8")
            with self.subTest(page=name):
                baseline_without_banner = strip_cookie_banner(baseline)
                current_without_banner = strip_cookie_banner(current)
                baseline_normalized = normalize_learner_revision(
                    relative_path, normalize_reviewed_content(relative_path, baseline_without_banner)
                )
                current_normalized = normalize_learner_revision(
                    relative_path, normalize_reviewed_content(relative_path, current_without_banner)
                )
                self.assertEqual(
                    baseline_normalized,
                    current_normalized,
                    "non-banner page content differs from approved main",
                )
                self.assertEqual(
                    self._footer_subscribe(baseline_normalized),
                    self._footer_subscribe(current_normalized),
                )
                self.assertEqual(
                    self._scientific_content(baseline_normalized),
                    self._scientific_content(current_normalized),
                )

    @staticmethod
    def _footer_subscribe(text):
        match = re.search(r"<footer\b.*?</footer>", text, re.S | re.I)
        if not match:
            return None
        return re.sub(r"\s+", " ", re.sub(r"<script\b.*?</script>", "", match.group(0), flags=re.S | re.I)).strip()

    @staticmethod
    def _scientific_content(text):
        # Compare article body and literal pre/code blocks independently of the footer/banner.
        article = re.search(r"<main\b.*?</main>", text, re.S | re.I)
        content = article.group(0) if article else text
        return re.sub(r"\s+", " ", content).strip()


if __name__ == "__main__":
    unittest.main()
