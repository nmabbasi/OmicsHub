"""Keep local CellTypist model loading independent of the remote model catalog."""
import ast
import os
from pathlib import Path, PureWindowsPath
import subprocess
import tempfile
import unittest

from test_revision_annotation_preflight import displayed_python


class LocalModelPathTests(unittest.TestCase):
    def test_displayed_model_path_is_resolved_before_loading(self):
        tree = ast.parse(displayed_python())
        assignment = next(node for node in tree.body
                          if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "MODEL_PATH"
                                  for target in node.targets))
        self.assertEqual(ast.unparse(assignment.value), "Path('Immune_All_Low.pkl').resolve()")
        calls = [node for node in ast.walk(tree)
                 if isinstance(node, ast.Call)
                 and ast.unparse(node.func) == "models.Model.load"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.unparse(calls[0].args[0]), "MODEL_PATH.as_posix()")

    def test_windows_model_path_retains_a_forward_slash_for_celltypist_dispatch(self):
        # CellTypist 1.7.1 distinguishes a path from a catalog name by '/' alone.
        local = PureWindowsPath("C:/teaching/model-review/Immune_All_Low.pkl")
        self.assertIn("/", local.as_posix())
        self.assertNotIn("\\", local.as_posix())
        self.assertTrue(local.is_absolute())


@unittest.skipUnless(os.environ.get("CELLTYPIST_TEST_PYTHON") and
                     os.environ.get("CELLTYPIST_TEST_MODEL"),
                     "Set isolated CellTypist Python and public model paths for the real loader test")
class RealCellTypistLocalModelTests(unittest.TestCase):
    def test_actual_loader_uses_local_file_without_catalog_lookup(self):
        model = Path(os.environ["CELLTYPIST_TEST_MODEL"]).resolve()
        self.assertTrue(model.is_file())
        self.assertEqual(model.name, "Immune_All_Low.pkl")
        source = '''
from pathlib import Path
import os
import sys
os.environ["CELLTYPIST_FOLDER"] = sys.argv[2]
from celltypist import models
calls = []
def forbidden_catalog():
    calls.append("catalog")
    raise AssertionError("Remote catalog access is forbidden in this regression")
models.get_all_models = forbidden_catalog
path = Path(sys.argv[1]).resolve()
loaded = models.Model.load(path.as_posix())
assert len(loaded.features) > 0
assert len(loaded.cell_types) > 1
assert calls == [], calls
# The original basename dispatch is still rejected by the same no-network guard.
try:
    models.Model.load(path.name)
except AssertionError as error:
    assert "Remote catalog access" in str(error)
else:
    raise AssertionError("Expected the original basename to consult the catalog")
assert calls == ["catalog"], calls
print("Explicit local path loaded the real model without catalog access")
'''
        with tempfile.TemporaryDirectory(prefix="celltypist-loader-regression-") as temp:
            result = subprocess.run(
                [os.environ["CELLTYPIST_TEST_PYTHON"], "-c", source, str(model), temp],
                cwd=model.parent, capture_output=True, text=True, timeout=120,
                env={**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"},
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("without catalog access", result.stdout)


if __name__ == "__main__":
    unittest.main()
