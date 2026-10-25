#!/usr/bin/env python3
"""Exercise review-only fixes on a temporary local server; never contact third parties.

Requires Python Playwright and Chromium. Newsletter fetch calls are simulated in-page,
so no signup, email or Google request is made. Results are written only when --output is given.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import threading
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def check(value, message):
    if not value:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--browser', default=shutil.which('chromium') or '')
    args = parser.parse_args()
    results = {'passed': [], 'failures': [], 'pageerrors': [], 'third_party_requests_sent': 0}
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'

    def run(name, fn):
        try:
            fn()
            results['passed'].append(name)
        except Exception as error:
            results['failures'].append({'name': name, 'error': str(error)})
        print(f'{name}: {len(results["passed"])} passed, {len(results["failures"])} failed', flush=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(results, indent=2) + '\n')

    try:
        with sync_playwright() as playwright:
            launch = {'args': ['--no-sandbox']}
            if args.browser:
                launch['executable_path'] = args.browser
            browser = playwright.chromium.launch(**launch)
            context = browser.new_context(reduced_motion='reduce')
            context.route('**/*', lambda route: route.continue_() if urlparse(route.request.url).hostname == '127.0.0.1' and route.request.method == 'GET' else route.abort())
            context.add_init_script("localStorage.setItem('omicsHubCookieChoice', 'declined');")
            page = context.new_page()
            page.set_default_timeout(10000)
            page.on('pageerror', lambda error: results['pageerrors'].append(str(error)))

            def ready(path):
                response = page.goto(base + path, wait_until='load')
                check(response.status == 200, 'Local page did not load')
                if path.startswith('tutorials/'):
                    page.wait_for_selector('html[data-tutorial-code-ready=true]')

            for width in [1440, 1024, 768, 390, 320]:
                page.set_viewport_size({'width': width, 'height': 1000})

                def searches():
                    ready('')
                    search = page.locator('#search-input')
                    for query in ['R Markdown', 'RMarkdown', 'Rmd']:
                        search.fill(query)
                        page.wait_for_function("document.querySelector('#search-results-status').textContent.includes('matching')")
                        check(page.locator('#search-suggestions a[href="tutorials/research-reporting-interpretation.html"]').count() == 1, 'Homepage omitted the reporting lesson')
                    search.press('Enter')
                    page.wait_for_url('**/tutorials.html?q=Rmd')
                    for query in ['R Markdown', 'RMarkdown', 'Rmd', '.Rmd']:
                        page.locator('#search-input').fill(query)
                        card = page.locator('.tutorial-grid-card').filter(has=page.locator('a[href="tutorials/research-reporting-interpretation.html"]'))
                        check(card.is_visible(), 'Catalogue omitted the reporting lesson')
                    check(page.evaluate('document.documentElement.scrollWidth') <= width + 1, 'Search view overflows')
                run(f'R Markdown homepage/catalogue searches {width}', searches)

                for slug, target in [('autonomous-research-orchestrator', 'python-alternative'), ('single-cell-foundation-models', 'foundation-embedding-python-run-stage')]:
                    def anchor():
                        ready('tutorials/' + slug + '.html')
                        page.locator('[data-code-tabs] [role=tab][data-language=r]').first.click()
                        page.locator(f'a[href="#{target}"]').click()
                        page.wait_for_function('(id)=>!document.getElementById(id).closest("[role=tabpanel]").hidden', arg=target)
                        check(page.locator('#' + target).is_visible(), 'Python target remains hidden')
                        check(page.locator('[data-code-tabs] [role=tab][data-language=python]').first.get_attribute('aria-selected') == 'true', 'Deep link did not select Python')
                    run(f'Optional Python jump {slug} {width}', anchor)

                for slug in ['ai-bioinformatics-github-copilot', 'ai-coding-cursor-aider', 'advanced-ai-single-cell', 'autonomous-research-orchestrator']:
                    def legal():
                        ready('tutorials/' + slug + '.html')
                        button = page.locator('#legal-menu-button')
                        if width < 1024:
                            check(not button.is_visible(), 'Desktop Legal control should not be exposed on mobile')
                            trigger = page.locator('button[aria-controls=mobile-menu]')
                            trigger.click()
                            menu = page.locator('#mobile-menu')
                            for policy in ['privacy', 'terms', 'disclaimer', 'cookie']:
                                check(menu.locator(f'a[href="../pages/{policy}.html"]').is_visible(), 'Missing mobile legal link')
                            trigger.press('Escape')
                            check(trigger.get_attribute('aria-expanded') == 'false', 'Mobile navigation did not close')
                            return
                        button.click()
                        check(button.get_attribute('aria-expanded') == 'true', 'Legal menu did not open')
                        button.press('Escape')
                        page.wait_for_timeout(300)
                        state = page.locator('#legal-menu').evaluate('e=>({visibility:getComputedStyle(e).visibility,opacity:getComputedStyle(e).opacity})')
                        check(button.get_attribute('aria-expanded') == 'false' and state == {'visibility': 'hidden', 'opacity': '0'}, 'Escape left the Legal menu painted while closed')
                        check(button.evaluate('e=>e===document.activeElement'), 'Escape lost trigger focus')
                        button.click()
                        page.mouse.click(5, 300)
                        page.wait_for_timeout(300)
                        check(not page.locator('#legal-menu').is_visible(), 'Outside click did not close Legal menu')
                    run(f'Legal close/mobile destinations {slug} {width}', legal)

                def newsletter():
                    ready('services.html#newsletter-title')
                    form = page.locator('#newsletter-gs-form')
                    check(page.locator('#nl-fields').evaluate('e=>!e.disabled'), 'JavaScript did not enable the form')
                    page.locator('#nl-name').fill('QA simulation')
                    page.locator('#nl-email').fill('qa@example.invalid')
                    page.locator('#nl-consent').check()
                    check(form.evaluate('e=>e.checkValidity()'), 'Filled form is invalid')
                    page.evaluate("() => {window.__fakeRequests=[];window.fetch=(url,options)=>{window.__fakeRequests.push({url,options});return new Promise((resolve,reject)=>{window.__finishFake=resolve;window.__rejectFake=reject;});};}")
                    page.locator('#nl-submit').click()
                    check(form.get_attribute('aria-busy') == 'true', 'Sending state is not exposed')
                    check('Sending' in page.locator('#nl-status').inner_text(), 'No announced sending state')
                    check(page.locator('#nl-submit').is_disabled(), 'Pending form can double-submit')
                    page.evaluate("window.__rejectFake(new Error('Simulated network failure'))")
                    page.wait_for_function("document.querySelector('#newsletter-gs-form').getAttribute('aria-busy')==='false'")
                    check(page.locator('#nl-error').is_visible() and page.locator('#nl-error').get_attribute('role') == 'alert', 'Failure is not exposed as an alert')
                    check(not page.locator('#nl-submit').is_disabled(), 'Retry was not enabled')
                    page.locator('#nl-submit').click()
                    page.evaluate('window.__finishFake({})')
                    page.wait_for_selector('#nl-success', state='visible')
                    check(page.locator('#nl-success').evaluate('e=>document.activeElement===e'), 'Completion focus is missing')
                    check('cannot confirm' in page.locator('#nl-status').inner_text(), 'Completion overclaims delivery')
                    check(page.evaluate('window.__fakeRequests.length') == 2, 'Unexpected simulated request count')
                    check(page.evaluate('document.documentElement.scrollWidth') <= width + 1, 'Newsletter view overflows')
                run(f'Newsletter simulated progress/failure/retry/completion {width}', newsletter)

            nojs = browser.new_context(java_script_enabled=False)
            nojs.route('**/*', lambda route: route.continue_() if urlparse(route.request.url).hostname == '127.0.0.1' and route.request.method == 'GET' else route.abort())
            offline = nojs.new_page()
            offline.goto(base + 'services.html#newsletter-title', wait_until='load')
            def no_javascript():
                check(offline.locator('#nl-fields').evaluate('e=>e.disabled'), 'No-JavaScript fields are unsafe')
                check(offline.locator('#nl-submit').is_disabled(), 'No-JavaScript submit is enabled')
                notice = offline.locator('#newsletter-form-wrap noscript p')
                check(notice.is_visible() and 'Newsletter signup requires JavaScript.' in notice.text_content(), 'No usable fallback explanation')
                check('?' not in offline.url, 'Personal details reached the URL')
            run('Newsletter no-JavaScript safe fallback', no_javascript)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps(results, indent=2))
    return 1 if results['failures'] or results['pageerrors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
