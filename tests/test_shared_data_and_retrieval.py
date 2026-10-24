#!/usr/bin/env python3
"""Offline checks for input preparation and recorded retrievals, not biology."""
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("visium_preparer", ROOT / "files/visium-example/prepare_inputs.py")
VISIUM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VISIUM)


class CodeBlocks(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "code":
            self.current = []

    def handle_data(self, text):
        if self.current is not None:
            self.current.append(text)

    def handle_endtag(self, tag):
        if tag == "code" and self.current is not None:
            self.blocks.append("".join(self.current))
            self.current = None


def archive_bytes(names=None):
    """Tiny invented archive for software tests; not a biological dataset."""
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as archive:
        for name in names or ["spatial/" + x for x in VISIUM.REQUIRED_SPATIAL]:
            info = tarfile.TarInfo(name)
            info.size = 4
            archive.addfile(info, io.BytesIO(b"test"))
    return output.getvalue()


class SharedVisiumTests(unittest.TestCase):
    def test_both_readers_share_named_h5_input(self):
        text = (ROOT / "tutorials/spatial-transcriptomics-r-python.html").read_text()
        self.assertIn('shared_input = "data/visium/V1_Adult_Mouse_Brain"', text)
        self.assertIn('shared_input &lt;- "data/visium/V1_Adult_Mouse_Brain"', text)
        self.assertIn('counts_file="filtered_feature_bc_matrix.h5"', text)
        self.assertIn('filename = "filtered_feature_bc_matrix.h5"', text)
        self.assertNotIn("visium_brain_data/", text)
        self.assertIn("Both language branches were executed", text)
        self.assertIn("not a complete QC workflow", text)
        self.assertIn("Other operating systems were not tested for this spatial route", text)

    def test_verified_source_fingerprints_match_preparer(self):
        records = json.loads((ROOT / "files/visium-example/verified-inputs.json").read_text())
        self.assertEqual({r["filename"]: r["sha256"] for r in records}, dict(VISIUM.SOURCES))
        self.assertTrue(all(r["url"] == VISIUM.BASE + r["filename"] for r in records))

    def test_prepare_stages_verified_files_and_refuses_overwrite(self):
        payloads = {"filtered_feature_bc_matrix.h5": b"\x89HDF\r\n\x1a\nunit-test-fixture", "spatial.tar.gz": archive_bytes()}
        fingerprints = tuple((name, hashlib.sha256(data).hexdigest()) for name, data in payloads.items())
        def fixture_fetcher(url, destination):
            destination.write_bytes(payloads[destination.name])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "sample"
            with patch.object(VISIUM, "SOURCES", fingerprints):
                VISIUM.prepare(target, fetcher=fixture_fetcher)
                self.assertTrue((target / "spatial/tissue_lowres_image.png").is_file())
                self.assertEqual(json.loads((target / "source-manifest.json").read_text())["sample"], VISIUM.SAMPLE)
                with self.assertRaises(FileExistsError):
                    VISIUM.prepare(target, fetcher=fixture_fetcher)

    def test_changed_checksum_does_not_publish_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "sample"
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                VISIUM.prepare(target, fetcher=lambda url, path: path.write_bytes(b"wrong-source"))
            self.assertFalse(target.exists())

    def test_archive_rejects_traversal_and_links(self):
        for attack in ("../outside", "/outside", "spatial/../../outside"):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as directory:
                archive = Path(directory) / "sample.tar.gz"
                archive.write_bytes(archive_bytes([attack]))
                with self.assertRaises(ValueError):
                    VISIUM.extract_spatial_archive(archive, Path(directory))
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "link.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                info = tarfile.TarInfo("spatial/link")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside"
                bundle.addfile(info)
            with self.assertRaises(ValueError):
                VISIUM.extract_spatial_archive(archive, Path(directory))


class RetrievalEvidenceTests(unittest.TestCase):
    def test_published_observed_outputs_match_success_manifest(self):
        folder = ROOT / "files/gget-example/observed"
        manifest = json.loads((folder / "manifest.json").read_text())
        self.assertEqual(manifest["gget_version"], "0.28.6")
        self.assertEqual(len(manifest["runs"]), 2)
        for run in manifest["runs"]:
            data = (folder / run["output_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), run["sha256"])
            self.assertEqual(len(data), run["output_bytes"])
            self.assertEqual(run["exit_status"], 0)
            self.assertFalse(run["timed_out"])
            self.assertTrue(run["nonempty_expected_format"])
            self.assertLessEqual(datetime.fromisoformat(run["started_utc"]), datetime.fromisoformat(run["finished_utc"]))
        record = json.loads((folder / "ACE2_info.json").read_text())["ENSG00000130234"]
        self.assertEqual(record["primary_gene_name"], "ACE2")
        self.assertEqual(record["assembly_name"], "GRCh38")
        lines = (folder / "ACE2_protein.fasta").read_text().splitlines()
        self.assertIn("Q9BYF1", lines[0])
        sequence = "".join(x for x in lines[1:] if x and not x.startswith(">"))
        self.assertTrue(re.fullmatch("[A-Z]+", sequence))
        self.assertEqual(len(sequence), int(re.search(r"sequence_length: (\d+)", lines[0]).group(1)))

    def test_dependency_constraints_are_in_published_commands(self):
        text = (ROOT / "tutorials/deterministic-retrieval-gget-ai.html").read_text()
        constraints = (ROOT / "files/gget-example/requirements-direct.txt").read_text()
        freeze = (ROOT / "files/gget-example/observed/requirements.txt").read_text()
        for pin in ("gget==0.28.6", "numpy==1.26.4", "pandas==2.2.3"):
            self.assertIn(pin, text)
            self.assertIn(pin, constraints)
            self.assertIn(pin, freeze)
        self.assertIn("separate Python API export above was not part of this recorded run", text)

    def test_extracted_shell_logger_uses_utc_and_keeps_failure_status(self):
        text = (ROOT / "tutorials/deterministic-retrieval-gget-ai.html").read_text()
        block = next(x for x in CodeBlocks(text).blocks if "log_run()" in x)
        logger = block.split("# Save the raw command-line JSON")[0]
        self.assertNotIn("--iso-8601", logger)
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "retrieval-results").mkdir()
            script = logger + "\nlog_run success true\nlog_run failure false\nstatus=$?\nexit \"$status\"\n"
            result = subprocess.run(["bash", "-c", script], cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            lines = (Path(directory) / "retrieval-results/commands.log").read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn("exit=0", lines[0])
            self.assertIn("exit=1", lines[1])
            for line in lines:
                timestamps = re.findall(r"(?:start|end)=([^ |]+)", line)
                self.assertEqual(len(timestamps), 2)
                for stamp in timestamps:
                    self.assertTrue(stamp.endswith("Z"))
                    datetime.fromisoformat(stamp.replace("Z", "+00:00"))


if __name__ == "__main__":
    unittest.main()
