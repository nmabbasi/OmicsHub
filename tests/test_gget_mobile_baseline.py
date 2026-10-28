"""Closed-scope and mutation tests for the approved gget mobile baseline layer."""
import hashlib
from pathlib import Path
import unittest

from gget_mobile_baseline import (
    APPROVED_PATHS,
    BASE_COMMIT,
    FIXTURE_PATH,
    FIXTURE_SHA256,
    gget_mobile_fixture,
    restore_gget_mobile_bytes,
    restore_gget_mobile_text,
)
from current_publication_baseline import normalize_current_publication

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATHS = frozenset({
    "tutorial-library.css",
    "tutorials/deterministic-retrieval-gget-ai.html",
})


class GgetMobileBaselineTests(unittest.TestCase):
    def test_fixture_is_exactly_two_hash_pinned_paths_and_restores_to_main(self):
        self.assertEqual(APPROVED_PATHS, EXPECTED_PATHS)
        self.assertEqual(BASE_COMMIT, "0caaeabb050845dcb07905fc5bf99cd699866baa")
        self.assertEqual(hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(), FIXTURE_SHA256)
        fixture = gget_mobile_fixture()
        self.assertEqual(set(fixture), EXPECTED_PATHS)

        for relative_path, entry in fixture.items():
            with self.subTest(path=relative_path):
                current = normalize_current_publication(
                    relative_path, (ROOT / relative_path).read_bytes()
                )
                base = entry["base_bytes"]
                self.assertEqual(hashlib.sha256(current).hexdigest(), entry["current_sha256"])
                self.assertEqual(hashlib.sha256(base).hexdigest(), entry["base_sha256"])
                self.assertEqual(restore_gget_mobile_bytes(relative_path, current), base)
                self.assertEqual(restore_gget_mobile_bytes(relative_path, base), base)

    def test_any_unrecognized_page_or_css_mutation_stays_visible(self):
        fixture = gget_mobile_fixture()
        for relative_path, entry in fixture.items():
            with self.subTest(path=relative_path):
                current = (ROOT / relative_path).read_bytes()
                mutation = current + b"\n/* unrelated unapproved mutation */\n"
                self.assertNotEqual(hashlib.sha256(mutation).hexdigest(), entry["current_sha256"])
                self.assertEqual(restore_gget_mobile_bytes(relative_path, mutation), mutation)

    def test_mutation_inside_the_approved_hunk_stays_visible(self):
        relative_path = "tutorials/deterministic-retrieval-gget-ai.html"
        current = (ROOT / relative_path).read_bytes()
        mutation = current.replace(b"gget-responsive-table", b"gget-responsive-table-unapproved", 1)
        self.assertNotEqual(mutation, current)
        self.assertEqual(restore_gget_mobile_bytes(relative_path, mutation), mutation)
        self.assertEqual(restore_gget_mobile_text(relative_path, mutation.decode("utf-8")), mutation.decode("utf-8"))

    def test_unknown_paths_and_wrong_types_are_not_coerced(self):
        data = b"unrelated source"
        self.assertEqual(restore_gget_mobile_bytes("elsewhere/example.html", data), data)
        with self.assertRaises(TypeError):
            restore_gget_mobile_bytes("tutorial-library.css", "not bytes")
        with self.assertRaises(TypeError):
            restore_gget_mobile_text("tutorials/deterministic-retrieval-gget-ai.html", b"not text")


if __name__ == "__main__":
    unittest.main()
