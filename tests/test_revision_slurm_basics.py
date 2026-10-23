"""Offline regression tests for the Basic Slurm Commands lesson.

These tests exercise displayed snippets and local command mocks only. They do
not contact a Slurm controller, load a site module, or run a cluster job.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser


ROOT = Path(__file__).resolve().parents[1]
LESSON = ROOT / "tutorials" / "hpc-basic-commands.html"


class PreformattedCodeParser(HTMLParser):
    """Collect decoded text from each preformatted code example."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._in_pre = False
        self._current: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "pre":
            self._in_pre = True
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self._in_pre:
            self.blocks.append("".join(self._current))
            self._in_pre = False

    def handle_data(self, data: str) -> None:
        if self._in_pre:
            self._current.append(data)


def page_and_blocks() -> tuple[str, list[str]]:
    page = LESSON.read_text(encoding="utf-8")
    parser = PreformattedCodeParser()
    parser.feed(page)
    return page, parser.blocks


def find_block(blocks: list[str], marker: str) -> str:
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"Expected one code block containing {marker!r}, got {len(matches)}")
    return matches[0]


def executable(directory: Path, name: str, contents: str) -> Path:
    path = directory / name
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o755)
    return path


def run_bash(script: str, *, cwd: Path, path: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    child_env = os.environ.copy()
    child_env.update({"PATH": path, "HOME": str(cwd)})
    if env:
        child_env.update(env)
    return subprocess.run(
        ["/bin/bash", "-c", script],
        cwd=cwd,
        env=child_env,
        text=True,
        capture_output=True,
        check=False,
    )


class RevisionSlurmBasicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page, cls.blocks = page_and_blocks()
        cls.python_example = find_block(cls.blocks, "Selected Python: {sys.executable}")
        cls.batch_script = find_block(cls.blocks, "REPLACE_WITH_SITE_DOCUMENTED_PYTHON_MODULE")
        cls.submit_code = find_block(cls.blocks, "submission=$(sbatch --parsable smoke.sbatch)")
        cls.queue_code = find_block(cls.blocks, 'squeue -u "$USER"')
        cls.status_code = find_block(cls.blocks, "sacct -M \"$CLUSTER\"")

    def test_page_keeps_reference_format_existing_ad_markup_and_no_em_dash(self) -> None:
        self.assertIn('class="prose prose-blue prose-lg max-w-none lesson-page lesson-format--reference"', self.page)
        self.assertIn('data-tutorial-format="reference"', self.page)
        self.assertIn('aria-label="Learning path navigation"', self.page)
        self.assertIn("googlesyndication", self.page)
        self.assertIn("google-adsense-account", self.page)
        self.assertNotIn("\u2014", self.page)
        self.assertIn("No real cluster, scheduler, paid service", self.page)

    def test_displayed_batch_submission_and_status_shell_syntax(self) -> None:
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash is required to syntax-check the displayed Bash examples")
        for label, snippet in (
            ("batch", self.batch_script),
            ("queue", self.queue_code),
            ("submission", self.submit_code),
            ("accounting", self.status_code),
        ):
            with self.subTest(snippet=label), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"{label}.sh"
                path.write_text(snippet, encoding="utf-8")
                result = subprocess.run([bash, "-n", str(path)], text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_synthetic_python_example_runs_and_prints_contract(self) -> None:
        python = shutil.which("python3")
        if not python:
            self.skipTest("python3 is required to run the displayed synthetic fixture")
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "local-smoke.py"
            script.write_text(self.python_example, encoding="utf-8")
            result = subprocess.run([python, str(script)], text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Selected Python:", result.stdout)
        self.assertIn("Python version:", result.stdout)
        self.assertIn("Hostname:", result.stdout)
        self.assertIn("Sum 1..100: 5050", result.stdout)

    def test_module_load_failure_stops_before_any_python_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            marker = root / "python-was-run"
            executable(bin_dir, "module", "#!/bin/sh\necho 'mock module load failed' >&2\nexit 42\n")
            for name in ("python", "python3"):
                executable(bin_dir, name, f"#!/bin/sh\nprintf '%s\\n' ran > {marker}\nexit 0\n")
            batch = root / "smoke.sbatch"
            batch.write_text(self.batch_script, encoding="utf-8")
            result = run_bash(f"bash {batch}", cwd=root, path=f"{bin_dir}:/usr/bin:/bin")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Python module load failed", result.stderr)
        self.assertFalse(marker.exists(), "no Python command may run after a failed module load")
        self.assertNotIn("Selected Python:", result.stdout)

    def test_successful_batch_path_reports_mock_selected_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            executable(bin_dir, "module", "#!/bin/sh\nexit 0\n")
            executable(
                bin_dir,
                "python3",
                "#!/bin/sh\n"
                "if [ \"$1\" = --version ]; then echo 'Python 3.mock'; exit 0; fi\n"
                "echo 'Sum 1..100: 5050'\n",
            )
            batch = root / "smoke.sbatch"
            batch.write_text(self.batch_script, encoding="utf-8")
            result = run_bash(f"bash {batch}", cwd=root, path=f"{bin_dir}:/usr/bin:/bin")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"Selected Python: {bin_dir / 'python3'}", result.stdout)
        self.assertIn("Python 3.mock", result.stdout)
        self.assertIn("Sum 1..100: 5050", result.stdout)

    def test_malformed_sbatch_response_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            executable(bin_dir, "sbatch", "#!/bin/sh\nprintf '%s\\n' 'not-a-job-id'\n")
            result = run_bash(self.submit_code, cwd=root, path=f"{bin_dir}:/usr/bin:/bin")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unexpected sbatch --parsable response", result.stderr)

    def test_numeric_and_cluster_qualified_sbatch_responses_are_captured(self) -> None:
        for response, expected in (("4829", "Slurm accepted job 4829"), ("4829;cluster-east", "Slurm accepted job 4829 on cluster cluster-east")):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                bin_dir = root / "bin"
                bin_dir.mkdir()
                executable(bin_dir, "sbatch", f"#!/bin/sh\nprintf '%s\\n' '{response}'\n")
                result = run_bash(self.submit_code, cwd=root, path=f"{bin_dir}:/usr/bin:/bin")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(expected, result.stdout)

    def test_sacct_success_gates_expected_log_check_and_uses_cluster_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            calls = root / "calls.txt"
            executable(bin_dir, "squeue", f"#!/bin/sh\nprintf 'squeue %s\\n' \"$*\" >> '{calls}'\n")
            executable(
                bin_dir,
                "sacct",
                f"#!/bin/sh\nprintf 'sacct %s\\n' \"$*\" >> '{calls}'\nprintf '4829|COMPLETED|0:0\\n4829.batch|COMPLETED|0:0\\n'\n",
            )
            (root / "slurm-4829.out").write_text("Sum 1..100: 5050\n", encoding="utf-8")
            result = run_bash(f'JOB_ID="4829"; CLUSTER="cluster-east"; {self.status_code}', cwd=root, path=f"{bin_dir}:/usr/bin:/bin")
            call_log = calls.read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("COMPLETED|0:0", result.stdout)
        self.assertIn("Confirmed COMPLETED/0:0", result.stdout)
        self.assertIn("squeue -M cluster-east -j 4829", call_log)
        self.assertIn("sacct -M cluster-east", call_log)
        self.assertIn("--jobs=4829", call_log)

    def test_pending_or_missing_accounting_is_not_called_failure_or_read_as_success(self) -> None:
        for output in ("4829|PENDING|0:0\n", ""):
            with self.subTest(accounting=output), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                bin_dir = root / "bin"
                bin_dir.mkdir()
                executable(bin_dir, "squeue", "#!/bin/sh\necho '4829|PENDING'\n")
                executable(bin_dir, "sacct", "#!/bin/sh\nprintf '%s' \"${MOCK_SACCT_OUTPUT}\"\n")
                result = run_bash(
                    f'JOB_ID="4829"; CLUSTER=""; {self.status_code}',
                    cwd=root,
                    path=f"{bin_dir}:/usr/bin:/bin",
                    env={"MOCK_SACCT_OUTPUT": output},
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                "not evidence of failure" in result.stderr or "do not prove failure" in result.stderr,
                result.stderr,
            )
            self.assertNotIn("Confirmed COMPLETED/0:0", result.stdout)


if __name__ == "__main__":
    unittest.main()
