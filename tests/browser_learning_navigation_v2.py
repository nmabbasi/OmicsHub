#!/usr/bin/env python3
"""Local-only responsive checks and review captures for learning navigation."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
from route_migration_baseline import published_tutorial_paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:8767')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {'checks': [], 'errors': []}
    pages = published_tutorial_paths(ROOT)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=2)
        context.route('https://**/*', lambda route: route.abort())
        page = context.new_page()
        page.on('pageerror', lambda err: report['errors'].append(str(err)))
        for width in [1440, 768, 390, 320]:
            page.set_viewport_size({'width': width, 'height': 1000})
            for source in pages:
                page.goto(f'{args.base}/tutorials/{source.name}', wait_until='load')
                page.wait_for_selector('html[data-tutorial-code-ready="true"]')
                page.evaluate('document.fonts.ready')
                data = page.evaluate('''() => {
                  const rect = e => { const r=e.getBoundingClientRect(); return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}; };
                  return {width:innerWidth,scroll:document.documentElement.scrollWidth,
                    links:[...document.querySelectorAll('.reader-toolbar > a, #reader-course-navigation .reader-path-card')].map(rect),
                    top:[...document.querySelectorAll('.reader-toolbar > a')].map(rect),
                    colors:[...document.querySelectorAll('.reader-path-card__title')].map(e=>getComputedStyle(e).color)};
                }''')
                assert data['scroll'] <= width + 1, (source.name, width, 'overflow', data)
                assert all(r['h'] >= 43.99 for r in data['links']), (source.name, width, 'small target', data['links'])
                assert all(r['x'] >= -1 and r['right'] <= width + 1 for r in data['links']), (source.name, width, 'clipped navigation')
                for i, a in enumerate(data['top']):
                    for b in data['top'][i+1:]:
                        assert not (min(a['right'],b['right'])-max(a['x'],b['x']) > 1 and min(a['bottom'],b['bottom'])-max(a['y'],b['y']) > 1), (source.name, width, 'overlap')
                report['checks'].append({'page': source.name, 'width': width, 'targets': len(data['links'])})
            print(f'Navigation checked: 58 tutorials at {width}px', flush=True)
        for width, device in [(1440, 'desktop'), (390, 'mobile')]:
            page.set_viewport_size({'width': width, 'height': 1000})
            page.goto(f'{args.base}/tutorials/data-visualization-fundamentals.html', wait_until='load')
            page.wait_for_selector('html[data-tutorial-code-ready="true"]')
            banner = page.get_by_role('button', name='Decline analytics', exact=True)
            if banner.is_visible():
                banner.click()
            page.locator('.reader-toolbar').screenshot(path=str(args.output / f'{device}-entry-navigation.png'))
            page.locator('#reader-course-navigation').screenshot(path=str(args.output / f'{device}-keep-exploring.png'))
            page.locator('#reader-course-navigation').evaluate("e=>scrollTo({top:scrollY+e.getBoundingClientRect().top-110,behavior:'instant'})")
            page.screenshot(path=str(args.output / f'{device}-navigation-context.png'))
        # Real native navigation and keyboard focus, not only markup inspection.
        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto(f'{args.base}/tutorials/command-line-part1.html', wait_until='load')
        page.locator('.reader-toolbar__next').click()
        page.wait_for_url('**/command-line-part2.html')
        page.locator('.reader-toolbar__previous').click()
        page.wait_for_url('**/command-line-part1.html')
        page.locator('.reader-toolbar__library').focus()
        assert page.locator('.reader-toolbar__library').evaluate("e=>getComputedStyle(e).outlineStyle") == 'solid'
        page.goto(f'{args.base}/tutorials/statistics-for-bioinformatics.html', wait_until='load')
        page.locator('.reader-toolbar__next').click()
        assert page.url.endswith('#reader-course-navigation')
        report['interactions'] = ['native next and previous', 'visible keyboard focus', 'branch anchor jump']
        browser.close()
    assert not report['errors'], report['errors']
    (args.output / 'navigation-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(report["checks"])} responsive page checks, native links, focus and branch navigation', flush=True)


if __name__ == '__main__':
    main()
