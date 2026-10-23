#!/usr/bin/env python3
"""Fetch the one public input specified by inputs.json; never generate study data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def validate(path: Path, source: dict) -> None:
    if not path.is_file():
        raise ValueError(f"Not a regular input file: {path}")
    if path.stat().st_size != source["bytes"]:
        raise ValueError("Input byte count differs from the recorded public archive")
    if sha256(path) != source["sha256"]:
        raise ValueError("SHA-256 mismatch: refusing an altered or different input archive")


def prepare(data_dir: Path, source: dict, cache: Path | None = None) -> Path:
    filename = source["filename"]
    if Path(filename).name != filename or not source["url"].startswith("https://"):
        raise ValueError("Manifest must name a local basename and an HTTPS public source")
    data_dir.mkdir(parents=True, exist_ok=True)
    target = data_dir / filename
    if target.exists():
        validate(target, source)
        print(f"Verified existing archive: {target}")
        return target
    descriptor, temporary = tempfile.mkstemp(prefix=".pbmc-download-", dir=data_dir)
    os.close(descriptor)
    staged = Path(temporary)
    try:
        if cache is not None:
            validate(cache, source)
            shutil.copyfile(cache, staged)
        else:
            request = Request(source["url"], headers={"User-Agent": "OmicsHub-public-PBMC-example/1.0"})
            print(f"Downloading {filename} ({source['bytes']:,} bytes)", flush=True)
            with urlopen(request, timeout=120) as response, staged.open("wb") as output:
                received = 0
                progress = 0
                while block := response.read(1024 * 1024):
                    received += len(block)
                    if received > source["bytes"]:
                        raise ValueError("Download exceeds the recorded archive size")
                    output.write(block)
                    if received - progress >= 8 * 1024 * 1024:
                        print(f"Received {received:,} bytes", flush=True)
                        progress = received
        validate(staged, source)
        # A hard-link publish is atomic and refuses to overwrite an existing path.
        os.link(staged, target)
        print(f"Verified SHA-256: {source['sha256']}")
        print(f"Public archive ready: {target}")
        return target
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--from-cache", type=Path,
                        help="Copy an already downloaded identical public archive after verifying its hash")
    args = parser.parse_args()
    try:
        source = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))["data_package"]
        prepare(args.data_dir, source, args.from_cache)
    except (OSError, ValueError, KeyError) as error:
        print(f"Input preparation stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
