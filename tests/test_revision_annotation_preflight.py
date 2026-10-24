"""Bounded checks for the displayed CellTypist preflight, using invented data only."""

from __future__ import annotations

import hashlib
import html.parser
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials" / "advanced-ai-single-cell.html"
FIXTURE = ROOT / "files" / "annotation-preflight-lesson" / "low-overlap.json"


class CodeBlockParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._active = False
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "code" and attrs.get("class") == "language-python":
            self._active = True
            self._parts = []

    def handle_endtag(self, tag):
        if tag == "code" and self._active:
            self.blocks.append("".join(self._parts))
            self._active = False

    def handle_data(self, data):
        if self._active:
            self._parts.append(data)


def displayed_python():
    parser = CodeBlockParser()
    parser.feed(PAGE.read_text(encoding="utf-8"))
    matching = [block for block in parser.blocks if 'INPUT_PATH = Path("my_data.h5ad")' in block]
    if len(matching) != 1:
        raise AssertionError(f"Expected one displayed preflight code block, found {len(matching)}")
    return matching[0]


class FakeNames(list):
    @property
    def is_unique(self):
        return len(self) == len(set(self))


class FakeMissingValues:
    def isna(self):
        return self

    def any(self):
        return False


class FakeAnnData:
    def __init__(self, features):
        self.var_names = FakeNames(features)
        self.n_obs = 3
        self.n_vars = len(features)
        self.layers = {"counts": object()}
        self.obs = {"review_overcluster": FakeMissingValues()}


class AnnotationPreflightRevisionTests(unittest.TestCase):
    def test_displayed_script_is_valid_python_and_has_required_audit_contract(self):
        code = displayed_python()
        compile(code, "tutorial-displayed-code", "exec")
        for required in (
            "INPUT_SPECIES", "MODEL_SPECIES", "INPUT_FEATURE_ID_CONVENTION",
            "MODEL_FEATURE_ID_CONVENTION", "model.features", "model.description",
            "CONTEXT_COMPATIBILITY_REVIEWED is not True",
            "model_feature_fraction", "MIN_MODEL_FEATURE_FRACTION",
            "celltypist-run-manifest.json", "input_sha256", "model_sha256",
            "pred.probability_matrix", "pred.decision_matrix", "majority_voting",
            "require_same_cell_order", "celltypist-review.csv",
        ):
            self.assertIn(required, code)

    def test_invented_low_overlap_fixture_refuses_before_annotate_and_writes_manifest(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertIn("Invented teaching fixture only", fixture["fixture_notice"])
        self.assertEqual(fixture["minimum_model_feature_fraction"], 0.25)
        observed_fraction = len(set(fixture["query_features"]) & set(fixture["model_features"])) / len(fixture["model_features"])
        self.assertEqual(observed_fraction, fixture["expected_model_feature_fraction"])
        self.assertLess(observed_fraction, fixture["minimum_model_feature_fraction"])

        calls = {"annotate": 0}
        fake_adata = FakeAnnData(fixture["query_features"])

        class FakeModel:
            features = fixture["model_features"]
            description = {"details": "Invented synthetic model adapter; not a public model"}
            @staticmethod
            def load(path):
                self.assertTrue(Path(path).is_absolute())
                self.assertEqual(Path(path).name, "Immune_All_Low.pkl")
                self.assertIn("/", path)
                return FakeModel()

        fake_model_api = types.SimpleNamespace(Model=FakeModel)
        def read_h5ad(path):
            self.assertEqual(Path(path).name, "my_data.h5ad")
            return fake_adata

        def forbidden_annotate(*args, **kwargs):
            calls["annotate"] += 1
            raise AssertionError("Annotation must not run after the overlap gate refuses")

        with tempfile.TemporaryDirectory() as temp_dir:
            work = Path(temp_dir)
            (work / "my_data.h5ad").write_bytes(b"invented synthetic input checksum fixture")
            (work / "Immune_All_Low.pkl").write_bytes(b"invented synthetic model checksum fixture")
            original_cwd = Path.cwd()
            fake_modules = {
                "anndata": types.SimpleNamespace(__version__="synthetic-test"),
                "numpy": types.SimpleNamespace(__version__="synthetic-test"),
                "scanpy": types.SimpleNamespace(
                    __version__="synthetic-test",
                    read_h5ad=read_h5ad,
                    pp=types.SimpleNamespace(),
                ),
            }
            celltypist = types.ModuleType("celltypist")
            celltypist.__version__ = "synthetic-test"
            celltypist.models = fake_model_api
            celltypist.annotate = forbidden_annotate
            fake_modules["celltypist"] = celltypist
            saved_modules = {name: sys.modules.get(name) for name in fake_modules}
            try:
                os.chdir(work)
                sys.modules.update(fake_modules)
                # This synthetic fixture is explicitly context-reviewed; keep every other
                # displayed statement unchanged and execute the page's actual code.
                code = displayed_python().replace(
                    "CONTEXT_COMPATIBILITY_REVIEWED = False",
                    "CONTEXT_COMPATIBILITY_REVIEWED = True",
                    1,
                )
                self.assertNotEqual(code, displayed_python())
                with self.assertRaisesRegex(RuntimeError, "Preflight refused annotation"):
                    exec(compile(code, "tutorial-displayed-code", "exec"), {"__name__": "__main__"})
            finally:
                os.chdir(original_cwd)
                for name, previous in saved_modules.items():
                    if previous is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = previous

            manifest_path = work / "celltypist-run-manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "refused_preflight")
            self.assertEqual(manifest["input_sha256"], hashlib.sha256((work / "my_data.h5ad").read_bytes()).hexdigest())
            self.assertEqual(manifest["model_sha256"], hashlib.sha256((work / "Immune_All_Low.pkl").read_bytes()).hexdigest())
            self.assertEqual(manifest["overlap_report"]["exact_matched_feature_count"], 1)
            self.assertEqual(manifest["overlap_report"]["model_feature_fraction_matched"], 0.125)
            self.assertTrue(manifest["preflight_issues"])
            self.assertEqual(calls["annotate"], 0)

    def test_review_exercise_is_explicitly_illustrative_and_has_unresolved_answer(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("Invented teaching example, not a CellTypist result", text)
        self.assertIn("Conflicting evidence", text)
        self.assertIn("Review answer:</strong> unresolved", text)


if __name__ == "__main__":
    unittest.main()
