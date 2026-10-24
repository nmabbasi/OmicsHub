#!/usr/bin/env python3
"""Apply reviewed learning metadata to catalogue cards; never modify lesson pages.

--check validates the evidence and generated HTML without writing either file.
"""
from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / 'tutorials.html'
DATA_PATH = ROOT / 'tools/catalogue-learning.json'
CARD_RE = re.compile(r'<article\b(?=[^>]*\bnative-tutorial-card\b)[\s\S]*?</article>', re.I)
LEVELS = {'beginner', 'intermediate', 'advanced'}
FORMATS = {'hands-on-lab', 'conceptual-guide', 'advanced-template', 'reference'}


def normalize(text: str) -> str:
    return ' '.join(html.unescape(text).split())


class VisibleText(HTMLParser):
    def __init__(self, markup: str):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.headings: list[str] = []
        self.heading: list[str] | None = None
        self.skipped = 0
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}:
            self.skipped += 1
        if not self.skipped and tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.heading = []

    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.skipped:
            self.skipped -= 1
        if self.heading is not None and tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.headings.append(normalize(' '.join(self.heading)))
            self.heading = None

    def handle_data(self, data):
        if not self.skipped:
            self.chunks.append(data)
            if self.heading is not None:
                self.heading.append(data)

    @property
    def text(self):
        return normalize(' '.join(self.chunks))


def get_attr(tag: str, name: str) -> str | None:
    match = re.search(r'\b' + re.escape(name) + r'\s*=\s*([\'"])(.*?)\1', tag, re.I | re.S)
    return html.unescape(match.group(2)) if match else None


def set_attr(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(r'(\b' + re.escape(name) + r'\s*=\s*)([\'"])(.*?)\2', re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(lambda m: m.group(1) + m.group(2) + escaped + m.group(2), tag, count=1)
    return tag[:-1] + f' {name}="{escaped}">'


def load_metadata() -> dict:
    data = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    if data.get('schemaVersion') != 1 or not isinstance(data.get('lessons'), dict):
        raise ValueError('Expected catalogue metadata schemaVersion 1 and a lesson mapping')
    metadata = data['lessons']
    expected = {p.stem for p in (ROOT / 'tutorials').glob('*.html')}
    if len(expected) != 58 or set(metadata) != expected:
        raise ValueError('Metadata must cover exactly the same 58 published lessons')
    for slug, item in metadata.items():
        if item.get('level') not in LEVELS or item.get('lessonPath') != f'tutorials/{slug}.html':
            raise ValueError(f'Invalid level or lesson source for {slug}')
        summary = item.get('prerequisiteSummary', '')
        if not 8 <= len(summary.split()) <= 45 or '\u2014' in summary or '<' in summary:
            raise ValueError(f'Prerequisite summary must be concise, plain text, and contain no em dash: {slug}')
        source = (ROOT / item['lessonPath']).read_text(encoding='utf-8')
        article = re.search(r'<article\b[^>]*>(.*?)</article>', source, re.S | re.I)
        if not article:
            raise ValueError(f'Actual lesson article is missing: {slug}')
        visible = VisibleText(article.group(1))
        excerpt = normalize(item.get('sourceExcerpt', ''))
        heading = normalize(item.get('sourceHeading', ''))
        if len(excerpt) < 36 or excerpt not in visible.text:
            raise ValueError(f'Evidence must quote the actual visible lesson body: {slug}')
        if heading not in visible.headings:
            raise ValueError(f'Evidence heading does not exist in the lesson body: {slug}: {heading!r}')
    return metadata


def enrich(card: str, metadata: dict) -> tuple[str, str]:
    end = card.find('>')
    opening = card[:end + 1]
    href_match = re.search(r'<a\b[^>]*href=[\'"](tutorials/[^\'"]+\.html)[\'"]', card, re.I)
    if not href_match:
        raise ValueError('Catalogue card lacks a local tutorial destination')
    slug = Path(html.unescape(href_match.group(1))).stem
    item = metadata[slug]
    format_tag = re.search(r'<span\b[^>]*data-tutorial-format[^>]*>', card, re.I)
    learning_format = get_attr(format_tag.group(0), 'data-tutorial-format') if format_tag else None
    if learning_format not in FORMATS:
        raise ValueError(f'No supported existing learning-format label: {slug}')
    opening = set_attr(opening, 'data-level', item['level'])
    opening = set_attr(opening, 'data-format', learning_format)
    base_search = get_attr(opening, 'data-search-base')
    if base_search is None:
        base_search = get_attr(opening, 'data-search') or ''
        opening = set_attr(opening, 'data-search-base', base_search)
    opening = set_attr(opening, 'data-search', base_search)
    card = opening + card[end + 1:]
    card = re.sub(r'\s*<span class="hc-card-level"[^>]*>.*?</span>', '', card, flags=re.I | re.S)
    card = re.sub(r'\s*<div class="hc-card-prerequisite"[^>]*>.*?</div>', '', card, flags=re.I | re.S)
    paragraph = re.search(r'<p\b[^>]*>.*?</p>', card, re.I | re.S)
    if not paragraph:
        raise ValueError(f'No original description paragraph found: {slug}')
    heading = re.search(r'<h3\b[^>]*>(.*?)</h3>', card, re.I | re.S)
    if not heading:
        raise ValueError(f'No original lesson title found: {slug}')
    title = re.sub(r'</?a\b[^>]*>', '', heading.group(1), flags=re.I)
    card = re.sub(r'\s*<a\b[^>]*class="[^"]*\bhc-card-link\b[^"]*"[^>]*>.*?</a>', '', card, flags=re.I | re.S)
    destination = html.escape(item['lessonPath'], quote=True)
    card = re.sub(r'(<h3\b[^>]*>).*?(</h3>)',
                  lambda match: match.group(1) + f'<a class="hc-card-link" href="{destination}">' + title + '</a>' + match.group(2),
                  card, count=1, flags=re.I | re.S)
    return card, slug


def render(document: str, metadata: dict) -> str:
    found: list[str] = []

    def replace(match):
        card, slug = enrich(match.group(0), metadata)
        found.append(slug)
        return card

    updated, count = CARD_RE.subn(replace, document)
    if count != 58 or len(set(found)) != 58 or set(found) != set(metadata):
        raise ValueError('Expected 58 unique catalogue cards matching the reviewed metadata')
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without writing generated HTML')
    args = parser.parse_args()
    try:
        metadata = load_metadata()
        document = HTML_PATH.read_text(encoding='utf-8')
        updated = render(document, metadata)
        if args.check and updated != document:
            print('Catalogue metadata hooks are stale. Run python3 tools/generate_catalogue_learning.py')
            return 1
        if not args.check and updated != document:
            HTML_PATH.write_text(updated, encoding='utf-8')
        print('Verified 58 evidence-backed catalogue cards.' if args.check else 'Generated 58 evidence-backed catalogue cards.')
        return 0
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f'Catalogue metadata error: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
