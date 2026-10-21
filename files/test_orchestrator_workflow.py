import csv
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import orchestrator_workflow as ow

DEMO_COUNTS = "gene_id,S1,S2,S3\nGENE1,10,20,0\nGENE2,0,5,0\nGENE3,90,75,0\nGENE4,0,0,0\n"
DEMO_META = "sample_id,group\nS1,control\nS2,case\nS3,case\n"

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.counts, self.meta = self.root / "counts.csv", self.root / "metadata.csv"
        self.write_inputs(DEMO_COUNTS, DEMO_META)
    def tearDown(self): self.tmp.cleanup()
    def write_inputs(self, counts, metadata):
        self.counts.write_text(counts, encoding="utf-8")
        self.meta.write_text(metadata, encoding="utf-8")
    def invoke(self, out, *extra):
        return ow.main(["--counts", str(self.counts), "--metadata", str(self.meta), "--out", str(out), *extra])

    def test_demo_golden_qc_and_roles(self):
        out = self.root / "run"
        self.assertEqual(self.invoke(out), 0)
        with (out / "sample_qc.csv").open() as f: rows = list(csv.DictReader(f))
        self.assertEqual([(r["sample_id"], int(r["library_size"]), int(r["detected_genes"]), r["low_library_warning"]) for r in rows],
                         [("S1", 100, 2, "no"), ("S2", 100, 3, "no"), ("S3", 0, 0, "yes")])
        self.assertEqual(json.loads((out / "plan.json").read_text()), {"steps": ["qc"]})
        roles = [json.loads(x) for x in (out / "events.jsonl").read_text().splitlines()]
        self.assertIn("needs_human_review", [x["status"] for x in roles])
        self.assertIn("synthetic", (out / "report.md").read_text().lower())
        self.assertIn("counts_sha256", json.loads((out / "manifest.json").read_text()))
        self.assertFalse((out / "cpm.csv").exists())

    def test_metadata_reordered_joined_by_id(self):
        self.meta.write_text("sample_id,group\nS3,case\nS1,control\nS2,case\n")
        out = self.root / "run"
        self.assertEqual(self.invoke(out), 0)
        with (out / "sample_qc.csv").open() as f: rows = list(csv.DictReader(f))
        self.assertEqual([r["group"] for r in rows], ["control", "case", "case"])

    def test_invalid_counts_matrix_inputs(self):
        bad = [
            ("gene_id,S1,S2\nG1,1,-1\n", DEMO_META),
            ("gene_id,S1,S2\nG1,1.5,2\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\n-G1,1,2\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\nG1,1234567890123,2\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\nG1,١,2\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\nG1,NaN,2\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\nG1,1\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S2\nG1,1,2\nG1,3,4\n", "sample_id,group\nS1,a\nS2,b\n"),
            ("gene_id,S1,S1\nG1,1,2\n", "sample_id,group\nS1,a\n"),
            ("gene_id,S1,S2\nG1,1,2\n", "sample_id,group\nS1,a\n"),
            ("gene_id,S1,S2\nG1,1,2\n", "sample_id,group\nS1,a\nS2,b\nS2,c\n"),
        ]
        for idx, (counts, meta) in enumerate(bad):
            with self.subTest(idx=idx):
                self.write_inputs(counts, meta)
                out = self.root / f"bad{idx}"
                self.assertEqual(self.invoke(out), 2)
                self.assertFalse(out.exists())  # invalid inputs are rejected before output/planning

    def test_invalid_plan_schemas_and_steps(self):
        cases = [{"steps": ["shell"]}, {"steps": ["qc", "qc"]}, {"steps": ["cpm", "qc"]},
                 {"steps": ["qc"], "code": "x"}, {"steps": []}, {"steps": ["qc", "cpm"]}]
        for idx, obj in enumerate(cases):
            with self.subTest(plan=obj):
                plan = self.root / f"p{idx}.json"; plan.write_text(json.dumps(obj))
                out = self.root / f"run{idx}"
                self.assertEqual(self.invoke(out, "--plan", str(plan)), 2)
                self.assertFalse((out / "sample_qc.csv").exists())
        plan = self.root / "norm.json"; plan.write_text('{"steps":["qc"]}')
        self.assertEqual(self.invoke(self.root / "norm", "--task", "normalize", "--plan", str(plan)), 2)

    def test_zero_total_cpm_fails_and_retains_qc(self):
        out = self.root / "zero"
        self.assertEqual(self.invoke(out, "--task", "normalize"), 2)
        self.assertTrue((out / "sample_qc.csv").exists())
        self.assertFalse((out / "cpm.csv").exists())
        self.assertIn("zero library", (out / "events.jsonl").read_text())
        self.assertFalse((out / "report.md").exists())

    def test_positive_synthetic_cpm_fixture(self):
        positive = DEMO_COUNTS.replace("GENE1,10,20,0", "GENE1,10,20,5").replace("GENE3,90,75,0", "GENE3,90,75,45")
        self.write_inputs(positive, DEMO_META)
        out = self.root / "positive"
        self.assertEqual(self.invoke(out, "--task", "normalize"), 0)
        with (out / "cpm.csv").open() as f: rows = list(csv.DictReader(f))
        for sample in ("S1", "S2", "S3"):
            self.assertTrue(all(float(r[sample]) >= 0 for r in rows))
            self.assertAlmostEqual(sum(float(r[sample]) for r in rows), 1_000_000, places=3)

    def test_qc_tampering_fails_review_and_no_report(self):
        out = self.root / "tamper-qc"
        original = ow.review_outputs
        def tamper(*args, **kwargs):
            qc = out / "sample_qc.csv"
            qc.write_text(qc.read_text().replace(",100,2,", ",101,2,"))
            return original(*args, **kwargs)
        with patch.object(ow, "review_outputs", side_effect=tamper):
            self.assertEqual(self.invoke(out), 2)
        self.assertFalse((out / "report.md").exists())
        self.assertIn('"status": "failed"', (out / "events.jsonl").read_text())

    def test_cpm_tampering_fails_review_and_no_report(self):
        self.write_inputs(DEMO_COUNTS.replace("GENE1,10,20,0", "GENE1,10,20,1"), DEMO_META)
        out = self.root / "tamper-cpm"
        original = ow.review_outputs
        def tamper(*args, **kwargs):
            cpm = out / "cpm.csv"
            cpm.write_text(cpm.read_text().replace("100000", "100001", 1))
            return original(*args, **kwargs)
        with patch.object(ow, "review_outputs", side_effect=tamper):
            self.assertEqual(self.invoke(out, "--task", "normalize"), 2)
        self.assertFalse((out / "report.md").exists())
        self.assertIn('"status": "failed"', (out / "events.jsonl").read_text())

    def test_plan_duplicate_keys_and_size_rejected(self):
        for content in ('{"steps":["qc"],"steps":["qc"]}', ' ' * (16 * 1024 + 1)):
            plan = self.root / "bad-plan.json"
            plan.write_text(content)
            out = self.root / ("duplicate" if len(content) < 100 else "oversize")
            self.assertEqual(self.invoke(out, "--plan", str(plan)), 2)
            self.assertFalse((out / "sample_qc.csv").exists())

    def test_dry_run_plan_only_no_analysis(self):
        out = self.root / "dry"
        self.assertEqual(self.invoke(out, "--dry-run"), 0)
        self.assertTrue((out / "plan.json").exists())
        self.assertFalse((out / "sample_qc.csv").exists())
        self.assertIn("plan_only", (out / "events.jsonl").read_text())
        self.assertFalse((out / "cpm.csv").exists())
        self.assertFalse((out / "report.md").exists())

    def test_refuses_output_and_demo_overwrite(self):
        out = self.root / "existing"; out.mkdir(); marker = out / "keep"; marker.write_text("safe")
        self.assertEqual(self.invoke(out), 2); self.assertEqual(marker.read_text(), "safe")
        demo = self.root / "demo"; demo.mkdir(); (demo / "keep").write_text("safe")
        self.assertEqual(ow.main(["--make-demo", str(demo)]), 2)
        self.assertEqual((demo / "keep").read_text(), "safe")
        fresh = self.root / "fresh"
        self.assertEqual(ow.main(["--make-demo", str(fresh)]), 0)
        self.assertEqual(sorted(p.name for p in fresh.iterdir()), ["counts.csv", "counts_positive.csv", "metadata.csv"])
        with (fresh / "counts_positive.csv").open(newline="") as f:
            positive = list(csv.reader(f))
        self.assertEqual([int(r[3]) for r in positive[1:]], [5, 0, 45, 0])

    def test_manifest_hashes_match_exact_parsed_snapshots(self):
        counts_before, metadata_before = self.counts.read_bytes(), self.meta.read_bytes()
        def planner_changes_source_files(*args):
            self.write_inputs(DEMO_COUNTS.replace("GENE1,10,20,0", "GENE1,11,20,0"), DEMO_META.replace("control", "different"))
            return {"steps": ["qc"]}
        out = self.root / "snapshot"
        with patch.object(ow, "openai_plan", side_effect=planner_changes_source_files):
            self.assertEqual(self.invoke(out, "--planner", "openai", "--model", "mock-model"), 0)
        manifest = json.loads((out / "manifest.json").read_text())
        self.assertEqual(manifest["counts_sha256"], hashlib.sha256(counts_before).hexdigest())
        self.assertEqual(manifest["metadata_sha256"], hashlib.sha256(metadata_before).hexdigest())
        self.assertNotEqual(manifest["counts_sha256"], ow.digest(self.counts))
        with (out / "sample_qc.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual((rows[0]["group"], rows[0]["library_size"]), ("control", "100"))

    def test_openai_planner_one_mocked_json_call_no_identifiers(self):
        class Message: content = '{"steps":["qc"]}'
        class Choice: message = Message()
        class Response: choices = [Choice()]
        class Completions:
            def __init__(self): self.calls = []
            def create(self, **kwargs): self.calls.append(kwargs); return Response()
        completions = Completions()
        class Chat: pass
        chat = Chat(); chat.completions = completions
        client_options = []
        class Client:
            def __init__(self, **kwargs):
                client_options.append(kwargs)
                self.chat = chat
        out = self.root / "mock-provider"
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-secret", "OPENAI_BASE_URL": "https://user:password@host.example:8443/path?token=query-secret"}, clear=False), patch.object(ow, "TOOLS", {"qc", "cpm"}), patch.dict("sys.modules", {"openai": type("Stub", (), {"OpenAI": Client})()}):
            self.assertEqual(self.invoke(out, "--planner", "openai", "--model", "mock-model"), 0)
        self.assertEqual(json.loads((out / "plan.json").read_text()), {"steps": ["qc"]})
        self.assertEqual(len(completions.calls), 1)
        serialized = json.dumps(completions.calls[0])
        self.assertNotIn("GENE", serialized); self.assertNotIn("S1", serialized); self.assertNotIn("10,20", serialized)
        self.assertIn('\\"n_samples\\": 3', serialized)
        self.assertEqual(completions.calls[0]["response_format"]["type"], "json_schema")
        self.assertEqual((client_options[0]["timeout"], client_options[0]["max_retries"]), (30.0, 0))
        manifest = (out / "manifest.json").read_text()
        self.assertEqual(json.loads(manifest)["provider_endpoint_origin"], "https://host.example:8443")
        for secret in ["test-secret", "password", "query-secret", "user:", "/path"]:
            self.assertNotIn(secret, manifest)

    def test_optional_provider_failures_never_run_tools_or_leak_errors(self):
        cases = [
            RuntimeError("private-provider-error-value"),
            SimpleNamespace(choices=[SimpleNamespace(finish_reason="length", message=SimpleNamespace(content='{"steps":["qc"]}', refusal=None))]),
            SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=None, refusal="private-provider-error-value"))]),
            SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="not json", refusal=None))]),
        ]
        for index, response in enumerate(cases):
            with self.subTest(case=index):
                calls = []
                def create(**kwargs):
                    calls.append(kwargs)
                    if isinstance(response, Exception):
                        raise response
                    return response
                class Client:
                    def __init__(self, **kwargs):
                        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))
                out = self.root / f"provider-failure-{index}"
                stderr = io.StringIO()
                with patch.dict("os.environ", {"OPENAI_API_KEY": "test-secret"}), patch.dict("sys.modules", {"openai": SimpleNamespace(OpenAI=Client)}), redirect_stderr(stderr):
                    self.assertEqual(self.invoke(out, "--planner", "openai", "--model", "mock-model"), 2)
                self.assertEqual(len(calls), 1)
                self.assertFalse((out / "sample_qc.csv").exists())
                self.assertFalse((out / "report.md").exists())
                self.assertNotIn("private-provider-error-value", stderr.getvalue())
                self.assertIn('"status": "failed"', (out / "events.jsonl").read_text())

if __name__ == "__main__": unittest.main()
