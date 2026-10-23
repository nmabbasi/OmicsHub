#!/usr/bin/env python3
"""Generate static redirect documents for confirmed historical tutorial URLs.

These are ordinary static HTML pages: meta refresh and a visible link help
visitors reach the moved tutorial, but they do not produce an HTTP 301/308.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "legacy-redirects.json"
CANONICAL_RE = re.compile(
    r'<link\b(?=[^>]*\brel=["\']canonical["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>',
    re.IGNORECASE,
)


def load_redirects() -> tuple[dict[str, str], dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    migration = {
        source: "tutorials/" + PurePosixPath(source).name
        for source in manifest["migration_root_urls"]
    }
    redirects = migration | manifest["historical_aliases"]
    if len(redirects) != len(migration) + len(manifest["historical_aliases"]):
        raise ValueError("Duplicate source URL in redirect manifest")
    return redirects, manifest


def canonical_url(target: str) -> str:
    page = ROOT / target
    if not page.is_file():
        raise ValueError(f"Redirect target does not exist: {target}")
    match = CANONICAL_RE.search(page.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"Redirect target has no canonical URL: {target}")
    return match.group(1)


def render(source: str, target: str) -> str:
    source_path = PurePosixPath(source)
    target_path = PurePosixPath(target)
    if not source_path.is_absolute() or source_path.parent != PurePosixPath("/"):
        raise ValueError(f"Source must be a root-level URL path: {source}")
    if target_path.is_absolute() or ".." in target_path.parts or not target.startswith("tutorials/"):
        raise ValueError(f"Target must be a relative tutorials/ route: {target}")
    canonical = html.escape(canonical_url(target), quote=True)
    href = html.escape(target, quote=True)
    title = html.escape(source_path.stem.replace("-", " ").replace("_", " ").title())
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} has moved | The Omics Hub</title>
  <meta http-equiv="refresh" content="0; url={href}">
  <link rel="canonical" href="{canonical}">
</head>
<body>
  <main>
    <h1>This tutorial has moved</h1>
    <p><a href="{href}">Continue to the current tutorial: {title}</a></p>
  </main>
</body>
</html>
'''


def generate(check: bool = False) -> list[str]:
    redirects, manifest = load_redirects()
    if manifest["migration_root_url_count"] != len(manifest["migration_root_urls"]):
        raise ValueError("Manifest migration count does not match its route list")
    failed: list[str] = []
    for source, target in redirects.items():
        if target in redirects:
            raise ValueError(f"Redirect chain detected: {source} -> {target}")
        relative_path = source.lstrip("/")
        output = ROOT / relative_path
        content = render(source, target)
        if check:
            if not output.is_file() or output.read_text(encoding="utf-8") != content:
                failed.append(relative_path)
        else:
            output.write_text(content, encoding="utf-8")
    return failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated stubs without writing")
    args = parser.parse_args()
    failed = generate(check=args.check)
    if failed:
        print("Out-of-date or missing redirect stubs: " + ", ".join(failed))
        return 1
    redirects, _ = load_redirects()
    print(f"{'Verified' if args.check else 'Generated'} {len(redirects)} static redirect stubs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
