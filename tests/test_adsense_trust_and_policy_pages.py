"""Regression tests for AdSense compliance, GDPR disclosures, and E-E-A-T trust pages."""
from html import unescape
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TRUST_PAGES = (
    "about.html",
    "contact.html",
    "services.html",
    "pages/privacy.html",
    "pages/cookie.html",
    "pages/terms.html",
    "pages/disclaimer.html",
)
NON_EDITORIAL_PAGES = (
    "about.html",
    "contact.html",
    "services.html",
    "start-here.html",
    "tutorials.html",
    "404.html",
    "success.html",
    "pages/privacy.html",
    "pages/cookie.html",
    "pages/terms.html",
    "pages/disclaimer.html",
)
EXCLUDED_LEGAL_URLS = (
    "https://theomicshub.com/pages/privacy.html",
    "https://theomicshub.com/pages/terms.html",
    "https://theomicshub.com/pages/disclaimer.html",
    "https://theomicshub.com/pages/cookie.html",
    "https://theomicshub.com/services.html",
    "https://theomicshub.com/404.html",
    "https://theomicshub.com/success.html",
)
SCHEMA_RE = re.compile(r'<script[^>]*type="application/ld\+json">(.*?)</script>', re.S)
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class AdSenseTrustAndPolicyPageTests(unittest.TestCase):
    def test_all_trust_and_policy_pages_share_clean_consent_and_head_setup(self):
        for rel in TRUST_PAGES:
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertNotIn("\u2014", unescape(text), f"em-dash found in {rel}")
                self.assertNotIn("adsbygoogle.js", text, f"non-editorial page {rel} must not load adsbygoogle.js")
                self.assertNotIn("google-adsense-account", text, f"non-editorial page {rel} must not declare google-adsense-account")
                self.assertIn("gtag('consent', 'default'", text, f"{rel} missing Consent Mode default")
                self.assertIn('images/favicon.svg" rel="icon" type="image/svg+xml"', text)
                self.assertRegex(text, r'<script\s+defer=""\s+src="(?:\.\./)?analytics\.js"></script>')
                self.assertIn("cookie-consent.js", text)
                blocks = SCHEMA_RE.findall(text)
                self.assertEqual(len(blocks), 1, f"{rel} should have one JSON-LD block")
                entity = json.loads(blocks[0])
                self.assertEqual(entity["author"]["name"], "Nasir Mahmood Abbasi, PhD")
                for profile in (
                    "https://orcid.org/0009-0005-0083-1984",
                    "https://www.linkedin.com/in/nmabbasi",
                    "https://github.com/nmabbasi",
                ):
                    self.assertIn(profile, entity["author"]["sameAs"])
                ids = re.findall(r'\bid="([^"]+)"', text)
                self.assertEqual(len(ids), len(set(ids)), f"duplicate id in {rel}")

    def test_about_page_schema_and_landmark_integrity(self):
        text = (ROOT / "about.html").read_text(encoding="utf-8")
        entity = json.loads(SCHEMA_RE.findall(text)[0])
        self.assertEqual(entity["@type"], "AboutPage")
        self.assertNotIn("affiliation", entity["about"])
        alumni_names = [item["name"] for item in entity["about"]["alumniOf"]]
        self.assertEqual(alumni_names, ["University of Bordeaux"])
        self.assertNotIn("Sweden", alumni_names)
        main_start = text.index("<main ")
        main_end = text.index("</main>")
        review_pos = text.index('class="page-review-date"')
        self.assertGreater(review_pos, main_start)
        self.assertLess(review_pos, main_end)
        self.assertIn("mailto:contact@theomicshub.com", text)
        self.assertIn("Advertising never influences tutorial topics", text)

    def test_contact_page_is_educational_accessible_and_has_direct_email(self):
        text = (ROOT / "contact.html").read_text(encoding="utf-8")
        entity = json.loads(SCHEMA_RE.findall(text)[0])
        self.assertEqual(entity["@type"], "ContactPage")
        self.assertEqual(entity["mainEntity"]["email"], "mailto:contact@theomicshub.com")
        self.assertIn('href="mailto:contact@theomicshub.com"', text)
        self.assertIn("Send a Message", text)
        self.assertIn('id="topic-select"', text)
        self.assertIn('value="https://theomicshub.com/contact.html?submitted=1"', text)
        self.assertIn('id="contact-submitted-banner"', text)
        self.assertNotIn("Service Inquiry Form", text)
        self.assertNotIn("Selected Service", text)
        self.assertNotIn("Desired Turnaround", text)
        self.assertNotIn("What This Service Does Not Cover", text)
        self.assertIn("https://orcid.org/0009-0005-0083-1984", text)
        self.assertNotRegex(text, r'rel="noopener"(?!\s)')

    def test_privacy_and_cookie_policies_meet_adsense_and_gdpr_requirements(self):
        privacy = (ROOT / "pages/privacy.html").read_text(encoding="utf-8")
        cookie = (ROOT / "pages/cookie.html").read_text(encoding="utf-8")
        for name, text in (("privacy.html", privacy), ("cookie.html", cookie)):
            with self.subTest(page=name):
                self.assertIn("https://policies.google.com/technologies/partner-sites", text)
                self.assertIn("https://myadcenter.google.com/", text)
                self.assertIn("https://www.youronlinechoices.eu/", text)
                self.assertIn("Privacy and cookie settings (advertising)", text)
                self.assertIn("homepage and tutorials catalogue", text)
                self.assertNotIn("DoubleClick DART", text)
                self.assertNotIn("adssettings.google.com", text)
                self.assertNotIn("google.com/settings/ads", text)
                self.assertNotIn('rel="noopener"', text)
                self.assertIn("Last updated: November 19, 2026", text)
        self.assertIn("Google Funding Choices", privacy)
        self.assertIn("Google Funding Choices", cookie)
        self.assertIn("IAB", privacy)
        self.assertIn("IAB TCF v2.2", cookie)
        self.assertIn("Data controller:", privacy)
        self.assertIn("Nasir Mahmood Abbasi, PhD", privacy)
        self.assertIn("Data retention:", privacy)
        self.assertIn("Legal Bases &amp; International Data Transfers (EEA/UK)", privacy)
        self.assertIn("supervisory authority", privacy)
        self.assertIn('href="mailto:contact@theomicshub.com"', privacy)
        self.assertNotIn("Service Inquiry Form", privacy)

    def test_terms_and_disclaimer_alignment(self):
        terms = (ROOT / "pages/terms.html").read_text(encoding="utf-8")
        disclaimer = (ROOT / "pages/disclaimer.html").read_text(encoding="utf-8")
        self.assertIn("Privacy and cookie settings (advertising)", terms)
        self.assertIn("<h2>Governing Law</h2>", terms)
        self.assertIn('href="mailto:contact@theomicshub.com"', terms)
        self.assertIn("Last updated: November 19, 2026", terms)
        self.assertIn('href="mailto:contact@theomicshub.com"', disclaimer)
        self.assertIn("Last updated: November 19, 2026", disclaimer)
        self.assertIn("<h2>Scope and Updates</h2>", disclaimer)
        self.assertIn('href="privacy.html">Privacy Policy</a> and <a class="text-blue-600 hover:underline" href="cookie.html">Cookie Policy</a>', disclaimer)

    def test_legal_pages_use_compiled_responsive_grid_and_wrapping_breadcrumbs(self):
        for rel in ("pages/privacy.html", "pages/terms.html", "pages/disclaimer.html", "pages/cookie.html"):
            with self.subTest(page=rel):
                text = (ROOT / rel).read_text(encoding="utf-8")
                self.assertIn("grid-cols-1 md:grid-cols-3", text)
                self.assertNotIn("sm:grid-cols-3", text)
                self.assertIn("flex flex-wrap items-center justify-between", text)
        services = (ROOT / "services.html").read_text(encoding="utf-8")
        self.assertIn("scroll-margin-top:", services)
        self.assertIn("#newsletter-title #nl-error", services)
        self.assertIn('<meta content="noindex, follow" name="robots"/>', services)
        not_found = (ROOT / "404.html").read_text(encoding="utf-8")
        self.assertNotIn("google-adsense-account", not_found)
        self.assertNotIn("impact-site-verification", not_found)
        self.assertNotIn('rel="canonical"', not_found)

    def test_editorial_vs_non_editorial_adsense_consent_and_comment_hygiene(self):
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
            with self.subTest(page=rel):
                text = page.read_text(encoding="utf-8")
                self.assertNotIn("AdSense: temporarily hidden", text)
                self.assertNotIn("Hidden commercial navigation link", text)
                self.assertIn("favicon.svg", text)
                self.assertIn("gtag('consent', 'default'", text)
                self.assertIn("cookie-consent.js", text)
                if rel in NON_EDITORIAL_PAGES:
                    self.assertNotIn("adsbygoogle.js", text)
                    self.assertNotIn("google-adsense-account", text)
                else:
                    consent_pos = text.find("gtag('consent', 'default'")
                    ads_pos = text.find(
                        "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2910340533244599"
                    )
                    self.assertGreater(ads_pos, consent_pos)
                    self.assertIn("'wait_for_update': 500", text)
                    self.assertIn(
                        '<meta content="ca-pub-2910340533244599" name="google-adsense-account"/>',
                        text,
                    )
                blocks = SCHEMA_RE.findall(text)
                self.assertEqual(len(blocks), 1, f"{rel} should have one JSON-LD block")
                entity = json.loads(blocks[0])
                self.assertEqual(entity["author"]["name"], "Nasir Mahmood Abbasi, PhD")
                for profile in (
                    "https://orcid.org/0009-0005-0083-1984",
                    "https://www.linkedin.com/in/nmabbasi",
                    "https://github.com/nmabbasi",
                ):
                    self.assertIn(profile, entity["author"]["sameAs"])

    def test_sitemap_excludes_legal_and_utility_pages_and_tracks_fresh_lastmod(self):
        root = ET.parse(ROOT / "sitemap.xml").getroot()
        dates = {
            entry.findtext("s:loc", namespaces=NS): entry.findtext("s:lastmod", namespaces=NS)
            for entry in root.findall("s:url", NS)
        }
        self.assertEqual(len(dates), 32)
        for url in EXCLUDED_LEGAL_URLS:
            with self.subTest(excluded=url):
                self.assertNotIn(url, dates)
        self.assertEqual(dates["https://theomicshub.com/"], "2026-11-20")
        self.assertEqual(dates["https://theomicshub.com/tutorials.html"], "2026-11-20")


if __name__ == "__main__":
    unittest.main()
