#!/usr/bin/env python3
"""Validate reviewed code metadata and wire local tutorial UI assets, never rewriting articles.

Run after generate_learning_paths.py. --check never writes.
"""
from __future__ import annotations
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261025-r-first-v1'
NAVIGATION_CSS_VERSION = '20261025-learning-navigation-v2'
CODE_DATA_VERSION = '20261025-executed-examples-v1'
STARTUP_VERSION = '20261026-startup-v1'
LANGUAGES = {'bash', 'python', 'r', 'text', 'yaml', 'json', 'csv', 'diff', 'powershell', 'lua', 'groovy', 'javascript', 'markdown', 'sql', 'ini', 'docker', 'rscript'}
TAB_ORDER = ['r', 'python']
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

class ArticleFacts(HTMLParser):
    """Minimal read-only textContent inventory. The original HTML is never serialized."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.nodes = []
        self.blocks = []
        self.in_pre = False
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        if tag == 'article' and not self.depth:
            self.depth = 1
            return
        if not self.depth: return
        if self.depth == 1: self.nodes.append({'tag': tag, 'text': ''})
        if tag == 'pre':
            self.in_pre = True
            self.blocks.append('')
        if tag not in VOID: self.depth += 1
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if not self.depth: return
        if tag == 'pre': self.in_pre = False
        if tag not in VOID: self.depth -= 1
    def handle_data(self, data):
        if self.depth > 1 and self.nodes: self.nodes[-1]['text'] += data
        if self.in_pre: self.blocks[-1] += data

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def load_metadata(root):
    languages = json.loads((root / 'tools/tutorial-code-languages.json').read_text())
    groups = json.loads((root / 'tools/tutorial-code-groups.json').read_text())
    if languages.get('schema') != 1 or groups.get('schema') != 1: raise ValueError('Unsupported UI metadata schema')
    pages = sorted(
        page for page in (root / 'tutorials').glob('*.html')
        if '<meta name="tutorial-route-redirect"' not in page.read_text(encoding='utf-8')
    )
    if len(pages) != 58 or {p.stem for p in pages} != set(languages['tutorials']):
        raise ValueError('UI metadata must cover exactly the 58 public tutorials')
    if not set(groups['tutorials']).issubset(languages['tutorials']): raise ValueError('Unknown grouped tutorial')
    result = {'schema': 1, 'tutorials': {}}
    for page in pages:
        facts = ArticleFacts(page.read_text())
        spec = languages['tutorials'][page.stem]
        if len(facts.blocks) != len(spec['blocks']): raise ValueError(f'{page.name}: code-block count changed')
        for index, (text, block) in enumerate(zip(facts.blocks, spec['blocks'])):
            if block['language'] not in LANGUAGES: raise ValueError(f'{page.name}: unsupported language {block["language"]}')
            if sha(text) != block['sha256']: raise ValueError(f'{page.name}: code {index} fingerprint changed; review its UI metadata')
        paired = groups['tutorials'].get(page.stem, [])
        occupied = set()
        for group in paired:
            panels = group['panels']
            if group.get('tabOrder') != TAB_ORDER:
                raise ValueError(f'{page.name}: language tabs must be ordered R then Python')
            if {p['language'] for p in panels} != {'r', 'python'} or len(panels) != 2:
                raise ValueError(f'{page.name}: expected one R and one Python route')
            start, end = panels[0]['start'], panels[-1]['end']
            if panels[0]['end'] + 1 != panels[1]['start'] or start > end:
                raise ValueError(f'{page.name}: language routes must form one contiguous section')
            if occupied.intersection(range(start, end + 1)): raise ValueError(f'{page.name}: overlapping groups')
            occupied.update(range(start, end + 1))
            if [m['index'] for m in group['members']] != list(range(start, end + 1)):
                raise ValueError(f'{page.name}: incomplete group fingerprints')
            for member in group['members']:
                node = facts.nodes[member['index']]
                if node['tag'] != member['tag'] or sha(node['text']) != member['sha256']:
                    raise ValueError(f'{page.name}: group boundary/content changed; leave both routes visible until reviewed')
        result['tutorials'][page.stem] = {**spec, 'groups': paired}
    return result

CSS = (f'<link href="../tutorial-reader.css?v={VERSION}" rel="stylesheet"/>\n'
       f'<link href="../tutorial-navigation.css?v={NAVIGATION_CSS_VERSION}" rel="stylesheet"/>\n'
       f'<link href="../back-to-top.css?v={VERSION}" rel="stylesheet"/>')
PRISM_LINK = re.compile(r'<link\b[^>]*href="https://cdnjs.cloudflare.com/ajax/libs/prism/1\.29\.0/themes/prism-tomorrow\.min\.css"[^>]*/>')
PRISM_SCRIPT = re.compile(r'<script\b[^>]*src="https://cdnjs.cloudflare.com/ajax/libs/prism/1\.29\.0/[^\"]+"[^>]*></script>\n?')
TOP_START = '<!-- Tutorial top link -->'
TOP_END = '<!-- /Tutorial top link -->'

def top_link(title):
    return (TOP_START + '\n<div class="reader-tools tutorial-top-tools">'
            '<a id="back-to-top" href="#tutorial-title" aria-label="Back to top">'
            '<span class="tutorial-top-icon" aria-hidden="true">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M12 19V5m-6 6 6-6 6 6"/></svg></span>'
            '<span>Back to top<small>' + escape(title) + '</small></span></a></div>\n' + TOP_END + '\n')

def render_page(source, metadata, slug):
    output = PRISM_LINK.sub('', source)
    output = PRISM_SCRIPT.sub('', output)
    # Keep every reviewed comparison, but ship only this lesson's metadata.
    # Escaping '<' prevents metadata text from closing its generated script.
    payload = {'schema': metadata['schema'], 'tutorials': {slug: metadata['tutorials'][slug]}}
    encoded = json.dumps(payload, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    scripts = ('<script src="../assets/vendor/prism/prism-1.29.0.js"></script>\n'
               '<script id="tutorial-code-data">\nwindow.OMICS_TUTORIAL_CODE = ' + encoded + ';\n</script>\n'
               f'<script src="../code-tabs.js?v={STARTUP_VERSION}"></script>')
    output = re.sub(r'((?:href|src)="\.\./(?:tutorial-(?:reader|navigation)\.css|back-to-top\.css|tutorial-code-data\.js|code-tabs\.js))(?:\?[^\"]*)?(\")',
                    lambda match: match.group(1) + '?v=' + (NAVIGATION_CSS_VERSION if 'tutorial-navigation.css' in match.group(1) else CODE_DATA_VERSION if 'tutorial-code-data.js' in match.group(1) else VERSION) + match.group(2), output)
    for include in CSS.splitlines():
        if include not in output: output = output.replace('</head>', include + '\n</head>', 1)
    marker = '__OMICS_REVIEWED_TUTORIAL_SCRIPTS__'
    output, count = re.subn(r'<script\b[^>]*src="\.\./code-tabs\.js(?:\?[^\"]*)?"[^>]*></script>', marker, output)
    if count != 1: raise ValueError('Expected one code-tabs script')
    output = re.sub(r'<script\b[^>]*src="\.\./(?:assets/vendor/prism/prism-1\.29\.0|tutorial-code-data)\.js(?:\?[^\"]*)?"[^>]*></script>\n?', '', output)
    output = re.sub(r'<script id="tutorial-code-data">.*?</script>\n?', '', output, flags=re.S)
    output = output.replace(marker, scripts, 1)
    # Static articles already own rendering, native routes and Legal behavior.
    # Reuse the small menu-dismissal helper instead of downloading the SPA bundle.
    output, count = re.subn(r'<script\b[^>]*src="\.\./(?:script|mobile-navigation)\.js(?:\?[^\"]*)?"[^>]*></script>',
                           f'<script defer="" src="../mobile-navigation.js?v={STARTUP_VERSION}"></script>', output)
    if count != 1: raise ValueError('Expected one static-page navigation helper')
    for name in ['copy-code', 'subscribe-fab']:
        version = STARTUP_VERSION if name == 'subscribe-fab' else VERSION
        output, count = re.subn(r'<script\b[^>]*src="\.\./' + name + r'\.js(?:\?[^\"]*)?"[^>]*></script>',
                               f'<script src="../{name}.js?v={version}"></script>', output)
        if count != 1: raise ValueError(f'Expected one {name} script')
    title_match = re.search(r'<h1\b[^>]*>(.*?)</h1>', output, re.S)
    if not title_match: raise ValueError('Missing tutorial title')
    title = re.sub('<[^>]*>', '', title_match.group(1))
    from html import unescape
    title = unescape(title)
    if TOP_START in output:
        output, count = re.subn(re.escape(TOP_START) + r'.*?' + re.escape(TOP_END) + r'\n?', lambda _: top_link(title), output, flags=re.S)
        if count != 1: raise ValueError('Expected one tutorial top link')
    else:
        output, count = re.subn(r'(?=<footer\b)', lambda _: top_link(title), output, count=1)
        if count != 1: raise ValueError('Missing tutorial footer')
    return output

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        metadata = load_metadata(root)
        data = ('/* Generated by tools/generate_tutorial_ui.py. Do not edit. */\n'
                'window.OMICS_TUTORIAL_CODE = ' + json.dumps(metadata, ensure_ascii=False, separators=(',', ':')) + ';\n')
        changes = []
        outputs = {root / 'tutorial-code-data.js': data}
        for page in sorted((root / 'tutorials').glob('*.html')):
            if '<meta name="tutorial-route-redirect"' in page.read_text(encoding='utf-8'):
                continue
            outputs[page] = render_page(page.read_text(), metadata, page.stem)
        for path, text in outputs.items():
            if not path.exists() or path.read_text() != text:
                changes.append(str(path.relative_to(root)))
                if not args.check: path.write_text(text, encoding='utf-8', newline='')
        if args.check and changes:
            print('Tutorial UI assets are stale: ' + ', '.join(changes))
            return 1
        count = sum(len(s['blocks']) for s in metadata['tutorials'].values())
        grouped = sum(len(s['groups']) for s in metadata['tutorials'].values())
        print(f'Tutorial UI: 58 pages, {count} fingerprinted code blocks, {grouped} reviewed language groups; {len(changes)} files {"stale" if args.check else "updated"}.')
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        print(f'tutorial-ui generator: {error}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
