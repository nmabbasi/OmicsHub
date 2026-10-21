import importlib.util
import math
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("protein_structure_workflow.py")
spec = importlib.util.spec_from_file_location("protein_structure_workflow", MODULE)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def atom(serial, atom="CA", alt=" ", chain="A", resid="1", icode=" ", b="80.00"):
    return (f"ATOM  {serial:5d} {atom:4s}{alt}{'ALA':>3s} {chain}{int(resid):4d}{icode}   "
            f"{0.0:8.3f}{0.0:8.3f}{0.0:8.3f}{1.0:6.2f}{b:>6s}          C\n")


class PdbParsingTests(unittest.TestCase):
    def test_parse_ca_and_ignore_non_ca(self):
        rows = w.parse_ca(atom(1) + atom(2, atom="N") + atom(3, chain="B", resid="2", b="42.5"))
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["chain"] for r in rows}, {"A", "B"})
        self.assertEqual(rows[1]["bfactor"], 42.5)

    def test_prefer_blank_and_deduplicate_alternates(self):
        text = atom(1, alt="A", b="40.0") + atom(2, alt="B", b="95.0") + atom(3, alt=" ", b="75.0")
        rows = w.parse_ca(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bfactor"], 75.0)

    def test_invalid_or_nonfinite_bfactor_rejected(self):
        for value in ("bad", "nan", "inf", "-1.0", "101.0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                w.parse_ca(atom(1, b=value))

    def test_no_ca_rejected(self):
        with self.assertRaisesRegex(ValueError, "no alpha-carbon"):
            w.parse_ca(atom(1, atom="N"))

    def test_summary_is_not_claim_of_biology(self):
        rows = w.parse_ca(atom(1, b="60") + atom(2, resid="2", b="80"))
        self.assertEqual(w.summarize(rows)["mean_ca_bfactor"], 70)
        self.assertIn("not evidence of function", w.summarize(rows)["interpretation"])

    def test_exclusive_write_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "keep.txt"
            target.write_text("original")
            with self.assertRaises(FileExistsError):
                w.write_new(target, b"replacement")
            self.assertEqual(target.read_text(), "original")

if __name__ == "__main__":
    unittest.main()

class HardeningTests(unittest.TestCase):
    def test_natural_residue_order(self):
        rows = w.parse_ca(atom(1, resid="10") + atom(2, resid="2") + atom(3, resid="1"))
        self.assertEqual([r["residue_id"] for r in rows], ["1", "2", "10"])

    def test_missing_residue_number_rejected(self):
        line = atom(1)
        line = line[:22] + "    " + line[26:]
        with self.assertRaisesRegex(ValueError, "residue number"):
            w.parse_ca(line)

    def test_short_ca_record_rejected(self):
        with self.assertRaisesRegex(ValueError, "too short"):
            w.parse_ca("ATOM      1  CA  ALA A   1\n")

    def test_duplicate_same_altloc_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate CA"):
            w.parse_ca(atom(1) + atom(2))

    def test_multiple_model_records_rejected(self):
        with self.assertRaisesRegex(ValueError, "multiple MODEL"):
            w.parse_ca("MODEL        1\n" + atom(1) + "ENDMDL\nMODEL        2\n" + atom(2))

    def test_generic_summary_does_not_assume_alphafold(self):
        interpretation = w.summarize(w.parse_ca(atom(1)))["interpretation"]
        self.assertIn("provenance was not verified", interpretation)
        self.assertIn("experimental B-factors are not pLDDT", interpretation)

    def test_multiple_matching_api_entries_fail_before_pdb_download(self):
        from unittest.mock import patch, mock_open
        import json
        payload = [{"uniprotAccession": "P69905", "pdbUrl": "https://alphafold.ebi.ac.uk/a.pdb"},
                   {"uniprotAccession": "P69905", "pdbUrl": "https://alphafold.ebi.ac.uk/b.pdb"}]
        response = mock_open(read_data=json.dumps(payload).encode()).return_value
        with tempfile.TemporaryDirectory() as d, patch.object(w.urllib.request, "urlopen", return_value=response) as urlopen:
            with self.assertRaisesRegex(ValueError, "multiple matching"):
                w.fetch("P69905", Path(d))
            self.assertEqual(urlopen.call_count, 1)

if __name__ == "__main__":
    unittest.main()
