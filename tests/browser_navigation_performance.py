#!/usr/bin/env python3
"""Read-only browser regression coverage for tutorial navigation and dependency removal.

The script serves the checked-out site from an ephemeral localhost server, blocks
all third-party requests, and never executes tutorial examples. A request for the
exact legacy Marked CDN script is held unresolved for 15 seconds (or until cleanup
aborts it); document-ready and code-ready each have a 10-second bound.

Usage:
  python3 tests/browser_navigation_performance.py \
    --output /workspace/website-review/navigation-performance-20261025/browser-performance.json

Pass --browser '' to use Playwright's installed Chromium instead of /usr/bin/chromium.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import sys
import threading
import time
from urllib.parse import urlsplit

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path('/workspace/website-review/navigation-performance-20261025/browser-performance.json')
MARKED_HOST = 'cdn.jsdelivr.net'
MARKED_PATH = '/npm/marked/marked.min.js'
MARKED_HOLD_SECONDS = 15.0
READY_TIMEOUT_MS = 10_000

INIT_SCRIPT = r"""(() => {
  window.__navPerf = {dclMs: null, codeReadyMs: null};
  document.addEventListener('DOMContentLoaded', () => {
    window.__navPerf.dclMs = performance.now();
  }, {once: true});
  document.addEventListener('tutorial-code-ready', () => {
    window.__navPerf.codeReadyMs = performance.now();
  }, {once: true});
})();"""


class QuietStaticHandler(SimpleHTTPRequestHandler):
    """Static file server restricted to read-only GETs and quiet logs."""

    def do_GET(self):
        super().do_GET()

    def do_POST(self):
        self.send_error(405, 'Read-only test server')

    def do_PUT(self):
        self.send_error(405, 'Read-only test server')

    def do_DELETE(self):
        self.send_error(405, 'Read-only test server')

    def log_message(self, *_args):
        pass


class Regression:
    def __init__(self, args, base, browser):
        self.args = args
        self.base = base.rstrip('/') + '/'
        self.browser = browser
        self.output = args.output
        self.log_path = self.output.with_suffix('.log')
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.results = {
            'test': 'browser_navigation_performance',
            'root': str(ROOT),
            'base_url': self.base,
            'marked_simulation': {
                'url': f'https://{MARKED_HOST}{MARKED_PATH}',
                'unresponsive_hold_seconds': MARKED_HOLD_SECONDS,
                'document_content_loaded_timeout_ms': READY_TIMEOUT_MS,
                'code_ready_timeout_ms': READY_TIMEOUT_MS,
            },
            'pages': [],
            'cpu_throttled_checks': [],
            'navigation_cases': [],
            'marked_requests': [],
            'blocked_external_hosts': {},
            'errors': [],
            'console_errors': [],
            'progress': [],
            'passed': False,
        }
        self.blocked_hosts = Counter()
        self.held_marked = []
        self.page_labels = {}
        self.log_path.write_text('', encoding='utf-8')

    def log(self, message):
        stamp = time.strftime('%H:%M:%S')
        line = f'[{stamp}] {message}'
        print(line, flush=True)
        with self.log_path.open('a', encoding='utf-8') as stream:
            stream.write(line + '\n')
        self.results['progress'].append(line)

    def check(self, condition, message):
        if not condition:
            raise AssertionError(message)

    @staticmethod
    def is_marked(url):
        parsed = urlsplit(url)
        return parsed.scheme == 'https' and parsed.hostname == MARKED_HOST and parsed.path == MARKED_PATH

    async def route_request(self, route):
        request = route.request
        parsed = urlsplit(request.url)
        if self.is_marked(request.url):
            record = {
                'url': request.url,
                'method': request.method,
                'requested_at_monotonic': time.monotonic(),
                'configured_unresponsive_hold_seconds': MARKED_HOLD_SECONDS,
                'aborted_during_cleanup': False,
            }
            self.results['marked_requests'].append(record)
            release = asyncio.Event()
            held = {'route': route, 'release': release, 'record': record, 'abort': False}
            self.held_marked.append(held)
            try:
                # Do not sleep synchronously: other localhost scripts and page
                # readiness continue loading while this classic-script fetch hangs.
                try:
                    await asyncio.wait_for(release.wait(), timeout=MARKED_HOLD_SECONDS)
                except asyncio.TimeoutError:
                    pass  # The simulated outage expires by aborting below.
                if held['abort']:
                    record['aborted_during_cleanup'] = True
                    record['actual_hold_ms'] = round((time.monotonic() - record['requested_at_monotonic']) * 1000, 3)
                    await route.abort('aborted')
                else:
                    # The 15-second fault injection expires by aborting, never by
                    # allowing this network request to reach the internet.
                    record['hold_expired_and_aborted'] = True
                    record['actual_hold_ms'] = round((time.monotonic() - record['requested_at_monotonic']) * 1000, 3)
                    await route.abort('timedout')
            except Exception as exc:
                record['route_error'] = str(exc)
            return

        if parsed.hostname in {'127.0.0.1', 'localhost'}:
            if request.method != 'GET':
                await route.abort('blockedbyclient')
                raise AssertionError(f'Non-GET localhost request blocked: {request.method} {request.url}')
            await route.continue_()
            return

        self.blocked_hosts[parsed.hostname or '(unknown)'] += 1
        await route.abort('blockedbyclient')

    async def configure_context(self, context):
        await context.add_init_script(INIT_SCRIPT)
        await context.route('**/*', self.route_request)

    def record_page_errors(self, page, slug):
        if page in self.page_labels:
            self.page_labels[page] = slug
            return
        self.page_labels[page] = slug
        page.on('pageerror', lambda error: self.results['errors'].append({'slug': self.page_labels[page], 'type': 'pageerror', 'message': str(error)}))
        # Keep browser console diagnostics, including expected blocked-resource
        # messages, without treating network-policy noise as a page regression.
        page.on('console', lambda message: self.results['console_errors'].append({'slug': self.page_labels[page], 'message': message.text}) if message.type == 'error' else None)

    async def open_lesson(self, page, slug, *, cpu_rate=None):
        if cpu_rate is not None:
            cdp = await page.context.new_cdp_session(page)
            await cdp.send('Emulation.setCPUThrottlingRate', {'rate': cpu_rate})
        url = f'{self.base}tutorials/{slug}.html'
        self.record_page_errors(page, slug)
        response = await page.goto(url, wait_until='commit', timeout=READY_TIMEOUT_MS)
        self.check(response is not None and response.ok, f'{slug}: local lesson request failed')
        # Two independent bounded gates make a newly reintroduced classic script
        # fail as soon as it blocks parsing/DCL, before code-ready can be delayed.
        await page.wait_for_function("document.readyState === 'interactive' || document.readyState === 'complete'", timeout=READY_TIMEOUT_MS)
        dcl_task = page.wait_for_function("window.__navPerf?.dclMs !== null", timeout=READY_TIMEOUT_MS)
        ready_task = page.wait_for_selector('html[data-tutorial-code-ready="true"]', timeout=READY_TIMEOUT_MS)
        await asyncio.gather(dcl_task, ready_task)

        data = await page.evaluate('''() => {
          const nav = performance.getEntriesByType('navigation')[0];
          const blocks = [...document.querySelectorAll('article pre')]
            .map(pre => ({index: Number(pre.dataset.codeSourceIndex), text: (pre.querySelector('code') || pre).textContent}))
            .sort((a, b) => a.index - b.index);
          return {
            url: location.href,
            timeOrigin: performance.timeOrigin,
            dclEventMs: window.__navPerf?.dclMs,
            codeReadyEventMs: window.__navPerf?.codeReadyMs,
            codeReadyObservedMs: performance.now(),
            navigation: nav ? {
              requestStartMs: nav.requestStart,
              responseStartMs: nav.responseStart,
              domInteractiveMs: nav.domInteractive,
              domContentLoadedMs: nav.domContentLoadedEventEnd,
              loadEventMs: nav.loadEventEnd
            } : null,
            blocks,
            frames: document.querySelectorAll('article .tutorial-code-frame').length,
            groups: document.querySelectorAll('[data-code-tabs]').length,
            groupLanguages: [...document.querySelectorAll('[data-code-tabs]')].map(group =>
              [...group.querySelectorAll('[role=tab]')].map(tab => tab.dataset.language)),
            selectedLanguages: [...document.querySelectorAll('[data-code-tabs]')].map(group =>
              group.querySelector('[role=tab][aria-selected=true]')?.dataset.language ?? null),
            visiblePanels: [...document.querySelectorAll('[data-code-tabs]')].map(group =>
              [...group.querySelectorAll('[role=tabpanel]')].filter(panel => !panel.hidden).length)
          };
        }''')
        self.check(data['dclEventMs'] is not None, f'{slug}: DOMContentLoaded timing was not recorded')
        self.check(data['codeReadyEventMs'] is not None, f'{slug}: tutorial-code-ready timing event was not recorded')
        self.check(data['timeOrigin'] > 0, f'{slug}: missing common performance.timeOrigin')
        return data

    def assert_page_metadata(self, slug, data, metadata, groups_metadata):
        spec = metadata[slug]
        blocks = data['blocks']
        actual_hashes = [hashlib.sha256(block['text'].encode('utf-8')).hexdigest() for block in blocks]
        expected_hashes = [block['sha256'] for block in spec['blocks']]
        self.check(actual_hashes == expected_hashes, f'{slug}: source code SHA-256 mismatch')
        self.check(data['frames'] == len(spec['blocks']), f'{slug}: expected {len(spec["blocks"])} copy frames, found {data["frames"]}')
        expected_groups = groups_metadata.get(slug, [])
        self.check(data['groups'] == len(expected_groups), f'{slug}: group count {data["groups"]} differs from metadata {len(expected_groups)}')
        if expected_groups:
            self.check(all(languages == ['r', 'python'] for languages in data['groupLanguages']), f'{slug}: configured groups must expose R then Python tabs')
            self.check(all(language == 'r' for language in data['selectedLanguages']), f'{slug}: configured groups did not default to R')
            self.check(all(count == 1 for count in data['visiblePanels']), f'{slug}: configured group has invalid visible-panel count')
        return actual_hashes

    async def run_all_pages(self, context, metadata, groups_metadata):
        page = await context.new_page()
        for index, (slug, spec) in enumerate(metadata.items(), start=1):
            self.log(f'Page {index}/{len(metadata)}: {slug}')
            data = await self.open_lesson(page, slug)
            hashes = self.assert_page_metadata(slug, data, metadata, groups_metadata)
            self.results['pages'].append({
                'slug': slug,
                'blocks': len(hashes),
                'groups': data['groups'],
                'time_origin': data['timeOrigin'],
                'navigation_request_start_ms': data['navigation']['requestStartMs'] if data['navigation'] else None,
                'navigation_response_start_ms': data['navigation']['responseStartMs'] if data['navigation'] else None,
                'navigation_dom_interactive_ms': data['navigation']['domInteractiveMs'] if data['navigation'] else None,
                'navigation_dom_content_loaded_ms': data['navigation']['domContentLoadedMs'] if data['navigation'] else None,
                'navigation_load_event_ms': data['navigation']['loadEventMs'] if data['navigation'] else None,
                'dom_content_loaded_event_ms': data['dclEventMs'],
                'code_ready_event_ms': data['codeReadyEventMs'],
                'code_ready_observed_ms': data['codeReadyObservedMs'],
            })
        await page.close()
        self.log(f'Validated {len(self.results["pages"])} of {len(metadata)} lesson pages and exact source hashes.')

    async def run_cpu_toggle(self, context, metadata, groups_metadata, slug):
        page = await context.new_page()
        self.log(f'6× CPU-throttled readiness and R/Python toggle: {slug}')
        data = await self.open_lesson(page, slug, cpu_rate=6)
        self.assert_page_metadata(slug, data, metadata, groups_metadata)
        self.check(data['groups'] > 0, f'{slug}: CPU toggle case needs configured language groups')
        group = page.locator('[data-code-tabs]').first
        initially_selected = await group.locator('[role=tab][aria-selected=true]').get_attribute('data-language')
        self.check(initially_selected in {'r', 'python'}, f'{slug}: initial language tab is not selected')
        python_tab = group.locator('[role=tab][data-language="python"]')
        r_tab = group.locator('[role=tab][data-language="r"]')
        self.check(await python_tab.count() == 1 and await r_tab.count() == 1, f'{slug}: missing R/Python tab control')
        await python_tab.click()
        await page.wait_for_function("document.querySelector('[data-code-tabs] [role=tab][data-language=python][aria-selected=true]') !== null", timeout=READY_TIMEOUT_MS)
        python_state = await group.evaluate("g => ({selected:g.querySelector('[role=tab][aria-selected=true]')?.dataset.language, visible:[...g.querySelectorAll('[role=tabpanel]')].filter(p=>!p.hidden).length})")
        self.check(python_state == {'selected': 'python', 'visible': 1}, f'{slug}: Python selection did not reveal exactly one panel')
        await r_tab.click()
        await page.wait_for_function("document.querySelector('[data-code-tabs] [role=tab][data-language=r][aria-selected=true]') !== null", timeout=READY_TIMEOUT_MS)
        reverted = await group.evaluate("g => ({selected:g.querySelector('[role=tab][aria-selected=true]')?.dataset.language, visible:[...g.querySelectorAll('[role=tabpanel]')].filter(p=>!p.hidden).length})")
        self.check(reverted == {'selected': 'r', 'visible': 1}, f'{slug}: R reversion did not reveal exactly one panel')
        self.results['cpu_throttled_checks'].append({
            'slug': slug,
            'cpu_throttle_rate': 6,
            'time_origin': data['timeOrigin'],
            'dom_content_loaded_ms': data['dclEventMs'],
            'code_ready_ms': data['codeReadyEventMs'],
            'initial_language': initially_selected,
            'python_toggle': python_state,
            'r_revert': reverted,
            'passed': True,
        })
        await page.close()

    async def wait_lesson_ready(self, page, label):
        await page.wait_for_selector('html[data-tutorial-code-ready="true"]', timeout=READY_TIMEOUT_MS)
        self.check(await page.locator('article pre').count() > 0, f'{label}: lesson code absent after native navigation')

    async def run_navigation_path(self, context):
        page = await context.new_page()
        self.log('Native next → catalogue → browser back/back/forward path.')
        await self.open_lesson(page, 'command-line-part1')
        start_url = page.url
        next_link = page.locator('#reader-course-navigation a[rel="next"]').first
        await next_link.click()
        await page.wait_for_url('**/tutorials/command-line-part2.html', timeout=READY_TIMEOUT_MS)
        await self.wait_lesson_ready(page, 'next lesson')
        next_url = page.url
        catalogue = page.locator('#reader-course-navigation a[data-catalogue-return]')
        self.check(await catalogue.count() == 1, 'command-line-part1: native catalogue return link missing')
        # A direct local catalogue click only; no outside reference links are clicked.
        await catalogue.click()
        await page.wait_for_url('**/tutorials.html', timeout=READY_TIMEOUT_MS)
        await page.wait_for_load_state('domcontentloaded', timeout=READY_TIMEOUT_MS)
        self.check(await page.locator('body').inner_text() != '', 'catalogue returned an empty document')
        catalogue_url = page.url
        await page.go_back(wait_until='domcontentloaded', timeout=READY_TIMEOUT_MS)
        await self.wait_lesson_ready(page, 'back from catalogue')
        self.check(page.url == next_url, 'Browser back from catalogue did not restore command-line-part2')
        await page.go_back(wait_until='domcontentloaded', timeout=READY_TIMEOUT_MS)
        await self.wait_lesson_ready(page, 'back to first lesson')
        self.check(page.url == start_url, 'Second browser back did not restore command-line-part1')
        await page.go_forward(wait_until='domcontentloaded', timeout=READY_TIMEOUT_MS)
        await self.wait_lesson_ready(page, 'forward to next lesson')
        self.check(page.url == next_url, 'Browser forward did not restore command-line-part2')
        self.results['navigation_cases'].append({
            'path': ['command-line-part1', 'command-line-part2', 'tutorials.html', 'back:command-line-part2', 'back:command-line-part1', 'forward:command-line-part2'],
            'start_url': start_url,
            'next_url': next_url,
            'catalogue_url': catalogue_url,
            'passed': True,
        })
        await page.close()

    async def abort_held_marked(self):
        for held in self.held_marked:
            held['abort'] = True
            held['release'].set()
        # Give route handlers a chance to abort their held requests before context
        # and browser teardown; no third-party request is ever continued.
        if self.held_marked:
            await asyncio.sleep(0)


async def async_main(args):
    metadata_path = ROOT / 'tools/tutorial-code-languages.json'
    groups_path = ROOT / 'tools/tutorial-code-groups.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))['tutorials']
    groups_metadata = json.loads(groups_path.read_text(encoding='utf-8'))['tutorials']
    test = None
    browser = None
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietStaticHandler, directory=str(ROOT)))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True, name='tutorial-readonly-http')
    server_thread.start()
    base = f'http://127.0.0.1:{server.server_port}/'
    test = Regression(args, base, browser=None)
    try:
        async with async_playwright() as playwright:
            launch_options = {
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-background-networking',
                    '--dns-prefetch-disable',
                    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
                ],
            }
            if args.browser:
                launch_options['executable_path'] = args.browser
            browser = await playwright.chromium.launch(**launch_options)
            test.browser = browser
            context = await browser.new_context(viewport={'width': 1440, 'height': 1000}, service_workers='block')
            await test.configure_context(context)
            try:
                test.check(len(metadata) == 58, f'Expected 58 lesson metadata records, found {len(metadata)}')
                test.log(f'Starting local-only review against {len(metadata)} tutorial records.')
                await test.run_all_pages(context, metadata, groups_metadata)
                await test.run_cpu_toggle(context, metadata, groups_metadata, 'statistics-for-bioinformatics')
                await test.run_cpu_toggle(context, metadata, groups_metadata, 'data-visualization-fundamentals')
                await test.run_navigation_path(context)
                test.check(not test.results['marked_requests'], f'Unexpected legacy Marked CDN requests: {test.results["marked_requests"]}')
                test.check(not test.results['errors'], f'Browser errors were observed: {test.results["errors"]}')
                test.results['blocked_external_hosts'] = dict(test.blocked_hosts)
                test.results['passed'] = True
                test.log('PASS: all 58 lessons, 6× interactions, and native navigation checks completed; no Marked request observed.')
            finally:
                await test.abort_held_marked()
                test.results['blocked_external_hosts'] = dict(test.blocked_hosts)
                await context.close()
                await browser.close()
    except Exception as error:
        test.results['passed'] = False
        test.results['failure'] = f'{type(error).__name__}: {error}'
        test.results['errors'].append({'type': 'test_failure', 'message': test.results['failure']})
        test.results['blocked_external_hosts'] = dict(test.blocked_hosts)
        test.log(f'FAIL: {test.results["failure"]}')
        raise
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
        if test is not None:
            test.results['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
            test.output.write_text(json.dumps(test.results, indent=2) + '\n', encoding='utf-8')
            print(f'JSON evidence: {test.output}', flush=True)
            print(f'Run log: {test.log_path}', flush=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', default='/usr/bin/chromium', help='Chromium executable; pass an empty string to use Playwright-installed Chromium.')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT, help='Path to JSON evidence output (a sibling .log file is also written).')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        asyncio.run(async_main(args))
    except Exception:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
