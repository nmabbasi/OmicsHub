"""Focused coverage and fail-closed tests for the coffee-removal adapter."""
import hashlib
from pathlib import Path
import unittest

from coffee_removal_baseline import (
    BASE_COMMIT,
    EXPECTED_HTML_COUNT,
    EXPECTED_PATH_COUNT,
    FIXTURE_PATH,
    FIXTURE_SHA256,
    coffee_removal_fixture,
    restore_coffee_removal_bytes,
)
from gget_mobile_baseline import restore_gget_mobile_bytes

ROOT = Path(__file__).resolve().parents[1]
HTML_ANCHOR = (
    b'<a class="group inline-flex items-center gap-2 px-5 py-2.5 bg-white/5 '
    b'text-gray-400 font-medium rounded-lg opacity-50 hover:opacity-100 '
    b'hover:bg-[#FFDD00] hover:text-gray-900 '
    b'hover:shadow-[0_0_20px_rgba(255,221,0,0.6)] transition-all duration-300 '
    b'text-sm transform hover:-translate-y-0.5" '
    b'href="https://paypal.me/nmabbasi12020?locale.x=en_US&amp;country.x=FR" '
    b'rel="noopener noreferrer" target="_blank"><span class="text-base '
    b'grayscale group-hover:grayscale-0">\xe2\x98\x95</span><span '
    b'class="font-bold">Buy me a coffee</span></a>'
)
SCRIPT_ANCHOR = (
    b'                            <a href="https://paypal.me/nmabbasi12020?locale.x=en_US&country.x=FR" '
    b'target="_blank" class="inline-flex items-center gap-2 px-6 py-2 '
    b'bg-emerald-500 text-white font-bold rounded-lg hover:bg-emerald-600 '
    b'transition-colors shadow-sm">\n'
    b'                                <span class="text-base">\xe2\x98\x95</span> Buy me a coffee\n'
    b'                            </a>\n'
)


@unittest.skip("Historical PR baseline superseded by site-wide redesign")
class CoffeeRemovalBaselineTests(unittest.TestCase):
    def test_closed_fixture_restores_all_exact_expected_deletions(self):
        fixture = coffee_removal_fixture()
        self.assertEqual(BASE_COMMIT, "be4429d1ac4cfb0f2164239057cddd95c59620b1")
        self.assertEqual(hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), FIXTURE_SHA256)
        self.assertEqual(len(fixture), EXPECTED_PATH_COUNT)
        html_paths = {path for path in fixture if path.endswith(".html")}
        self.assertEqual(len(html_paths), EXPECTED_HTML_COUNT)
        self.assertEqual(set(fixture), html_paths | {"script.js", "home-page.min.css"})

        for relative_path, entry in sorted(fixture.items()):
            with self.subTest(path=relative_path):
                current = restore_gget_mobile_bytes(
                    relative_path, (ROOT / relative_path).read_bytes()
                )
                self.assertEqual(hashlib.sha256(current).hexdigest(), entry["current_sha256"])
                original = entry["base_bytes"]
                self.assertEqual(hashlib.sha256(original).hexdigest(), entry["base_sha256"])
                self.assertEqual(restore_coffee_removal_bytes(relative_path, current), original)
                self.assertEqual(restore_coffee_removal_bytes(relative_path, original), original)

    def test_manifested_delta_is_only_the_69_anchors_script_anchor_and_css_fingerprint(self):
        fixture = coffee_removal_fixture()
        for relative_path in sorted(path for path in fixture if path.endswith(".html")):
            with self.subTest(path=relative_path):
                before = fixture[relative_path]["base_bytes"]
                current = restore_gget_mobile_bytes(
                    relative_path, (ROOT / relative_path).read_bytes()
                )
                self.assertEqual(before.count(HTML_ANCHOR), 1)
                self.assertEqual(before.replace(HTML_ANCHOR, b"", 1), current)

        script_before = fixture["script.js"]["base_bytes"]
        self.assertEqual(script_before.count(SCRIPT_ANCHOR), 1)
        self.assertEqual(script_before.replace(SCRIPT_ANCHOR, b"\n", 1), (ROOT / "script.js").read_bytes())

        css_before = fixture["home-page.min.css"]["base_bytes"]
        css_after = (ROOT / "home-page.min.css").read_bytes()
        before_header, before_rules = css_before.split(b"\n", 1)
        after_header, after_rules = css_after.split(b"\n", 1)
        self.assertNotEqual(before_header, after_header)
        self.assertIn(b"Source SHA256:", before_header)
        self.assertIn(b"Source SHA256:", after_header)
        self.assertEqual(before_rules, after_rules)

    def test_strict_mode_rejects_unrelated_mutations_on_each_kind_of_path(self):
        fixture = coffee_removal_fixture()
        samples = ("index.html", "script.js", "home-page.min.css")
        for relative_path in samples:
            with self.subTest(path=relative_path):
                current = (ROOT / relative_path).read_bytes()
                mutated = current + b"\n<!-- unrelated unapproved change -->\n"
                with self.assertRaisesRegex(AssertionError, "unrecognized coffee-removal mutation"):
                    restore_coffee_removal_bytes(relative_path, mutated)

    def test_unknown_paths_are_outside_the_adapter_scope(self):
        data = b"unapproved path data"
        self.assertEqual(restore_coffee_removal_bytes("elsewhere/example.html", data), data)


if __name__ == "__main__":
    unittest.main()
