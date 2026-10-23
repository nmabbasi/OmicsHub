#!/usr/bin/env python3
"""Stage one conventional 10x Visium sample for both Seurat and Squidpy.

Python 3.10+; standard library only. Refuses an existing destination. Downloads
about 30 MB from 10x Genomics and verifies the recorded SHA256 fingerprints.
This prepares inputs; it does not execute or validate either analysis branch.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
from urllib.request import urlopen

SAMPLE = "V1_Adult_Mouse_Brain"
BASE = f"https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/{SAMPLE}/{SAMPLE}_"
SOURCES = (
    ("filtered_feature_bc_matrix.h5", "eb78379e02dcf48036abf05b67233e73ecb0d880787feb82f76ff16f6ce01eb3"),
    ("spatial.tar.gz", "46d6b05ba740f232d6bf4b27b9a8846815851e000985fb878f1364bab04e5bd4"),
)
REQUIRED_SPATIAL = (
    "tissue_positions_list.csv", "scalefactors_json.json",
    "tissue_lowres_image.png", "tissue_hires_image.png",
)
MAX_BYTES = 200 * 1024 * 1024


def download_file(url: str, destination: Path) -> None:
    total = 0
    with urlopen(url, timeout=60) as response, destination.open("xb") as stream:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("Download exceeds this teaching example's 200 MiB limit")
            stream.write(chunk)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_spatial_archive(archive: Path, destination: Path) -> None:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        if sum(member.size for member in members) > MAX_BYTES:
            raise ValueError("Expanded spatial archive exceeds 200 MiB")
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or not path.parts
                    or path.parts[0] != "spatial" or "\\" in member.name
                    or not (member.isfile() or member.isdir())):
                raise ValueError(f"Unsafe or unexpected archive member: {member.name}")
        for member in members:
            target = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise ValueError(f"Missing archive data: {member.name}")
                with source, target.open("xb") as output:
                    shutil.copyfileobj(source, output)


def prepare(destination: Path, fetcher=download_file) -> None:
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Destination already exists; choose a new path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".visium-staging-", dir=destination.parent) as temporary:
        stage = Path(temporary)
        records = []
        for filename, expected in SOURCES:
            path = stage / filename
            print(f"Downloading {filename}", flush=True)
            fetcher(BASE + filename, path)
            actual = sha256(path)
            if actual != expected:
                raise ValueError(f"Source changed or download corrupted: {filename}; SHA256 mismatch. Do not disable verification.")
            records.append({"url": BASE + filename, "file": filename,
                            "bytes": path.stat().st_size, "sha256": actual})
        with (stage / "filtered_feature_bc_matrix.h5").open("rb") as stream:
            if stream.read(8) != b"\x89HDF\r\n\x1a\n":
                raise ValueError("Expected an HDF5 matrix file")
        extract_spatial_archive(stage / "spatial.tar.gz", stage)
        for filename in REQUIRED_SPATIAL:
            if not (stage / "spatial" / filename).is_file():
                raise ValueError(f"Required spatial file missing: {filename}")
        manifest = {"sample": SAMPLE, "prepared_utc": datetime.now(timezone.utc).isoformat(),
                    "boundary": "Input download/checksums/layout only; no R or Python analysis executed.",
                    "sources": records}
        (stage / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Destination appeared while preparing: {destination}")
        stage.rename(destination)
    print(f"Prepared shared R/Python input: {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/visium") / SAMPLE)
    args = parser.parse_args()
    try:
        prepare(args.output)
    except (OSError, ValueError, tarfile.TarError) as error:
        parser.exit(1, f"Input preparation failed: {error}\n")


if __name__ == "__main__":
    main()
