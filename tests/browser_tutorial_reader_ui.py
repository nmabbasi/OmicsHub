#!/usr/bin/env python3
"""Real-browser regression checks, no scientific execution.

Run with a local static server on port 8767:
  python3 tests/browser_tutorial_reader_ui.py --output /tmp/omics-ui-check
Requires Playwright and Chromium; --browser defaults to the sandbox Chrome path.
Remote requests are blocked. Results/screenshots are private, outside the site.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', default='http://127.0.0.1:8767')
    ap.add_argument('--browser', default='/opt/google/chrome/chrome')
    ap.add_argument('--output', type=Path, default=Path('/tmp/omics-ui-check'))
    args = ap.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((ROOT / 'tools/tutorial-code-languages.json').read_text())['tutorials']
    groups = json.loads((ROOT / 'tools/tutorial-code-groups.json').read_text())['tutorials']
    results = {'pages': [], 'interactions': [], 'errors': []}
    def check(condition, message):
        if not condition: raise AssertionError(message)
    def configure(context):
        context.route('https://**/*', lambda route: route.abort())
    def ready(page, slug):
        page.goto(f'{args.base}/tutorials/{slug}.html', wait_until='load')
        page.wait_for_selector('html[data-tutorial-code-ready="true"]')
        page.evaluate('document.fonts.ready')
    try:
        with sync_playwright() as pw:
            launch = {'headless': True, 'args': ['--no-sandbox']}
            if args.browser: launch['executable_path'] = args.browser
            browser = pw.chromium.launch(**launch)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, permissions=['clipboard-read', 'clipboard-write'])
            configure(context); page = context.new_page()
            page.on('pageerror', lambda error: results['errors'].append(str(error)))
            for width in [1440, 768, 390, 320]:
                page.set_viewport_size({'width': width, 'height': 1000})
                for slug, spec in metadata.items():
                    ready(page, slug)
                    data = page.evaluate('''() => ({
                      width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
                      blocks:[...document.querySelectorAll('article pre')].map(pre=>({index:Number(pre.dataset.codeSourceIndex),text:(pre.querySelector('code')||pre).textContent})).sort((a,b)=>a.index-b.index).map(block=>block.text),
                      frames:document.querySelectorAll('article .tutorial-code-frame').length,
                      groups:document.querySelectorAll('[data-code-tabs]').length,
                      selected:[...document.querySelectorAll('[data-code-tabs]')].map(g=>g.querySelectorAll('[role=tab][aria-selected=true]').length),
                      tabLanguages:[...document.querySelectorAll('[data-code-tabs]')].map(g=>[...g.querySelectorAll('[role=tab]')].map(tab=>tab.dataset.language)),
                      selectedLanguages:[...document.querySelectorAll('[data-code-tabs]')].map(g=>g.querySelector('[role=tab][aria-selected=true]')?.dataset.language),
                      visible:[...document.querySelectorAll('[data-code-tabs]')].map(g=>[...g.querySelectorAll('[role=tabpanel]')].filter(p=>!p.hidden).length),
                      tokens:document.querySelectorAll('.token').length,
                      colors:[...document.querySelectorAll('.token')].map(t=>getComputedStyle(t).color).filter((v,i,a)=>a.indexOf(v)===i),
                      topCount:document.querySelectorAll('#back-to-top').length,
                      nav:[...document.querySelectorAll('.reader-toolbar > a')].map(a=>{const r=a.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}}),
                      topIntegrated:!!document.querySelector('#reader-course-navigation .reader-sequence-footer #back-to-top'),
                      continuation:[...document.querySelectorAll('#reader-course-navigation a')].filter(a=>a.getClientRects().length).map(a=>a.getBoundingClientRect().height),
                      codeBg:document.querySelector('article pre')?getComputedStyle(document.querySelector('article pre')).backgroundColor:null
                    })''')
                    hashes = [hashlib.sha256(code.encode()).hexdigest() for code in data['blocks']]
                    # Tabs move whole branches but retain the original route order.
                    check(hashes == [block['sha256'] for block in spec['blocks']], f'{slug} code changed at {width}')
                    check(data['scrollWidth'] <= width + 1, f'{slug} horizontal page overflow at {width}: {data["scrollWidth"]}')
                    check(data['frames'] == len(spec['blocks']), f'{slug} missing/duplicate copy frames')
                    check(data['groups'] == len(groups.get(slug, [])), f'{slug} unexpected grouping')
                    check(all(n == 1 for n in data['selected'] + data['visible']), f'{slug} invalid tab visibility')
                    check(all(languages == ['r', 'python'] for languages in data['tabLanguages']), f'{slug} tabs are not physically R-first')
                    check(all(language == 'r' for language in data['selectedLanguages']), f'{slug} did not default to R')
                    check(data['topCount'] == 1, f'{slug} duplicate/missing top control')
                    check(all(round(r['h']) >= 44 for r in data['nav']), f'{slug} small navigation target')
                    check(data['topIntegrated'], f'{slug} detached back-to-top control at {width}')
                    check(all(h >= 44 for h in data['continuation']), f'{slug} small continuation target at {width}')
                    for i, first in enumerate(data['nav']):
                        for second in data['nav'][i+1:]:
                            overlap = min(first['right'],second['right'])-max(first['x'],second['x']) > 1 and min(first['bottom'],second['bottom'])-max(first['y'],second['y']) > 1
                            check(not overlap, f'{slug} toolbar overlaps at {width}')
                    if spec['blocks']: check(data['codeBg'] == 'rgb(9, 12, 17)', f'{slug} code not black')
                    results['pages'].append({'slug': slug, 'width': width, 'blocks': len(hashes), 'groups': data['groups'], 'tokenColors': len(data['colors'])})
                print(f'Checked all 58 tutorials at {width}px', flush=True)
            page.set_viewport_size({'width': 1440, 'height': 1000})
            ready(page, 'statistics-for-bioinformatics')
            decline = page.get_by_role('button', name='Decline analytics', exact=True)
            if decline.is_visible(): decline.click()
            first = page.locator('[data-code-tabs]').first
            rtab = first.get_by_role('tab', name='R · base R', exact=True)
            rtab.click()
            check(page.locator('[role=tab][aria-selected=true][data-language=r]').count() == 2, 'Language selection not synchronized')
            rtab.focus(); page.keyboard.press('ArrowRight')
            check(first.get_by_role('tab', name='Python', exact=True).get_attribute('aria-selected') == 'true', 'Arrow key failed')
            page.keyboard.press('End'); check(first.get_by_role('tab', name='Python', exact=True).get_attribute('aria-selected') == 'true', 'End did not select the last R-first tab')
            page.keyboard.press('Home'); check(rtab.get_attribute('aria-selected') == 'true', 'Home did not select the first R tab')
            panel = first.locator('[role=tabpanel]:not([hidden])')
            copy = panel.get_by_role('button', name=re.compile('Copy code:')).first
            expected = panel.locator('pre code').first.text_content()
            copy.click()
            page.wait_for_function('navigator.clipboard.readText().then(t=>t.length>0)')
            check(page.evaluate('navigator.clipboard.readText()') == expected, 'Clipboard did not preserve exact code')
            check(copy.inner_text().strip() == 'Copied', 'Copy feedback absent')
            check('Copy code' not in page.evaluate('navigator.clipboard.readText()'), 'Copied toolbar text')
            page.evaluate('''() => { const target=document.querySelector('[data-code-tabs] [role=tabpanel][data-language=r] h3'); target.id='tutorial-r-deep-link'; location.hash='tutorial-r-deep-link'; }''')
            page.wait_for_function("document.getElementById('tutorial-r-deep-link')?.closest('[role=tabpanel]').hidden === false")
            check(rtab.get_attribute('aria-selected') == 'true', 'Hash target not revealed')
            page.evaluate('''() => { const target=document.querySelector('[data-code-tabs] [role=tabpanel][data-language=python] h3'); target.id='tutorial-python-deep-link'; location.hash='tutorial-python-deep-link'; }''')
            page.wait_for_function("document.getElementById('tutorial-python-deep-link')?.closest('[role=tabpanel]').hidden === false")
            check(first.get_by_role('tab', name='Python', exact=True).get_attribute('aria-selected') == 'true', 'Python hash target not revealed')
            check(page.evaluate("sessionStorage.getItem('omicsHubCodeLanguage')") == 'r', 'Hash reveal overwrote the reader language preference')
            rtab.click(); ready(page, 'experimental-design-batch-effects')
            check(page.locator('[role=tab][aria-selected=true][data-language=r]').count() == 2, 'Language preference not retained across lessons')
            check(not page.locator('#back-to-top').is_visible(), 'Top control should wait until the reader scrolls')
            page.evaluate("window.scrollTo({top:650,behavior:'instant'})")
            page.locator('#back-to-top').wait_for(state='visible')
            page.get_by_role('link', name=re.compile('Back to top')).click()
            page.wait_for_function("document.activeElement?.id === 'tutorial-title' && window.scrollY < 300")
            check(page.evaluate('document.activeElement.id') == 'tutorial-title', 'Back-to-top focus not returned')
            check(page.evaluate('window.scrollY') < 300, 'Back-to-top did not navigate')
            first_python = page.locator('[data-code-tabs]').first.get_by_role('tab', name='Python', exact=True)
            first_python.click()
            check(page.locator('[role=tab][aria-selected=true][data-language=python]').count() == 2, 'Explicit Python choice did not synchronize')
            ready(page, 'statistics-for-bioinformatics')
            check(page.locator('[role=tab][aria-selected=true][data-language=python]').count() == 2, 'Explicit Python preference was not retained across lessons')
            page.locator('[data-code-tabs]').first.get_by_role('tab', name='R · base R', exact=True).click()
            results['interactions'] += ['R-first tab order', 'R default', 'tab click', 'synchronized language preference', 'Arrow/Home/End keys', 'exact clipboard contents', 'visible copied feedback', 'R and Python hash reveals without preference changes', 'cross-page R and Python preference', 'native back-to-top and focus']
            # Print exposes both language routes with their original headings.
            page.emulate_media(media='print')
            check(page.locator('[role=tabpanel]').evaluate_all('(els)=>els.every(el=>getComputedStyle(el).display!=="none")'), 'Print hides a language route')
            printed = page.locator('.reader-path-card--suggested').first
            check(printed.evaluate('el=>getComputedStyle(el).backgroundColor') == 'rgb(255, 255, 255)', 'Print navigation is not white')
            check(printed.locator('.reader-path-card__title').evaluate('el=>getComputedStyle(el).color') == 'rgb(18, 51, 72)', 'Print navigation title is not dark')
            page.emulate_media(media='screen'); results['interactions'] += ['print includes both routes', 'readable printed continuation navigation']
            # Screenshots deliberately contain public teaching examples only.
            page.set_viewport_size({'width': 1440, 'height': 1000}); ready(page, 'spatial-transcriptomics-r-python')
            page.locator('[data-code-tabs]').nth(1).evaluate("el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().top-120,behavior:'instant'})")
            page.screenshot(path=str(args.output / 'desktop-language-tabs.png'))
            page.locator('#reader-course-navigation').evaluate("el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().top-120,behavior:'instant'})")
            page.screenshot(path=str(args.output / 'desktop-next-steps.png'))
            page.set_viewport_size({'width': 390, 'height': 844}); ready(page, 'spatial-transcriptomics-r-python')
            page.locator('[data-code-tabs]').nth(1).evaluate("el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().top-125,behavior:'instant'})")
            page.screenshot(path=str(args.output / 'mobile-language-tabs.png'))
            page.locator('#reader-course-navigation').evaluate("el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().top-120,behavior:'instant'})")
            page.screenshot(path=str(args.output / 'mobile-next-steps.png'))
            # Clipboard denial selects the original code and provides a visible instruction.
            denied = browser.new_context(viewport={'width': 390, 'height': 844}); configure(denied)
            denied.add_init_script("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}});")
            dp = denied.new_page(); ready(dp, 'statistics-for-bioinformatics')
            target = dp.locator('[data-code-tabs]').first.locator('[role=tabpanel]:not([hidden])')
            expected = target.locator('pre code').first.text_content()
            target.get_by_role('button', name=re.compile('Copy code:')).first.click()
            dp.get_by_text('Clipboard access failed. The example is selected; copy it manually.').wait_for()
            # Selection.toString() may omit a trailing rendered LF; the DOM Range
            # must nevertheless span the complete original source, byte for byte.
            check(dp.evaluate('window.getSelection().getRangeAt(0).toString()') == expected, 'Clipboard fallback selected wrong source range')
            results['interactions'].append('clipboard denial and exact manual selection')
            denied.close()
            # An altered fingerprint must leave both original alternatives visible.
            stale = browser.new_context(); configure(stale)
            script = (ROOT / 'tutorial-code-data.js').read_text()
            bad_hash = metadata['statistics-for-bioinformatics']['blocks'][0]['sha256']
            stale.route('**/tutorial-code-data.js?*', lambda route: route.fulfill(body=script.replace(bad_hash, '0'*64), content_type='text/javascript'))
            sp = stale.new_page(); ready(sp, 'statistics-for-bioinformatics')
            check(sp.locator('[data-code-tabs]').count() == 0, 'Stale code fingerprint still hides route')
            check(sp.locator('article pre:visible').count() == 10, 'Stale fallback loses original code')
            results['interactions'].append('stale metadata fails closed')
            stale.close()
            malformed = browser.new_context(); configure(malformed)
            malformed_data = json.loads(script.split('window.OMICS_TUTORIAL_CODE = ', 1)[1].rstrip(';\n'))
            malformed_data['tutorials']['statistics-for-bioinformatics']['groups'][0]['panels'][0]['end'] = 9999
            malformed_script = 'window.OMICS_TUTORIAL_CODE = ' + json.dumps(malformed_data) + ';\n'
            malformed.route('**/tutorial-code-data.js?*', lambda route: route.fulfill(body=malformed_script, content_type='text/javascript'))
            mp = malformed.new_page(); ready(mp, 'statistics-for-bioinformatics')
            check(mp.locator('[data-code-tabs]').count() == 0, 'Invalid panel bounds still move source content')
            check(mp.locator('article pre:visible').count() == 10, 'Invalid panel bounds lose original code')
            results['interactions'].append('malformed panel bounds fail closed')
            malformed.close()
            nojs = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844}); configure(nojs)
            np = nojs.new_page()
            for slug in metadata:
                np.goto(f'{args.base}/tutorials/{slug}.html')
                check(np.locator('article pre:visible').count() == len(metadata[slug]['blocks']), f'{slug} no-JS route missing')
                check(np.locator('#back-to-top').get_attribute('href') == '#tutorial-title', 'No-JS top link absent')
            results['interactions'].append('no-JS source routes and native top link')
            nojs.close()
            ready(page, 'command-line-part1')
            source_url = page.url
            page.locator('#reader-course-navigation a[rel=next]').first.click()
            page.wait_for_load_state('load'); page.wait_for_selector('html[data-tutorial-code-ready="true"]')
            check(page.url.endswith('/command-line-part2.html'), 'Suggested next link did not load the next lesson')
            page.go_back(); page.wait_for_selector('html[data-tutorial-code-ready="true"]')
            check(page.url == source_url and page.locator('article pre').count() > 0, 'Browser back lost the original lesson')
            page.evaluate("window.scrollTo({top:650,behavior:'instant'})")
            page.locator('#back-to-top').wait_for(state='visible')
            page.locator('#back-to-top').click()
            page.wait_for_function('document.activeElement?.id === "tutorial-title"')
            check(page.locator('article pre').count() > 0, 'Native fragment replaced the restored lesson')
            results['interactions'] += ['actual suggested-next navigation', 'browser back restores lesson', 'native top link after browser back']
            context.close(); browser.close()
        check(not results['errors'], 'Browser errors: ' + str(results['errors']))
        results['passed'] = True
    except Exception as error:
        results['passed'] = False; results['failure'] = str(error)
        raise
    finally:
        (args.output / 'browser-results.json').write_text(json.dumps(results, indent=2) + '\n')
        print(f'Browser evidence: {args.output}', flush=True)
    print(f'PASS: {len(results["pages"])} page/viewport checks and {len(results["interactions"])} interaction checks.', flush=True)

if __name__ == '__main__': main()
