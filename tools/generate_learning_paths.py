#!/usr/bin/env python3
"""Generate prerequisite-aware tutorial continuation navs from learning-paths.json.

Only the existing nav.reader-toolbar and nav#reader-course-navigation blocks are
replaced. Page bodies are never parsed and serialized, preserving article bytes.
Run: python3 tools/generate_learning_paths.py [--root SITE_ROOT] [--check]
"""
from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

EXPECTED_TUTORIALS = 58
NAV_PATTERNS = {
    "toolbar": re.compile(
        r'<nav\b(?=[^>]*\bclass\s*=\s*["\'][^"\']*\breader-toolbar\b[^"\']*["\'])[^>]*>.*?</nav\s*>',
        re.IGNORECASE | re.DOTALL,
    ),
    "continuation": re.compile(
        r'<nav\b(?=[^>]*\bid\s*=\s*["\']reader-course-navigation["\'])[^>]*>.*?</nav\s*>',
        re.IGNORECASE | re.DOTALL,
    ),
}


class PageFacts(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.h1: list[str] = []
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self._h1_depth = 0
        self._h1_parts: list[str] = []
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        if tag.lower() == "a" and values.get("href") is not None:
            self.links.append((values["href"] or "", "start"))
        if tag.lower() == "h1":
            self._h1_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "h1" and self._h1_depth:
            self._h1_depth -= 1
            if self._h1_depth == 0:
                self.h1.append("".join(self._h1_parts).strip())
                self._h1_parts = []

    def handle_data(self, data: str) -> None:
        if self._h1_depth:
            self._h1_parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._h1_depth:
            self._h1_parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._h1_depth:
            self._h1_parts.append(html.unescape(f"&#{name};"))


def load_site(root: Path) -> tuple[dict, dict[str, PageFacts]]:
    manifest_path = root / "tools" / "learning-paths.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = sorted((root / "tutorials").glob("*.html"))
    if len(pages) != EXPECTED_TUTORIALS:
        raise ValueError(f"Expected exactly {EXPECTED_TUTORIALS} tutorials; found {len(pages)}")
    facts: dict[str, PageFacts] = {}
    for page in pages:
        key = page.stem
        source = page.read_text(encoding="utf-8")
        data = PageFacts(source)
        if len(data.h1) != 1 or not data.h1[0]:
            raise ValueError(f"tutorials/{page.name}: expected exactly one non-empty h1")
        facts[key] = data
    configured = set(manifest.get("tutorials", {}))
    actual = set(facts)
    if configured != actual:
        missing = sorted(actual - configured)
        extra = sorted(configured - actual)
        raise ValueError(f"Manifest coverage mismatch; missing={missing}, extra={extra}")
    start = PageFacts((root / "start-here.html").read_text(encoding="utf-8"))
    for anchor in manifest.get("start_targets", {}):
        if anchor not in start.ids:
            raise ValueError(f"Start Here target #{anchor} does not exist")

    def validate_ref(source: str, target: str | None, relation: str) -> None:
        if target is None:
            return
        if target == source:
            raise ValueError(f"{source}: self-loop in {relation}")
        if target.startswith("@"):
            anchor = target[1:]
            if anchor not in manifest.get("start_targets", {}):
                raise ValueError(f"{source}: unknown Start Here target {target!r}")
        elif target not in actual:
            raise ValueError(f"{source}: unknown tutorial target {target!r} in {relation}")

    for key, item in manifest["tutorials"].items():
        validate_ref(key, item.get("previous"), "previous")
        for edge in item.get("next", []):
            if not isinstance(edge.get("reason"), str) or not edge["reason"].strip():
                raise ValueError(f"{key}: every next edge needs a concise reason")
            validate_ref(key, edge.get("target"), "next")
    return manifest, facts


def href_for(target: str) -> str:
    if target.startswith("@"):
        return "../start-here.html#" + target[1:]
    return target + ".html"


def target_label(target: str, manifest: dict, facts: dict[str, PageFacts], override: str | None = None) -> str:
    if override:
        return override
    if target.startswith("@"):
        return manifest["start_targets"][target[1:]]["label"]
    return facts[target].h1[0]


def render_link(target: str, label: str, rel: str | None = None, extra_class: str = "") -> str:
    href = html.escape(href_for(target), quote=True)
    safe_label = html.escape(label, quote=False)
    rel_attr = f' rel="{html.escape(rel, quote=True)}"' if rel else ""
    class_attr = f' class="{html.escape(extra_class, quote=True)}"' if extra_class else ""
    return f'<a href="{href}"{rel_attr}{class_attr}>{safe_label}</a>'


def render_card(target: str, small: str, strong: str, reason: str | None = None,
                rel: str | None = None) -> str:
    """Render only trusted fixed markup; escape all manifest/title text and attributes."""
    href = html.escape(href_for(target), quote=True)
    rel_attr = f' rel="{html.escape(rel, quote=True)}"' if rel else ""
    body = (f'<small>{html.escape(small, quote=False)}</small>'
            f'<strong>{html.escape(strong, quote=False)}</strong>')
    if reason:
        body += f'<span>{html.escape(reason, quote=False)}</span>'
    return f'<a href="{href}"{rel_attr} class="reader-path-card">{body}</a>'


def render_toolbar(key: str, item: dict, manifest: dict, facts: dict[str, PageFacts]) -> str:
    previous = item.get("previous")
    if previous:
        label = target_label(previous, manifest, facts)
        if previous.startswith("@"):
            prev_link = render_link(previous, "← " + label)
        else:
            prev_link = render_link(previous, "← Prerequisite: " + label, "prev")
    else:
        prev_link = render_link("@sh-routes", "← Choose a learning path")
    next_edges = item.get("next", [])
    if len(next_edges) > 1:
        next_links = '<a href="#reader-course-navigation">Choose a next step ↓</a>'
    elif next_edges:
        edge = next_edges[0]
        target = edge["target"]
        label = edge.get("label") or ("Explore: " + target_label(target, manifest, facts))
        next_links = render_link(target, label, "next")
    else:
        next_links = render_link("@sh-routes", "Choose another path →")
    return ('<nav aria-label="Learning path navigation" class="reader-toolbar">'
            + prev_link + '<a data-catalogue-return="" href="../tutorials.html">All tutorials</a>'
            + next_links + '</nav>')


def render_continuation(key: str, item: dict, manifest: dict, facts: dict[str, PageFacts]) -> str:
    route = html.escape(item["route"], quote=False)
    sequence = [f'<nav aria-label="Learning path continuation" class="reader-sequence" id="reader-course-navigation">',
                '<h2>Choose a relevant next step</h2>',
                f'<p class="reader-sequence-position"><strong>Learning route:</strong> {route}. Suggested links are not a completion tracker or a required linear course.</p>',
                '<div class="reader-sequence-grid">']
    previous = item.get("previous")
    if previous:
        label = "← " + target_label(previous, manifest, facts)
        sequence.append(render_card(previous, "Relevant prerequisite / back to path", label, rel="prev"))
    else:
        sequence.append(render_card("@sh-routes", "Start Here", "Choose a learning path"))
    sequence.append('<a data-catalogue-return="" href="../tutorials.html"><small>Tutorial library</small><strong>All tutorials</strong></a>')
    for edge in item.get("next", []):
        target = edge["target"]
        label = target_label(target, manifest, facts, edge.get("label"))
        sequence.append(render_card(target, "Suggested next step", label, edge["reason"], "next"))
    sequence.append('</div></nav>')
    return '\n'.join(sequence)


def replace_one(text: str, pattern: re.Pattern[str], replacement: str, page: str, name: str) -> str:
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"tutorials/{page}: expected exactly one {name} nav block; found {len(matches)}")
    match = matches[0]
    return text[:match.start()] + replacement + text[match.end():]


def render_page(key: str, source: str, manifest: dict, facts: dict[str, PageFacts]) -> str:
    item = manifest["tutorials"][key]
    rendered = replace_one(source, NAV_PATTERNS["toolbar"], render_toolbar(key, item, manifest, facts), key + ".html", "reader-toolbar")
    return replace_one(rendered, NAV_PATTERNS["continuation"], render_continuation(key, item, manifest, facts), key + ".html", "reader-course-navigation")


def validate_generated_links(root: Path, key: str, output: str, manifest: dict) -> None:
    """Validate local hrefs emitted in the two generated navs, including anchors."""
    navs = [pattern.search(output) for pattern in NAV_PATTERNS.values()]
    if any(match is None for match in navs):
        raise ValueError(f"tutorials/{key}.html: generated navigation block missing")
    for match in navs:
        parser = PageFacts('')
        # A focused attribute parser avoids parsing/rewriting the rest of the page.
        class Links(HTMLParser):
            def __init__(self):
                super().__init__(); self.hrefs = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    attrs = dict(attrs)
                    if attrs.get('href') is not None: self.hrefs.append(attrs['href'])
        links = Links(); links.feed(match.group(0))
        for href in links.hrefs:
            if href == "../tutorials.html":
                if not (root / "tutorials.html").is_file():
                    raise ValueError("Generated catalogue link has no tutorials.html target")
                continue
            if href == "#reader-course-navigation":
                if 'id="reader-course-navigation"' not in output:
                    raise ValueError("Generated next-step jump has no continuation target")
                continue
            if href.startswith("../start-here.html#"):
                anchor = href.split("#", 1)[1]
                if anchor not in manifest["start_targets"]:
                    raise ValueError(f"Generated link references unknown Start Here anchor #{anchor}")
                continue
            target = root / "tutorials" / href
            if not target.is_file():
                raise ValueError(f"tutorials/{key}.html: generated link target missing: {href}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="site root (defaults to repository root)")
    parser.add_argument("--check", action="store_true", help="validate and report stale pages without writing")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        manifest, facts = load_site(root)
        changed: list[str] = []
        for key in sorted(facts):
            page = root / "tutorials" / f"{key}.html"
            original = page.read_text(encoding="utf-8")
            generated = render_page(key, original, manifest, facts)
            validate_generated_links(root, key, generated, manifest)
            if generated != original:
                changed.append(key)
                if not args.check:
                    page.write_text(generated, encoding="utf-8", newline="")
        if args.check:
            if changed:
                print(f"Learning-path navigation is stale in {len(changed)} tutorial pages: " + ", ".join(changed))
                return 1
            print(f"Learning-path navigation is current across {len(facts)} tutorials.")
            return 0
        print(f"Generated learning-path navigation in {len(changed)} tutorial pages (of {len(facts)}).")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"learning-path generator: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
