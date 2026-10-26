#!/usr/bin/env python3
"""Validate static tutorial learning contracts and local site references.

Run from any directory: python3 tests/validate_tutorials.py
Uses only the Python standard library; it does not execute biological analyses.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

FORMATS = {
    "hands-on-lab": "Hands-on lab",
    "conceptual-guide": "Conceptual guide",
    "advanced-template": "Advanced template",
    "reference": "Reference",
}


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.contracts: list[str] = []
        self.meta: dict[str, str] = {}
        self.headings: list[str] = []
        self.title = ""
        self.jsonld: list[str] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag: str, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        for attribute in ("href", "src"):
            if a.get(attribute):
                self.links.append((tag, a[attribute]))
        if "tutorial-learning-contract" in a.get("class", "").split():
            self.contracts.append(a.get("data-tutorial-format", ""))
        if tag == "meta":
            self.meta[a.get("name", a.get("property", ""))] = a.get("content", "")
        if tag in ("h1", "title") or (tag == "script" and a.get("type") == "application/ld+json"):
            self._capture = tag
            self._buffer = []

    def handle_data(self, data: str):
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag: str):
        if tag == self._capture:
            text = "".join(self._buffer).strip()
            if tag == "h1":
                self.headings.append(text)
            elif tag == "title":
                self.title = text
            elif tag == "script":
                self.jsonld.append(text)
            self._capture = None
            self._buffer = []


def inspect(root: Path):
    errors: list[str] = []
    warnings: list[str] = []
    formats: Counter = Counter()
    pages = sorted(
        path for path in (root / "tutorials").glob("*.html")
        if '<meta name="tutorial-route-redirect"' not in path.read_text(encoding="utf-8")
    )
    if len(pages) != 58:
        errors.append(f"Expected 58 tutorials, found {len(pages)}")
    cache: dict[Path, Page] = {}

    def load(path: Path):
        if path not in cache:
            cache[path] = Page(path.read_text(encoding="utf-8"))
        return cache[path]

    for path in pages:
        text = path.read_text(encoding="utf-8")
        page = load(path)
        label = path.relative_to(root).as_posix()
        if len(page.contracts) != 1:
            errors.append(f"{label}: expected one learning-format contract, found {len(page.contracts)}")
        elif page.contracts[0] not in FORMATS:
            errors.append(f"{label}: unknown learning format {page.contracts[0]!r}")
        else:
            formats[page.contracts[0]] += 1
        if len(page.headings) != 1 or not page.headings[0]:
            errors.append(f"{label}: expected one nonempty h1")
        elif page.title.split(" | ")[0].strip() != page.headings[0]:
            errors.append(f"{label}: title and h1 disagree")
        if not page.meta.get("description"):
            errors.append(f"{label}: missing description")
        for key in ("og:description", "twitter:description"):
            if page.meta.get(key) != page.meta.get("description"):
                errors.append(f"{label}: {key} disagrees with description")
        for raw in page.jsonld:
            try:
                json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{label}: invalid JSON-LD: {exc.msg}")
        duplicates = [key for key, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            errors.append(f"{label}: duplicate IDs: {', '.join(duplicates)}")
        if "This tutorial records the software versions used in its examples." in text:
            errors.append(f"{label}: unsupported generic version-recording claim remains")
        for tag, url in page.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (root / unquote(parsed.path.lstrip("/"))) if parsed.path.startswith("/") else (path.parent / unquote(parsed.path))
            target = target.resolve()
            if not target.is_relative_to(root):
                errors.append(f"{label}: local URL escapes site root: {url}")
            elif not target.exists():
                errors.append(f"{label}: missing local target: {url}")
            elif parsed.fragment and target.suffix == ".html":
                if unquote(parsed.fragment) not in load(target).ids:
                    warnings.append(f"{label}: missing HTML anchor: {url}")
    catalogue = load(root / "tutorials.html")
    linked = {Path(urlsplit(url).path).name for tag, url in catalogue.links if urlsplit(url).path.startswith("tutorials/")}
    missing = {p.name for p in pages} - linked
    if missing:
        errors.append("Catalogue omits tutorials: " + ", ".join(sorted(missing)))
    return {"tutorials": len(pages), "formats": dict(sorted(formats.items())), "errors": errors, "warnings": sorted(set(warnings))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, help="Optional report path")
    args = parser.parse_args()
    result = inspect(args.root.resolve())
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
