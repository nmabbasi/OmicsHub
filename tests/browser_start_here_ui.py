#!/usr/bin/env python3
"""Beginner landing-page and shared circular-control checks; remote requests blocked."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8767')
    parser.add_argument('--browser', default='/opt/google/chrome/chrome')
    parser.add_argument('--output', type=Path, default=Path('/tmp/omics-beginner-ui'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = {'layouts': [], 'interactions': [], 'errors': []}
    def check(value, message):
        if not value: raise AssertionError(message)
    def block_remote(context):
        context.route('https://**/*', lambda route: route.abort())
    def circle(page):
        return page.locator('#back-to-top')
    def scroll(page, y):
        # Narrow screens with a consent banner can have only brief safe gaps.
        # Search the actual layout rather than requiring a text-obscuring arrow.
        for offset in range(0, 1601, 20):
            page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})', y + offset)
            page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            if circle(page).is_visible(): return
        raise AssertionError('No safe position for the circular control near requested scroll')
    try:
        with sync_playwright() as p:
            options = {'headless': True, 'args': ['--no-sandbox']}
            if args.browser: options['executable_path'] = args.browser
            browser = p.chromium.launch(**options)
            for width, height in [(1440, 1250), (1920, 1200), (2560, 1200), (768, 1000), (390, 844), (320, 568)]:
                context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
                block_remote(context)
                page = context.new_page()
                page.on('pageerror', lambda error: results['errors'].append(str(error)))
                page.goto(args.base + '/start-here.html')
                page.wait_for_function('document.querySelector(".tutorial-top-tools.is-floating") !== null')
                check(not circle(page).is_visible(), f'{width}: top control visible before scrolling')
                data = page.evaluate('''() => ({
                  width:innerWidth, scrollWidth:document.documentElement.scrollWidth,
                  heroLeft:getComputedStyle(document.querySelector('.sh-hero')).textAlign,
                  coreVisible:document.getElementById('sh-step-1').checkVisibility() && [...document.querySelectorAll('.sh-step-nav a')].every(e=>e.checkVisibility()),
                  details:[...document.querySelectorAll('main details')].map(e=>({open:e.open,summaryHeight:e.querySelector('summary').getBoundingClientRect().height})),
                  actions:[...document.querySelectorAll('.sh-primary-link,.sh-orbit-stop,.sh-step-nav a,.sh-choice-links a,.sh-catalogue a')].filter(e=>e.checkVisibility()).map(e=>({height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width})),
                  visibleWords:document.querySelector('main').innerText.trim().split(/\\s+/).length,
                  totalWords:document.querySelector('main').textContent.trim().split(/\\s+/).length,
                  mainHeight:document.querySelector('main').getBoundingClientRect().height,
                  heroButtonBottom:document.querySelector('.sh-primary-link').getBoundingClientRect().bottom,
                  desktop:innerWidth >= 1440 ? (() => {
                    const hero=document.querySelector('.sh-hero'), r=hero.getBoundingClientRect();
                    const body=document.querySelector('#sh-step-1 p:not(.sh-panel-kicker):not(.sh-note)');
                    const note=document.querySelector('#sh-step-1 .sh-note');
                    const title=document.querySelector('.sh-step-nav strong'), secondary=document.querySelector('.sh-step-nav small');
                    return {heroLeft:r.left,heroWidth:r.width,bodySize:parseFloat(getComputedStyle(body).fontSize),
                      noteSize:parseFloat(getComputedStyle(note).fontSize),navTitleSize:parseFloat(getComputedStyle(title).fontSize),
                      navSecondarySize:parseFloat(getComputedStyle(secondary).fontSize),bodyColor:getComputedStyle(body).color,
                      noteColor:getComputedStyle(note).color,heroBackground:getComputedStyle(hero).backgroundImage};
                  })() : null
                })''')
                check(data['scrollWidth'] <= width + 1, f'{width}: page overflow')
                check(data['heroLeft'] == 'left', f'{width}: hero is not left aligned')
                check(data['coreVisible'], f'{width}: essential beginner guidance is hidden')
                check(all(not d['open'] and d['summaryHeight'] >= 48 for d in data['details']), f'{width}: optional details not initially compact')
                check(all(a['height'] >= 44 and a['width'] >= 44 for a in data['actions']), f'{width}: small primary target')
                check(data['visibleWords'] < 340 and data['totalWords'] < 650, f'{width}: excessive reading load')
                max_button_bottom = height + (120 if width == 320 else 0)
                check(data['heroButtonBottom'] <= max_button_bottom, f'{width}: first lesson button is beyond the permitted initial view/short scroll')
                if width >= 1440:
                    desktop = data['desktop']
                    check(abs(desktop['heroLeft']) <= 1 and abs(desktop['heroWidth'] - width) <= 1,
                          f'{width}: banner does not span the full viewport')
                    check(desktop['bodySize'] >= 16, f'{width}: lesson body text is below 16px')
                    check(desktop['noteSize'] >= 14, f'{width}: lesson note is below 14px')
                    check(desktop['navTitleSize'] >= 16, f'{width}: navigation title is below 16px')
                    check(desktop['navSecondarySize'] >= 14, f'{width}: navigation secondary text is below 14px')
                    check('gradient(' in desktop['heroBackground'], f'{width}: banner gradient was lost')
                    for key in ('bodyColor', 'noteColor'):
                        channels = [int(value) for value in __import__('re').findall(r'\d+', desktop[key])[:3]]
                        check(len(channels) == 3 and sum(channels) / 3 < 150,
                              f'{width}: {key} is not dark readable copy')
                # Circle, side guide and previous/next controls stay in sync.
                for step in range(1, 5):
                    page.locator(f'.sh-orbit-stop[data-sh-step="{step}"]').click()
                    check(page.locator(f'#sh-step-{step}').is_visible(), f'{width}: orbit selection {step}')
                    check(page.locator('.sh-lesson-panel:visible').count() == 1, f'{width}: competing lesson panels')
                    check(page.locator(f'.sh-step-nav a[data-sh-step="{step}"]').get_attribute('aria-current') == 'step', f'{width}: unsynced side guide')
                    check(f'Viewing step {step} of 4' in page.locator('.sh-step-status').inner_text(), f'{width}: status missing')
                    if width >= 1440:
                        geometry = page.evaluate('''(step) => {
                          const panel=document.getElementById(`sh-step-${step}`), orbit=document.querySelector('.sh-orbit');
                          const p=panel.getBoundingClientRect(), o=orbit.getBoundingClientRect();
                          return {panel:{left:p.left,top:p.top,right:p.right,bottom:p.bottom},orbit:{left:o.left,top:o.top,right:o.right,bottom:o.bottom},
                            panelScrollWidth:panel.scrollWidth,panelClientWidth:panel.clientWidth,
                            panelScrollHeight:panel.scrollHeight,panelClientHeight:panel.clientHeight,
                            bodySize:parseFloat(getComputedStyle(panel.querySelector('p:not(.sh-panel-kicker):not(.sh-note)')).fontSize),
                            noteSize:parseFloat(getComputedStyle(panel.querySelector('.sh-note')).fontSize)};
                        }''', step)
                        check(geometry['panel']['left'] >= geometry['orbit']['left'] - 1 and
                              geometry['panel']['top'] >= geometry['orbit']['top'] - 1 and
                              geometry['panel']['right'] <= geometry['orbit']['right'] + 1 and
                              geometry['panel']['bottom'] <= geometry['orbit']['bottom'] + 1,
                              f'{width}: lesson panel {step} is not safely within the orbit')
                        check(geometry['panelScrollWidth'] <= geometry['panelClientWidth'] + 1 and
                              geometry['panelScrollHeight'] <= geometry['panelClientHeight'] + 1,
                              f'{width}: lesson panel {step} content overflows')
                        check(geometry['bodySize'] >= 16 and geometry['noteSize'] >= 14,
                              f'{width}: lesson panel {step} body/note typography is too small')
                check(page.locator('[data-sh-next]').is_disabled(), f'{width}: last step incorrectly wraps')
                page.locator('.sh-step-nav a[data-sh-step="2"]').focus()
                page.keyboard.press('Enter')
                check(page.locator('#sh-step-2').is_visible(), f'{width}: keyboard side guide selection')
                page.locator('[data-sh-next]').click()
                check(page.locator('#sh-step-3').is_visible(), f'{width}: next control')
                page.locator('[data-sh-previous]').click()
                check(page.locator('#sh-step-2').is_visible(), f'{width}: previous control')
                page.goto(args.base + '/start-here.html#sh-language-choice')
                check(page.locator('#sh-step-4').is_visible(), f'{width}: language deep link remains hidden')
                check(page.locator('.sh-choice-links a:visible').count() == 2, f'{width}: R/Python options unavailable')
                page.goto(args.base + '/start-here.html')
                check(page.locator('[data-sh-previous]').is_disabled(), f'{width}: first step incorrectly wraps')
                scroll(page, 650)
                placement = page.evaluate('''() => {
                    const e=document.getElementById('back-to-top'), r=e.getBoundingClientRect(), b=document.getElementById('cookie-consent-banner');
                    return {width:r.width,height:r.height,left:r.left,top:r.top,right:r.right,bottom:r.bottom,viewportHeight:innerHeight,radius:getComputedStyle(e).borderRadius,bg:getComputedStyle(e).backgroundColor,position:getComputedStyle(e.parentElement).position,bannerTop:b.getBoundingClientRect().top};
                }''')
                check(placement['width'] == placement['height'] and placement['width'] >= 48, f'{width}: control not circular/touch-safe')
                check(placement['radius'] == '50%' and placement['position'] == 'fixed', f'{width}: circular/floating styling absent')
                check(placement['bg'] == 'rgb(18, 59, 93)', f'{width}: control does not use brand navy')
                check(placement['top'] >= 0 and placement['right'] <= width and placement['bottom'] <= height, f'{width}: control outside viewport')
                check(placement['bottom'] <= placement['bannerTop'] - 8, f'{width}: control overlaps consent banner')
                page.get_by_role('button', name='Decline analytics', exact=True).click()
                page.wait_for_function('parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--reader-banner-space")) === 0')
                scroll(page, 650)
                if width == 390:
                    circle(page).hover()
                    page.screenshot(path=str(args.output / 'back-to-top-mobile.png'))
                    page.mouse.move(0, 0)
                page.keyboard.press('Tab')
                circle(page).focus()
                check(circle(page).evaluate('el=>getComputedStyle(el).outlineStyle') == 'solid', f'{width}: no visible keyboard focus')
                page.keyboard.press('Enter')
                page.wait_for_function('document.activeElement?.id === "sh-hero-title" && scrollY < 240')
                page.wait_for_function('document.querySelector(".tutorial-top-tools").hidden')
                check(page.locator('.sh-eyebrow').bounding_box()['y'] >= page.locator('body > header').bounding_box()['height'], f'{width}: top arrow hides hero eyebrow')
                if width in (1440, 390):
                    page.goto(args.base + '/start-here.html')
                    page.reload()
                    page.wait_for_function('document.querySelector(".tutorial-top-tools.is-floating") !== null && scrollY === 0')
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.screenshot(path=str(args.output / ('start-here-desktop.png' if width == 1440 else 'start-here-mobile.png')))
                # Native keyboard details, hash reveal and a clean return to collapsed state.
                details = page.locator('#sh-single-cell')
                details.locator('summary').focus()
                page.keyboard.press('Enter')
                check(details.get_attribute('open') is not None, f'{width}: keyboard cannot expand a topic')
                details.locator('summary').press('Enter')
                check(details.get_attribute('open') is None, f'{width}: keyboard cannot collapse a topic')
                page.goto(args.base + '/start-here.html#sh-single-cell')
                page.wait_for_function('document.getElementById("sh-single-cell").open')
                bounds = details.locator('summary').bounding_box()
                header_bottom = page.locator('body > header').bounding_box()['height']
                check(bounds['y'] >= header_bottom - 1, f'{width}: deep-linked summary hidden by header')
                page.goto(args.base + '/start-here.html#sh-hpc')
                page.wait_for_function('document.getElementById("sh-hpc-track").open')
                # Printing opens optional guidance, then restores the user's choices.
                states = page.locator('main details').evaluate_all('(els)=>els.map(e=>e.open)')
                page.evaluate('dispatchEvent(new Event("beforeprint"))')
                check(page.locator('main details').evaluate_all('(els)=>els.every(e=>e.open)'), f'{width}: print loses optional guidance')
                page.evaluate('dispatchEvent(new Event("afterprint"))')
                check(page.locator('main details').evaluate_all('(els)=>els.map(e=>e.open)') == states, f'{width}: print changed disclosure preferences')
                if width == 390:
                    page.goto(args.base + '/start-here.html#sh-routes')
                    page.locator('main details').evaluate_all('(els)=>els.forEach(e=>e.open=false)')
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    # Put a full-width disclosure where the circle would otherwise sit.
                    summary = page.locator('#sh-genomics summary')
                    summary.evaluate('el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().bottom-(innerHeight-14),behavior:"instant"})')
                    page.wait_for_function('document.querySelector(".tutorial-top-tools").hidden')
                    results['interactions'].append('circle yields to overlapping disclosure controls')
                    page.locator('#sh-routes').evaluate('el=>el.scrollIntoView({block:"start",behavior:"instant"})')
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    # A heading below this band used to be obscured by the circle.
                    heading = page.locator('#sh-curriculum-title')
                    heading.evaluate('el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().bottom-(innerHeight-20),behavior:"instant"})')
                    page.wait_for_function('document.querySelector(".tutorial-top-tools").hidden')
                    results['interactions'].append('circle yields to overlapping reading text')
                    page.locator('#sh-routes').evaluate('el=>el.scrollIntoView({block:"start",behavior:"instant"})')
                    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.screenshot(path=str(args.output / 'start-here-topics-mobile.png'))
                results['layouts'].append({**data, 'height': height, 'circle': placement})
                context.close()
                print(f'PASS Start Here at {width}px: {data["visibleWords"]} visible / {data["totalWords"]} total words', flush=True)
            context = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
            block_remote(context)
            page = context.new_page()
            page.goto(args.base + '/start-here.html')
            page.locator('#sh-hpc-track summary').click()
            check(page.locator('#sh-hpc-track a').first.is_visible(), 'No-JS optional HPC content inaccessible')
            check(page.locator('.sh-primary-link').first.get_attribute('href') == 'tutorials/introduction-to-bioinformatics.html', 'No-JS first lesson missing')
            check(page.locator('.sh-lesson-panel:visible').count() == 4, 'No-JS lessons hidden')
            check(circle(page).get_attribute('href') == '#sh-hero-title', 'No-JS native top link missing')
            check(circle(page).is_visible(), 'No-JS top link inaccessible')
            context.close()
            results['interactions'] += ['first lesson above fold', 'one focused lesson with all four steps navigable', 'compact optional disclosures', '44px primary and 48px disclosure targets', 'brand circular arrow geometry', 'consent-safe floating placement', 'keyboard top focus return', 'keyboard disclosure toggling', 'topic hash reveal', 'optional HPC hash reveal', 'print open/restore', 'native no-JS reading and top anchor']
            browser.close()
        check(not results['errors'], str(results['errors']))
        results['passed'] = True
    except Exception as error:
        results['passed'] = False
        results['failure'] = str(error)
        raise
    finally:
        (args.output / 'start-here-browser-results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'PASS: {len(results["layouts"])} beginner layouts and {len(results["interactions"])} interaction contracts', flush=True)

if __name__ == '__main__':
    main()
