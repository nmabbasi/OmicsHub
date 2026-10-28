#!/usr/bin/env python3
"""Focused regression tests for the first-job Slurm tutorial route.

All commands are extracted from the page and run only with local stub commands;
these tests do not invoke sbatch or validate behavior on a real cluster.
"""
from html import unescape
from pathlib import Path
import re
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials" / "hpc-submission-part1.html"
CODE_BLOCK = re.compile(r'<pre\b[^>]*>\s*<code\b[^>]*>(.*?)</code>\s*</pre>', re.S)
BARE_AMPERSAND = re.compile(r"&(?!#\d+;|#x[0-9a-fA-F]+;|[A-Za-z][A-Za-z0-9]+;)")


def code_blocks():
    text = PAGE.read_text(encoding="utf-8")
    return [unescape(code) for code in CODE_BLOCK.findall(text)]


def block_containing(marker):
    return next(code for code in code_blocks() if marker in code)


def executable(path, content):
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


class LearnerPathTests(unittest.TestCase):
    def test_first_job_route_has_targets_and_optional_topics_are_linked(self):
        text = PAGE.read_text(encoding="utf-8")
        for target in (
            "before-submit", "smoke-job", "resources", "submit-job", "job-state",
            "optional-parallel", "optional-conda",
        ):
            with self.subTest(target=target):
                self.assertIn(f'href="#{target}"', text)
                self.assertIn(f'id="{target}"', text)
        for target in (
            "optional-parallel", "optional-conda",
        ):
            self.assertRegex(text, rf'<h2 id="{target}">Optional\b')
        for removed_target in ("optional-x11", "optional-custom-modules", "optional-compression"):
            with self.subTest(removed_target=removed_target):
                self.assertNotIn(f'href="#{removed_target}"', text)
                self.assertNotIn(f'id="{removed_target}"', text)
        self.assertRegex(text, r'<nav\b[^>]*aria-label="First-job learning route"')
        self.assertIn('<h2>First-job route</h2>', text)
        self.assertIn('id="smoke-job">First job: a safe smoke test</h2>', text)

    def test_environment_variables_are_documented_individually_with_conditions(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn("no general rule", text)
        self.assertNotIn("Capitalizing every letter", text)
        self.assertIn("SLURM_CPUS_PER_TASK</code> is set only when", text)
        self.assertIn("SLURM_ARRAY_TASK_ID</code> is set for array tasks", text)
        self.assertIn("SLURM_JOB_NODELIST</code> describes nodes allocated", text)
        self.assertIn(
            'href="https://slurm.schedmd.com/sbatch.html#SECTION_OUTPUT-ENVIRONMENT-VARIABLES"',
            text,
        )

    def test_smoke_script_is_single_copy_and_shell_syntax_is_valid(self):
        blocks = code_blocks()
        smoke = [code for code in blocks if "--job-name=hpc-smoke" in code]
        self.assertEqual(len(smoke), 1)
        script = smoke[0]
        self.assertIn("hostname\ndate", script)
        self.assertIn("--ntasks=1", script)
        self.assertIn("--cpus-per-task=1", script)
        self.assertNotIn("module load", script)
        result = subprocess.run(["sh", "-n"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_smoke_script_runs_only_against_stub_hostname_and_date(self):
        script = block_containing("--job-name=hpc-smoke")
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            executable(directory / "hostname", "#!/bin/sh\nprintf 'test-node\\n'\n")
            executable(directory / "date", "#!/bin/sh\nprintf 'Thu Jan  1 00:00:00 UTC 1970\\n'\n")
            env = os.environ.copy()
            env["PATH"] = str(directory) + os.pathsep + os.defpath
            result = subprocess.run(
                ["sh", "-s"], input=script, text=True, capture_output=True,
                cwd=directory, env=env,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "test-node", "Thu Jan  1 00:00:00 UTC 1970",
        ])

    def test_parallel_script_checks_each_step_and_surfaces_a_stub_failure(self):
        script = block_containing("step0_pid=$!")
        self.assertIn('wait "$step0_pid"', script)
        self.assertIn('wait "$step1_pid"', script)
        result = subprocess.run(["sh", "-n"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            executable(directory / "module", "#!/bin/sh\nexit 0\n")
            executable(
                directory / "srun",
                "#!/bin/sh\ncase \"$*\" in *program1*) exit 7 ;; esac\nexit 0\n",
            )
            env = os.environ.copy()
            env["PATH"] = str(directory) + os.pathsep + os.defpath
            result = subprocess.run(
                ["sh", "-s"], input=script, text=True, capture_output=True,
                cwd=directory, env=env,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("program1=7", result.stderr)

    def test_array_example_uses_a_supplied_slurm_index_with_stub_commands(self):
        script = block_containing("$SLURM_ARRAY_TASK_ID")
        result = subprocess.run(["sh", "-n"], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            executable(directory / "module", "#!/bin/sh\nexit 0\n")
            executable(directory / "srun", "#!/bin/sh\nprintf '%s\\n' \"$*\" > \"$SRUN_CAPTURE\"\n")
            env = os.environ.copy()
            env["PATH"] = str(directory) + os.pathsep + os.defpath
            env["SLURM_ARRAY_TASK_ID"] = "2"
            env["SRUN_CAPTURE"] = str(directory / "srun-capture.txt")
            result = subprocess.run(
                ["sh", "-s"], input=script, text=True, capture_output=True,
                cwd=directory, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--arg=2", Path(env["SRUN_CAPTURE"]).read_text(encoding="utf-8"))

    def test_code_examples_escape_html_operators(self):
        text = PAGE.read_text(encoding="utf-8")
        for index, code in enumerate(CODE_BLOCK.findall(text), 1):
            with self.subTest(block=index):
                self.assertNotIn("<", code, "Escape literal less-than operators as &lt;")
                self.assertIsNone(BARE_AMPERSAND.search(code))


if __name__ == "__main__":
    unittest.main()
