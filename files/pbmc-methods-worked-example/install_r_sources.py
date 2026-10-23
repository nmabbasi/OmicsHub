#!/usr/bin/env python3
"""Install checksum-pinned R sources after the documented Ubuntu prerequisites."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from prepare_inputs import HERE, prepare


def r_output(expression: str, *arguments: str) -> str:
    return subprocess.check_output(["Rscript", "-e", expression, *arguments], text=True).strip()


def installed(package: str) -> str:
    return r_output('p <- commandArgs(TRUE)[1]; cat(tryCatch(as.character(packageVersion(p)), error=function(e) "missing"))', package)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--package-cache", type=Path, default=Path("package-cache"))
    args = parser.parse_args()
    manifest = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    try:
        actual_r = r_output('cat(as.character(getRversion()))')
        expected_r = manifest["tested_r_version"]
        print(f"R: installed={actual_r}, tested={expected_r}")
        if actual_r != expected_r:
            raise ValueError(f"R version mismatch: need {expected_r}, found {actual_r}")
        if not args.check_only:
            library = Path(r_output('cat(path.expand(Sys.getenv("R_LIBS_USER")))').split(":" )[0])
            if not str(library) or str(library) == ".":
                raise ValueError("R_LIBS_USER must identify a writable user R library")
            library.mkdir(parents=True, exist_ok=True)
            for source in manifest["r_sources"]:
                if installed(source["package"]) == source["version"]:
                    print(f"Already verified: {source['package']} {source['version']}")
                    continue
                archive = prepare(args.package_cache, source)
                subprocess.run(["R", "CMD", "INSTALL", "--library=" + str(library), str(archive)], check=True)
        mismatches = []
        for package, expected in manifest["tested_direct_versions"].items():
            actual = installed(package)
            print(f"{package}: installed={actual}, tested={expected}")
            if actual != expected:
                mismatches.append(f"{package}: need {expected}, found {actual}")
        if mismatches:
            raise ValueError("Tested environment does not match: " + "; ".join(mismatches))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Environment setup stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
