"""Source-level contracts for the sitewide circular top control; no adapters or network."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROOT_PAGES = (
    "index.html", "start-here.html", "tutorials.html", "about.html",
    "contact.html", "services.html", "success.html", "404.html",
)


def canonical_pages() -> list[Path]:
    return [*(ROOT / name for name in ROOT_PAGES), *sorted((ROOT / "tutorials").glob("*.html")), *sorted((ROOT / "pages").glob("*.html"))]


class SitewideTopControlContracts(unittest.TestCase):
    def test_canonical_inventory_has_70_pages_and_shared_script_coverage(self):
        pages = canonical_pages()
        self.assertEqual(len(pages), 70)
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                html = page.read_text(encoding="utf-8")
                self.assertIn("subscribe-fab.js", html)
                self.assertIn("<h1", html)
        self.assertIn('defer src="/subscribe-fab.js?v=20261024-sitewide-circle"', (ROOT / "404.html").read_text(encoding="utf-8"))

    def test_shared_script_loads_stylesheet_relative_to_its_own_url(self):
        script = (ROOT / "subscribe-fab.js").read_text(encoding="utf-8")
        self.assertIn("document.currentScript?.src", script)
        self.assertRegex(script, r"new URL\('back-to-top\.css\?v=20261024-sitewide-circle', sharedScriptURL\)")
        self.assertIn("tools.hidden = true", script)
        self.assertIn("window.scrollY < 240", script)

    def test_generated_control_is_a_native_anchor_with_unique_heading_target(self):
        script = (ROOT / "subscribe-fab.js").read_text(encoding="utf-8")
        self.assertIn("document.createElement('a')", script)
        self.assertIn("document.querySelector('main h1') || document.querySelector('h1')", script)
        self.assertIn("const baseId = 'site-page-title'", script)
        self.assertIn("existing.href = `#${heading.id}`", script)
        self.assertIn("target.focus({ preventScroll: true })", script)
        self.assertIn("target.focus()", script)
        self.assertIn("event.button !== 0", script)
        self.assertIn("event.preventDefault();", script)
        self.assertIn("window.history.replaceState", script)
        self.assertIn("window.location.replace(cleanUrl)", script)
        self.assertIn("target.scrollIntoView({ block: 'start' })", script)
        self.assertIn("target.scrollIntoView(true)", script)
        self.assertIn("window.scrollTo(0, targetY)", script)
        self.assertIn("M12 19V5m-6 6 6-6 6 6", script)
        self.assertRegex(script, r"body h1, body h2, body h3, body h4, body h5, body h6, body p, body li")
        self.assertRegex(script, r"body a\[href\], body button, body summary, body input, body select, body textarea")


if __name__ == "__main__":
    unittest.main()
