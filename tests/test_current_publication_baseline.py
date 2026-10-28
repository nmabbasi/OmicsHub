"""Tests for exact normalization of the latest pinned mainline revisions."""
import hashlib
from pathlib import Path
import unittest

from current_publication_baseline import (
    ROOT,
    _css_rules,
    normalize_approved_navigation,
    normalize_current_publication,
    publication_layers,
)


class CurrentPublicationBaselineTests(unittest.TestCase):
    def test_each_exact_mainline_blob_restores_to_its_pinned_parent(self):
        layers = publication_layers()
        for layer_index, layer in enumerate(layers):
            next_layer = layers[layer_index + 1] if layer_index + 1 < len(layers) else None
            for relative_path, entry in layer["files"].items():
                with self.subTest(layer=layer["name"], path=relative_path):
                    expected = entry["base"]
                    if next_layer is not None:
                        older = next_layer["files"].get(relative_path)
                        if older is not None and hashlib.sha256(expected).hexdigest() == older["head_sha256"]:
                            expected = older["base"]
                    self.assertEqual(
                        normalize_current_publication(relative_path, entry["head"]),
                        expected,
                    )

    def test_generated_homepage_css_is_pinned_and_changes_only_its_hash_comment(self):
        layers = publication_layers()
        approved = layers[0]["files"]["home-page.min.css"]
        generated = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(
            hashlib.sha256(generated).hexdigest(),
            approved["generated_head_sha256"],
        )
        self.assertEqual(_css_rules(generated), _css_rules(approved["base"]))
        self.assertEqual(normalize_current_publication("home-page.min.css", generated), approved["base"])

    def test_approved_navigation_adapter_stops_at_exact_immediate_parent(self):
        approved = publication_layers()[0]
        relative_path = "tutorials/16s-rrna-prokka-annotation.html"
        entry = approved["files"][relative_path]
        self.assertEqual(normalize_approved_navigation(relative_path, entry["head"]), entry["base"])
        self.assertEqual(normalize_approved_navigation(relative_path, entry["base"]), entry["base"])
        changed = entry["head"] + b"<!-- unknown scope mutation -->\n"
        self.assertEqual(normalize_approved_navigation(relative_path, changed), changed)
        generated = (ROOT / "home-page.min.css").read_bytes()
        self.assertEqual(
            normalize_approved_navigation("home-page.min.css", generated),
            approved["files"]["home-page.min.css"]["base"],
        )

    def test_unknown_mutations_and_unlisted_paths_remain_visible(self):
        relative_path = "tutorials/scrna-seq-basics.html"
        current = (ROOT / relative_path).read_bytes()
        changed = current + b"<!-- unknown scope mutation -->\n"
        self.assertEqual(normalize_current_publication(relative_path, changed), changed)
        self.assertEqual(
            normalize_current_publication("unlisted/path.txt", b"unregistered bytes"),
            b"unregistered bytes",
        )
        css = (ROOT / "home-page.min.css").read_bytes()
        changed_css = css + b"/* unknown css mutation */\n"
        self.assertEqual(normalize_current_publication("home-page.min.css", changed_css), changed_css)


if __name__ == "__main__":
    unittest.main()
