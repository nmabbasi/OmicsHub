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
import http.client
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import tarfile
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SAMPLE = "V1_Adult_Mouse_Brain"
BASE = f"https://cf.10xgenomics.com/samples/spatial-exp/1.1.0/{SAMPLE}/{SAMPLE}_"
SOURCES = (
    ("filtered_feature_bc_matrix.h5", "eb78379e02dcf48036abf05b67233e73ecb0d880787feb82f76ff16f6ce01eb3"),
    ("spatial.tar.gz", "46d6b05ba740f232d6bf4b27b9a8846815851e000985fb878f1364bab04e5bd4"),
)
# Exact sizes observed for the same immutable sources whose hashes are pinned above.
SOURCE_SIZES = {
    "filtered_feature_bc_matrix.h5": 21_106_953,
    "spatial.tar.gz": 9_039_745,
}
REQUIRED_SPATIAL = (
    "tissue_positions_list.csv", "scalefactors_json.json",
    "tissue_lowres_image.png", "tissue_hires_image.png",
)
MAX_BYTES = 200 * 1024 * 1024
RANGE_CHUNK_BYTES = 1024 * 1024
RANGE_ATTEMPTS = 4


def _is_transient(error: BaseException) -> bool:
    if isinstance(error, HTTPError):
        return error.code in {408, 429, 500, 502, 503, 504}
    return isinstance(error, (URLError, TimeoutError, socket.timeout,
                              ConnectionError, http.client.HTTPException))


def _read_at_most(response, limit: int) -> bytes:
    """Read no more than limit bytes, tolerating short network reads."""
    chunks = []
    remaining = limit
    while remaining:
        block = response.read(min(64 * 1024, remaining))
        if not block:
            break
        chunks.append(block)
        remaining -= len(block)
    return b"".join(chunks)


def _download_full(url: str, destination: Path, expected_size: int) -> None:
    created = False
    try:
        with urlopen(url, timeout=60) as response:
            status = getattr(response, "status", None)
            if status is None and hasattr(response, "getcode"):
                status = response.getcode()
            if status is not None and status != 200:
                raise ValueError(f"Expected HTTP 200 for full download, received {status}")
            with destination.open("xb") as stream:
                created = True
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("Download exceeds this teaching example's 200 MiB limit")
                    stream.write(chunk)
        if total != expected_size:
            raise ValueError(f"Unexpected full-download size: expected {expected_size}, received {total}")
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


def _content_range(response) -> tuple[int, int, int] | None:
    headers = getattr(response, "headers", None)
    value = headers.get("Content-Range") if headers is not None else None
    if value is None and hasattr(response, "getheader"):
        value = response.getheader("Content-Range")
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", value or "", re.IGNORECASE)
    return tuple(map(int, match.groups())) if match else None


def _download_ranged(url: str, destination: Path, expected_size: int) -> None:
    if expected_size <= 0 or expected_size > MAX_BYTES:
        raise ValueError("Expected source size is outside this teaching example's 200 MiB limit")
    created = False
    try:
        with destination.open("xb") as output:
            created = True
            for begin in range(0, expected_size, RANGE_CHUNK_BYTES):
                end = min(begin + RANGE_CHUNK_BYTES, expected_size) - 1
                wanted = end - begin + 1
                request = Request(url, headers={
                    "Range": f"bytes={begin}-{end}",
                    "Accept-Encoding": "identity",
                    "User-Agent": "Mozilla/5.0",
                })
                last_error = None
                for attempt in range(RANGE_ATTEMPTS):
                    try:
                        with urlopen(request, timeout=60) as response:
                            status = getattr(response, "status", None)
                            if status is None and hasattr(response, "getcode"):
                                status = response.getcode()
                            got_range = _content_range(response)
                            expected_range = (begin, end, expected_size)
                            if status != 206 or got_range != expected_range:
                                raise ValueError(
                                    f"Invalid ranged response: status={status}, "
                                    f"Content-Range={got_range!r}, expected 206/{expected_range!r}"
                                )
                            headers = getattr(response, "headers", None)
                            content_length = headers.get("Content-Length") if headers is not None else None
                            if content_length is not None and int(content_length) != wanted:
                                raise ValueError(
                                    f"Invalid ranged Content-Length: expected {wanted}, received {content_length}"
                                )
                            payload = _read_at_most(response, wanted + 1)
                            if len(payload) != wanted:
                                raise ValueError(
                                    f"Invalid ranged body size for bytes {begin}-{end}: "
                                    f"expected {wanted}, received {len(payload)}"
                                )
                        output.write(payload)
                        break
                    except BaseException as error:
                        if not _is_transient(error) or attempt + 1 == RANGE_ATTEMPTS:
                            raise
                        last_error = error
                        time.sleep(min(2 ** attempt, 4))
                if last_error is not None and output.tell() < end + 1:
                    raise last_error
        if destination.stat().st_size != expected_size:
            raise ValueError(
                f"Ranged download size mismatch: expected {expected_size}, received {destination.stat().st_size}"
            )
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


def download_file(url: str, destination: Path) -> None:
    """Try the ordinary source GET; recover only 403/transient failures by strict byte ranges."""
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"Refusing to overwrite an existing download: {destination}")
    url_filename = Path(url).name
    filename = url_filename.removeprefix(SAMPLE + "_")
    try:
        expected_size = SOURCE_SIZES[filename]
    except KeyError as error:
        raise ValueError(f"No pinned source size for {filename}") from error
    if expected_size > MAX_BYTES:
        raise ValueError("Expected source size is outside this teaching example's 200 MiB limit")

    try:
        _download_full(url, destination, expected_size)
    except BaseException as error:
        recoverable = (isinstance(error, HTTPError) and error.code == 403) or _is_transient(error)
        if not recoverable:
            raise
        # The full transfer removes only a partial file that it created.
        # Exclusive creation below must preserve any concurrently appearing file.
        print(f"Ordinary GET unavailable ({error}); retrying with verified HTTP byte ranges", flush=True)
        _download_ranged(url, destination, expected_size)


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
