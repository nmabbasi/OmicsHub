"""Unit tests for the resilient navigation guard in subscribe-fab.js."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NavigationGuardTests(unittest.TestCase):
    def setUp(self):
        self.script = (ROOT / "subscribe-fab.js").read_text(encoding="utf-8")
        self.contact_html = (ROOT / "contact.html").read_text(encoding="utf-8")

    def test_contact_page_has_proper_nav_anchors_and_shared_script(self):
        self.assertIn('id="nav-desktop-contact"', self.contact_html)
        self.assertIn('id="nav-mobile-contact"', self.contact_html)
        self.assertIn('subscribe-fab.js', self.contact_html)

    def test_navigation_guard_normalizes_trailing_slashes_and_clean_urls(self):
        # Ensure the script strips trailing slashes and .html extension
        self.assertIn("pathname.replace(/\\/+$/, '')", self.script)
        self.assertIn("replace(/\\.html$/, '')", self.script)

    def test_navigation_guard_tracks_in_flight_target_specifically(self):
        self.assertIn("inFlightTarget", self.script)
        # Verify targeted debounce logic
        self.assertRegex(self.script, r"inFlightTarget === targetPage && now - lastNavTime < 800")

    def test_script_initializes_reliably_for_any_ready_state(self):
        self.assertIn("document.readyState === 'loading'", self.script)
        self.assertIn("DOMContentLoaded", self.script)
        self.assertIn("initAll()", self.script)

    def test_normalized_page_token_logic_matches_contact_and_home_correctly(self):
        from urllib.parse import urlparse

        def get_page_token(url: str) -> str:
            # Models: const path = new URL(url, location.href).pathname.replace(/\/+$/, '');
            #         const file = path.split('/').pop() || 'index';
            #         return file.replace(/\.html$/, '') || 'index';
            path = urlparse(url).path.rstrip('/')
            file = path.split('/')[-1] if path else 'index'
            file = re.sub(r'\.html$', '', file)
            return file or 'index'

        # Current page variants for Contact
        contact_locs = [
            "https://theomicshub.com/contact.html",
            "https://theomicshub.com/contact",
            "https://theomicshub.com/contact/",
            "http://127.0.0.1:8765/contact.html",
            "http://localhost:8765/contact/",
        ]
        for loc in contact_locs:
            token = get_page_token(loc)
            self.assertEqual(token, "contact", f"Failed for {loc}")

        # Target link variants for Contact
        contact_hrefs = ["contact.html", "/contact", "/contact.html", "https://theomicshub.com/contact"]
        for href in contact_hrefs:
            self.assertEqual(get_page_token(href), "contact", f"Failed for {href}")

        # Cross navigation: on contact, clicking index should NOT match contact
        self.assertEqual(get_page_token("index.html"), "index")
        self.assertEqual(get_page_token("https://theomicshub.com/"), "index")
        self.assertEqual(get_page_token("https://theomicshub.com"), "index")


if __name__ == "__main__":
    unittest.main()
