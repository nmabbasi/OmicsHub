#!/usr/bin/env python3
"""Capture the published gget 0.28.6 queries without inventing successful output.

Run in an environment with gget==0.28.6:
    python run_retrieval.py --output retrieval-results
The output directory must not exist. Network results can change or fail.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import subprocess
import sys


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("retrieval-results"))
    args = parser.parse_args()
    installed = version("gget")
    if installed != "0.28.6":
        parser.error("This example requires gget==0.28.6; do not silently substitute versions.")
    executable = shutil.which("gget")
    if not executable:
        parser.error("gget CLI is missing from PATH; activate the same Python environment.")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "gget_version": installed,
        "python_version": sys.version.split()[0],
        "query_id": "ENSG00000130234",
        "boundary": "Live CLI retrieval only; not a biological analysis or validation.",
        "runs": [],
    }
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True, check=True)
    (args.output / "requirements.txt").write_text(freeze.stdout, encoding="utf-8")
    queries = [
        (["info", "ENSG00000130234"], "ACE2_info.json"),
        (["seq", "--translate", "ENSG00000130234"], "ACE2_protein.fasta"),
    ]
    failed = False
    for command, filename in queries:
        started = utc_now()
        print("Starting gget " + " ".join(command), flush=True)
        timed_out = False
        try:
            result = subprocess.run([executable, *command], capture_output=True, timeout=120)
            stdout, stderr, status = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, status = error.stdout or b"", error.stderr or b"", None
            timed_out = True
        output = args.output / filename
        output.write_bytes(stdout)
        (args.output / (filename + ".stderr.txt")).write_bytes(stderr)
        valid_shape = False
        if status == 0:
            if filename.endswith(".json"):
                try:
                    parsed = json.loads(stdout)
                    valid_shape = isinstance(parsed, (dict, list)) and bool(parsed)
                except (ValueError, UnicodeDecodeError):
                    pass
            else:
                lines = stdout.decode("utf-8", errors="replace").splitlines()
                valid_shape = bool(lines and lines[0].startswith(">") and any(x and not x.startswith(">") for x in lines[1:]))
        run = {
            "command": ["gget", *command], "started_utc": started,
            "finished_utc": utc_now(), "exit_status": status,
            "timed_out": timed_out, "output_file": filename,
            "output_bytes": len(stdout), "sha256": hashlib.sha256(stdout).hexdigest(),
            "nonempty_expected_format": valid_shape,
        }
        manifest["runs"].append(run)
        failed |= status != 0 or not valid_shape
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(run), flush=True)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
