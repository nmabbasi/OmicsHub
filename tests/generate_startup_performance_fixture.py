#!/usr/bin/env python3
"""Generate the pinned startup-performance fixture against commit 93f0626.

This helper reads only the explicit production inventory in
startup_performance_baseline.py. Tutorial article element bytes must match the
base exactly. It never edits production source files; use --write and
--update-pin together after source edits are final.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from generate_latest_review_fixture import add_contextual_hunks
from editorial_review_baseline import normalize_editorial_review_bytes
from startup_performance_baseline import (
    ASSET_PATHS,
    BASE_COMMIT,
    FIXTURE_PATH,
    ROOT,
    TUTORIAL_PATHS,
)

BASELINE = ROOT / "tests/startup_performance_baseline.py"
ARTICLE_PATTERN = re.compile(rb"<article\b[^>]*>.*?</article\s*>", re.I | re.S)


def git_base(relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{relative_path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise AssertionError(f"cannot read immutable base {BASE_COMMIT}:{relative_path}")
    return result.stdout


def build_fixture() -> dict:
    if len(TUTORIAL_PATHS) != 58 or len(ASSET_PATHS) != 3:
        raise AssertionError("startup-performance scope must remain exactly 58 tutorials and three assets")
    if any(not path.startswith("tutorials/") or not path.endswith(".html") for path in TUTORIAL_PATHS):
        raise AssertionError("startup-performance tutorial inventory contains a non-HTML path")

    files = {}
    for relative_path in sorted(TUTORIAL_PATHS | ASSET_PATHS):
        base = git_base(relative_path)
        current = normalize_editorial_review_bytes(
            relative_path, (ROOT / relative_path).read_bytes()
        )
        if base == current:
            raise AssertionError(f"expected a startup-performance delta but found identical bytes: {relative_path}")
        record = {
            "base_sha256": hashlib.sha256(base).hexdigest(),
            "current_sha256": hashlib.sha256(current).hexdigest(),
        }
        if relative_path in ASSET_PATHS:
            record["kind"] = "asset"
        else:
            base_articles = ARTICLE_PATTERN.findall(base)
            current_articles = ARTICLE_PATTERN.findall(current)
            if not base_articles or base_articles != current_articles:
                raise AssertionError(f"article element bytes changed from immutable base: {relative_path}")
            try:
                before_text, after_text = base.decode("utf-8"), current.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AssertionError(f"tutorial source is not UTF-8: {relative_path}") from exc
            record["kind"] = "text"
            record["patches"] = add_contextual_hunks(before_text, after_text, relative_path)
        files[relative_path] = record

    if set(files) != TUTORIAL_PATHS | ASSET_PATHS:
        raise AssertionError("generated fixture path set differs from explicit inventory")
    return {"schema": 1, "base_commit": BASE_COMMIT, "files": files}


def update_pin(digest: str) -> None:
    source = BASELINE.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(?m)^FIXTURE_SHA256 = "[^"]*"$',
        f'FIXTURE_SHA256 = "{digest}"', source, count=1,
    )
    if count != 1:
        raise AssertionError("could not locate startup-performance fixture SHA pin")
    BASELINE.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write deterministic JSON fixture")
    parser.add_argument("--update-pin", action="store_true", help="update baseline SHA pin after writing")
    args = parser.parse_args()
    if args.update_pin and not args.write:
        parser.error("--update-pin requires --write")
    fixture = build_fixture()
    raw = (json.dumps(fixture, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if args.write:
        FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_PATH.write_bytes(raw)
    if args.update_pin:
        update_pin(digest)
    print(f"fixture_sha256={digest}")
    print(f"files={len(fixture['files'])}")
    print(f"text_files={sum(record['kind'] == 'text' for record in fixture['files'].values())}")
    print(f"assets={sum(record['kind'] == 'asset' for record in fixture['files'].values())}")
    print(f"fixture={'written' if args.write else 'not written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
