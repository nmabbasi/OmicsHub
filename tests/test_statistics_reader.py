"""Test the actual read_values function embedded in the statistics tutorial.

Run: python3 -m unittest discover -s tests -p 'test_*.py' -v
Requires pandas and numpy; skips explicitly if those optional packages are absent.
Only synthetic CSV fixtures are used. This does not test statistical inference.
"""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
import tempfile
import unittest

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = pd = None


class CodeCollector(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.inside = False
        self.buffer = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.inside = True
            self.buffer = []

    def handle_data(self, data):
        if self.inside:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "pre" and self.inside:
            self.blocks.append("".join(self.buffer))
            self.inside = False


@unittest.skipIf(pd is None or np is None, "optional pandas and numpy are required")
class StatisticsReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        page = Path(__file__).resolve().parents[1] / "tutorials" / "statistics-for-bioinformatics.html"
        functions = []
        for text in CodeCollector(page.read_text(encoding="utf-8")).blocks:
            if "def read_values(" not in text:
                continue
            tree = ast.parse(text)
            functions.extend(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "read_values")
        if len(functions) != 1:
            raise AssertionError("Expected exactly one Python read_values function in tutorial")
        namespace = {"pd": pd, "np": np}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<tutorial reader>", "exec"), namespace)
        cls.reader = staticmethod(namespace["read_values"])

    def read(self, csv):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.csv"
            path.write_text(csv, encoding="utf-8")
            with redirect_stdout(StringIO()) as captured:
                result = self.reader(path)
            return result, captured.getvalue()

    def test_valid_numeric_values(self):
        values, output = self.read("value\n1\n3\n5\n")
        self.assertEqual(list(values), [1.0, 3.0, 5.0])
        self.assertIn("discarded 0 blank", output)

    def test_genuinely_blank_cells_are_counted_and_discarded(self):
        values, output = self.read('value\n1\n\n""\n"   "\n3\n5\n')
        self.assertEqual(list(values), [1.0, 3.0, 5.0])
        self.assertIn("discarded 3 blank", output)

    def test_malformed_nonblank_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "not numeric"):
            self.read("value\n1\nbad\n3\n")

    def test_nonblank_missing_markers_are_not_discarded(self):
        for marker in ("NA", "NaN", "NULL", "nan"):
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                self.read(f"value\n1\n{marker}\n3\n")

    def test_infinite_values_rejected(self):
        for value in ("inf", "-inf", "Infinity"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "finite"):
                self.read(f"value\n1\n{value}\n3\n")

    def test_missing_value_column_rejected(self):
        with self.assertRaisesRegex(ValueError, "column 'value'"):
            self.read("other\n1\n3\n")

    def test_too_few_observations_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            self.read("value\n1\n")

    def test_zero_variance_rejected(self):
        with self.assertRaisesRegex(ValueError, "variance is zero"):
            self.read("value\n2\n2\n2\n")


if __name__ == "__main__":
    unittest.main()
