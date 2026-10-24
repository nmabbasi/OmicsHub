#!/usr/bin/env python3
"""Homepage/catalogue review checks. All external services are blocked."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='http://127.0.0.1:8767')
    parser.add_argument('--browser',default='/opt/google/chrome/chrome')
    parser.add_argument('--output',type=Path,default=Path('/tmp/omics-home-catalogue'))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    results={'layouts':[],'interactions':[],'errors':[]}

    def check(value,message):
        if not value:raise AssertionError(message)

    def visit(page,path):
        response=page.goto(args.base+'/'+path,wait_until='networkidle')
        check(response.status==200,f'{path}: response status {response.status}')
        decline=page.get_by_role('button',name='Decline analytics',exact=True)
        if decline.is_visible():decline.click()

    def visible_cards(page):
        return page.locator('#all-tutorials-list article:visible')

    def check_filter_match(page):
        data=page.evaluate('''()=>{
          const category=document.querySelector('#catalogue-category').value;
          const level=document.querySelector('#catalogue-level').value;
          const format=document.querySelector('#catalogue-format').value;
          return [...document.querySelectorAll('#all-tutorials-list article')].filter(e=>e.checkVisibility()).map(e=>({
            valid:(category==='all'||e.dataset.category===category)&&(level==='all'||e.dataset.level===level)&&(format==='all'||e.dataset.format===format)
          }));
        }''')
        check(all(item['valid'] for item in data),'Combined filters leaked a nonmatching card')

    def check_circle(page,title):
        circle=page.locator('#back-to-top')
        found=False
        for y in range(240,2201,40):
            page.evaluate('(y)=>scrollTo({top:y,behavior:"instant"})',y)
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            if circle.is_visible():
                found=True
                props=circle.evaluate('''e=>({radius:getComputedStyle(e).borderRadius,width:e.getBoundingClientRect().width,
                  label:getComputedStyle(e.lastElementChild).display,bottom:e.getBoundingClientRect().bottom})''')
                check(props['radius']=='50%' and props['width']>=44 and props['label']=='none','Unstyled circular top control')
                check(props['bottom']<=page.viewport_size['height'],'Top control extends beyond viewport')
                circle.click()
                page.wait_for_function('(id)=>document.activeElement?.id===id&&scrollY<240',arg=title)
                break
        check(found,'Circular top control never found a safe visible position')
        results['interactions'].append({'page':page.url,'check':'circular top control and heading focus','passed':True})

    try:
        with sync_playwright() as p:
            options={'headless':True,'args':['--no-sandbox']}
            if args.browser:options['executable_path']=args.browser
            browser=p.chromium.launch(**options)
            for width,height in [(1440,1100),(1024,900),(768,1024),(390,844),(320,568)]:
                context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                context.route('https://**/*',lambda route:route.abort())
                page=context.new_page()
                page.on('pageerror',lambda e:results['errors'].append(str(e)))
                for path in ['index.html','tutorials.html']:
                    visit(page,path)
                    layout=page.evaluate('''()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
                      h1:document.querySelectorAll('main h1').length,
                      unaligned:[...document.querySelectorAll('main h1,main h2,main h3,main p,main dd')].filter(e=>e.checkVisibility()&&!['left','start'].includes(getComputedStyle(e).textAlign)).map(e=>e.textContent.slice(0,60)),
                      smallControls:[...document.querySelectorAll('main input,main select,main button,.hc-hero-actions a')].filter(e=>e.checkVisibility()&&(e.getBoundingClientRect().height<44||e.getBoundingClientRect().width<44)).map(e=>e.id),
                      duplicateIds:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,a)=>a.indexOf(id)!==i)
                    })''')
                    check(layout['scrollWidth']<=width+1,f'{path} {width}: horizontal page overflow')
                    check(layout['h1']==1,f'{path}: expected one primary heading')
                    check(not layout['unaligned'],f'{path}: non-left-aligned reading text {layout["unaligned"]}')
                    check(not layout['smallControls'],f'{path}: small touch controls {layout["smallControls"]}')
                    check(not layout['duplicateIds'],f'{path}: duplicate IDs {layout["duplicateIds"]}')
                    results['layouts'].append({'page':path,'width':width,'passed':True})
                    if path=='index.html':
                        check(page.locator('.native-tutorial-card').count()==6,'Homepage lost a selected lesson')
                        check(page.locator('.hero-laptop-frame').count()==1,'Photographed terminal frame was replaced')
                        check(page.locator('[aria-label="Terminal prompt"]').count()==1,'Terminal header was removed')
                        check(page.locator('.hero-btn[href="tutorials.html"]').is_visible(),'Original Explore Tutorials action was removed')
                        hero=page.locator('.hero-laptop-canvas').evaluate('e=>getComputedStyle(e).backgroundColor')
                        check(hero=='rgb(255, 255, 255)','Original light hero background was changed')
                        if width>=1024:
                            boxes=page.locator('.hero-laptop-content').evaluate('e=>({text:e.querySelector("h1").getBoundingClientRect().left,art:e.querySelector("picture").getBoundingClientRect().left})')
                            check(boxes['art']>boxes['text'],'Original illustration must stay to the right of the text')
                        search=page.locator('#search-input')
                        search.fill('trajectory')
                        page.wait_for_function('document.querySelector("#search-results-status").textContent.includes("matching")')
                        check(page.locator('#search-suggestions a').count()>0,'Homepage search did not include non-featured catalogue lessons')
                        check(page.locator('.native-tutorial-card:visible').count()==6,'Homepage search unexpectedly hides curated lessons')
                        search.press('Escape')
                        check(not page.locator('#search-suggestions').is_visible(),'Search suggestions did not dismiss with Escape')
                        search.fill('scrna')
                        search.press('Enter')
                        page.wait_for_url('**/tutorials.html?q=scrna')
                        page.wait_for_load_state('networkidle')
                        check(visible_cards(page).count()>0,'Homepage search Enter lost matching catalogue results')
                        visit(page,'index.html')
                        check_circle(page,'site-page-title')
                    else:
                        check(visible_cards(page).count()==58,'Default catalogue does not expose all 58 lessons')
                        check(page.locator('#catalogue-category').count()==1,'Duplicate topic select')
                        check(page.locator('#all-tutorials-list .hc-card-prerequisite').count()==58,'Missing prerequisite previews')
                        page.select_option('#catalogue-category','Foundations & Prerequisites')
                        check(visible_cards(page).count()==12,'Topic filter count changed')
                        page.select_option('#catalogue-level','beginner')
                        page.select_option('#catalogue-format','reference')
                        page.fill('#search-input','biological')
                        check(visible_cards(page).count()==1,'Combined topic/level/format/query filter did not isolate data-format reference')
                        check_filter_match(page)
                        state=parse_qs(urlparse(page.url).query)
                        check(state=={'category':['Foundations & Prerequisites'],'level':['beginner'],'format':['reference'],'q':['biological']},'Combined filter URL state is incomplete')
                        page.reload(wait_until='networkidle')
                        check(visible_cards(page).count()==1 and page.locator('#catalogue-format').input_value()=='reference','Reload lost filter state')
                        link=visible_cards(page).locator('a.hc-card-link')
                        lesson=link.get_attribute('href')
                        link.click()
                        page.wait_for_url('**/'+lesson)
                        page.wait_for_load_state('networkidle')
                        return_link=page.locator('[data-catalogue-return]').first
                        saved=parse_qs(urlparse(return_link.get_attribute('href')).query)
                        check(saved==state,'Lesson return navigation lost combined filters')
                        return_link.click()
                        page.wait_for_url('**/tutorials.html?**')
                        page.wait_for_load_state('networkidle')
                        check(visible_cards(page).count()==1,'Return to results did not restore filtered catalogue')
                        page.fill('#search-input','no-such-lesson-xyzz')
                        check(visible_cards(page).count()==0,'No-match query leaks visible results')
                        check(page.locator('#catalogue-clear-empty').is_visible(),'No-match recovery is missing')
                        page.locator('#catalogue-clear-empty').click()
                        check(visible_cards(page).count()==58 and not urlparse(page.url).query,'Reset did not clear all four filters')
                        page.select_option('#catalogue-category','Metagenomics')
                        check(visible_cards(page).count()==3,'Metagenomics topic count changed')
                        page.select_option('#catalogue-level','advanced')
                        page.go_back(wait_until='networkidle')
                        check(page.locator('#catalogue-category').input_value()=='Metagenomics' and page.locator('#catalogue-level').input_value()=='all','History Back did not restore the prior filter state')
                        page.locator('#catalogue-reset').click()
                        check_circle(page,'catalogue-hero-title')
                        results['interactions'].append({'width':width,'check':'combined filters, URL reload, history, lesson return, no-match recovery','passed':True})
                context.close()
                print(f'PASS homepage/catalogue layout and interaction checks at {width}px',flush=True)
            context=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False)
            context.route('https://**/*',lambda route:route.abort())
            page=context.new_page()
            page.goto(args.base+'/tutorials.html')
            check(visible_cards(page).count()==58,'Catalogue hides lessons without JavaScript')
            page.goto(args.base+'/index.html')
            check(page.locator('main a[href="start-here.html"]').first.is_visible(),'Beginner action is unavailable without JavaScript')
            check(page.locator('.hero-btn[href="tutorials.html"]').is_visible(),'Original Explore Tutorials action is unavailable without JavaScript')
            results['interactions'].append({'check':'no-JavaScript lesson access','passed':True})
            context.close()
            browser.close()
        check(not results['errors'],f'Uncaught browser errors: {results["errors"]}')
        results['passed']=True
    finally:
        (args.output/'home-catalogue-browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS {len(results["layouts"])} layouts and {len(results["interactions"])} interaction groups; no uncaught browser errors',flush=True)

if __name__=='__main__':main()
