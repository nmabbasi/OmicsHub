#!/usr/bin/env python3
"""Generate the exact latest-review fixture against the pinned base commit.

This is a deliberately narrow helper for the 2026-10-25 review. It only reads
an explicit path allowlist, emits contextual literal hunks for text files, and
records generated CSS as a complete-file SHA-256 asset. It never modifies
source files. Use --write to replace the fixture and --update-pin to refresh
its SHA constant in tests/latest_review_baseline.py after sources are final.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "36bc46d"
FIXTURE = ROOT / "tests/fixtures/latest-review-edits.json"
BASELINE = ROOT / "tests/latest_review_baseline.py"
# Explicit files only: no directory-wide acceptance of future/unreviewed edits.
TEXT_PATHS = frozenset({
    ".github/workflows/tutorial-review.yml",
    "index.html", "tutorials.html", "sitemap.xml", "script.js", "services.html", "style.css",
    "tutorials/advanced-ai-single-cell.html",
    "tutorials/ai-bioinformatics-github-copilot.html",
    "tutorials/ai-coding-cursor-aider.html",
    "tutorials/ai-prompt-engineering-seurat.html",
    "tutorials/autonomous-research-orchestrator.html",
    "tutorials/biological-data-formats.html",
    "tutorials/command-line-part1.html",
    "tutorials/command-line-part2.html",
    "tutorials/computer-data-fundamentals.html",
    "tutorials/deterministic-retrieval-gget-ai.html",
    "tutorials/evolutionary-phylogeny-analysis.html",
    "tutorials/git-github-bioinformatics.html",
    "tutorials/hpc-support.html",
    "tutorials/introduction-to-bioinformatics.html",
    "tutorials/long-read-pacbio-nanopore.html",
    "tutorials/metagenomics-assembly-mapping.html",
    "tutorials/research-reporting-interpretation.html",
    "tutorials/scrna-seq-integration-strategies.html",
    "tutorials/single-cell-foundation-models.html",
    "tutorials/wes-variant-calling-pipeline.html",
})
ASSET_PATHS = frozenset({"home-page.min.css"})
ALLOWED_PATHS = TEXT_PATHS | ASSET_PATHS


def git_base(path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{path}"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"cannot read {BASE_COMMIT}:{path}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def add_contextual_hunks(before: str, after: str, path: str) -> list[dict[str, str]]:
    """Build non-overlapping unique literal hunks, retaining >=3 context lines when available."""
    old_lines = before.splitlines(keepends=True)
    new_lines = after.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    groups = matcher.get_grouped_opcodes(3)
    chunks = []
    for group in groups:
        i1, i2 = group[0][1], group[-1][2]
        j1, j2 = group[0][3], group[-1][4]
        old_start, old_end = i1, i2
        new_start, new_end = j1, j2
        old_chunk = "".join(old_lines[old_start:old_end])
        new_chunk = "".join(new_lines[new_start:new_end])
        if old_chunk == new_chunk:
            continue
        # Extend only across identical lines, keeping the mapping exact, until
        # the source-side literal is unique. This prevents ambiguous reversals.
        while before.count(old_chunk) != 1:
            expanded = False
            if old_start and new_start and old_lines[old_start - 1] == new_lines[new_start - 1]:
                old_start -= 1
                new_start -= 1
                expanded = True
            if before.count("".join(old_lines[old_start:old_end])) == 1:
                old_chunk = "".join(old_lines[old_start:old_end])
                new_chunk = "".join(new_lines[new_start:new_end])
                break
            if old_end < len(old_lines) and new_end < len(new_lines) and old_lines[old_end] == new_lines[new_end]:
                old_end += 1
                new_end += 1
                expanded = True
            old_chunk = "".join(old_lines[old_start:old_end])
            new_chunk = "".join(new_lines[new_start:new_end])
            if not expanded:
                raise AssertionError(f"cannot make a unique contextual hunk for {path}")
        # Runtime fixture validation also checks these boundary contexts.
        prefix = 0
        for a, b in zip(old_chunk.splitlines(keepends=True), new_chunk.splitlines(keepends=True)):
            if a != b:
                break
            prefix += 1
        suffix = 0
        old_part, new_part = old_chunk.splitlines(keepends=True), new_chunk.splitlines(keepends=True)
        for a, b in zip(reversed(old_part[prefix:]), reversed(new_part[prefix:])):
            if a != b:
                break
            suffix += 1
        if (prefix < 3 and old_start != 0) or (suffix < 3 and old_end != len(old_lines)):
            raise AssertionError(f"generated hunk lacks available three-line context: {path}")
        chunks.append({"before": old_chunk, "after": new_chunk})
    # Verify the ordered literal patches actually reconstruct the exact file.
    reconstructed = before
    for index, patch in enumerate(chunks):
        if reconstructed.count(patch["before"]) != 1:
            raise AssertionError(f"fixture patch is not unique in sequence {index}: {path}")
        reconstructed = reconstructed.replace(patch["before"], patch["after"], 1)
    if reconstructed != after:
        raise AssertionError(f"contextual chunks do not reconstruct current file: {path}")
    return chunks


def build_fixture() -> dict:
    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE_COMMIT, "--"], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    unexpected = sorted(set(changed) - ALLOWED_PATHS - {
        "tests/home_catalogue_baseline.py", "tests/reader_text_colour_baseline.py",
        "tests/tutorial_ui_baseline.py", "tests/latest_review_baseline.py",
        "tests/test_latest_review_baseline.py", "tools/generate_latest_review_fixture.py",
    })
    # Untracked generated fixture and test helpers do not appear in `git diff`;
    # tracked source changes outside this explicit review boundary must stop.
    if unexpected:
        raise AssertionError("changed paths outside the explicit source allowlist: " + ", ".join(unexpected))
    files = {}
    for path in sorted(set(changed) & ALLOWED_PATHS):
        base = git_base(path)
        current = (ROOT / path).read_bytes()
        if base == current:
            continue
        record = {
            "base_sha256": hashlib.sha256(base).hexdigest(),
            "current_sha256": hashlib.sha256(current).hexdigest(),
        }
        if path in ASSET_PATHS:
            record["kind"] = "asset"
        else:
            try:
                old_text = base.decode("utf-8")
                new_text = current.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AssertionError(f"text source is not UTF-8: {path}") from exc
            record["kind"] = "text"
            record["patches"] = add_contextual_hunks(old_text, new_text, path)
        files[path] = record
    if not files:
        raise AssertionError("no changed allowlisted source files found")
    return {"schema": 1, "base_commit": BASE_COMMIT, "files": files}


def update_pin(digest: str) -> None:
    source = BASELINE.read_text(encoding="utf-8")
    import re
    updated, count = re.subn(
        r'(?m)^FIXTURE_SHA256 = "[^"]*"$',
        f'FIXTURE_SHA256 = "{digest}"', source, count=1,
    )
    if count != 1:
        raise AssertionError("could not locate latest-review fixture SHA pin")
    BASELINE.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write deterministic JSON fixture")
    parser.add_argument("--update-pin", action="store_true", help="also update the baseline module SHA pin")
    args = parser.parse_args()
    fixture = build_fixture()
    raw = (json.dumps(fixture, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_bytes(raw)
    if args.update_pin:
        if not args.write:
            parser.error("--update-pin requires --write")
        update_pin(digest)
    print(f"fixture_sha256={digest}")
    print(f"files={len(fixture['files'])}")
    print(f"text_files={sum(v['kind'] == 'text' for v in fixture['files'].values())}")
    print(f"assets={sum(v['kind'] == 'asset' for v in fixture['files'].values())}")
    print(f"fixture={'written' if args.write else 'not written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
