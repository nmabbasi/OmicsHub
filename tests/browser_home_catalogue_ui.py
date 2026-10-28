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
          return [...document.querySelectorAll('#all-tutorials-list article')].filter(e=>e.checkVisibility()).map(e=>({
            valid:(category==='all'||e.dataset.category===category)&&e.dataset.search.toLowerCase().includes(document.querySelector('#search-input').value.toLowerCase())
          }));
        }''')
        check(all(item['valid'] for item in data),'Category/search filters leaked a nonmatching card')

    def check_catalogue_images(page):
        images=page.evaluate('''async()=>{
          const rows=[];
          for(const card of document.querySelectorAll('#all-tutorials-list article')){
            const image=card.querySelector('img');
            const box=image?.closest('.hc-card-image')||image?.parentElement;
            image?.scrollIntoView({block:'center',inline:'nearest'});
            if(image){try{await image.decode()}catch(error){}}
            const rect=image?.getBoundingClientRect();
            const boxRect=box?.getBoundingClientRect();
            const style=image?getComputedStyle(image):null;
            rows.push({title:card.querySelector('h3')?.textContent.trim(),src:image?.getAttribute('src'),alt:image?.alt,
              naturalWidth:image?.naturalWidth||0,visible:!!image&&image.checkVisibility()&&!!rect&&rect.width>0&&rect.height>0&&rect.bottom>0&&rect.top<innerHeight,
              containerHeight:boxRect?.height||0,ratio:boxRect?.width&&boxRect?.height?boxRect.width/boxRect.height:0,
              objectFit:style?.objectFit||''});
          }
          return rows;
        }''')
        check(len(images)==58,f'Expected 58 catalogue images, found {len(images)}')
        failed=[image for image in images if not image['src'] or not image['alt'] or image['naturalWidth']<=0 or not image['visible'] or image['containerHeight']<140 or not 1.70<=image['ratio']<=1.90 or image['objectFit']!='cover']
        check(not failed,f'Catalogue images are missing, unloaded, not visible, too small, or not 16:9: {failed[:5]}')
        results['interactions'].append({'width':page.viewport_size['width'],'check':'all 58 catalogue images visible, loaded, and prominent 16:9','passed':True})
        page.evaluate('scrollTo({top:0,behavior:"instant"})')

    def check_card_link_surfaces(page):
        card=visible_cards(page).first
        link=card.locator('h3 a.hc-card-link')
        title=card.locator('h3').inner_text().strip()
        check(card.locator('a').count()==1,'A lesson card must expose exactly one link')
        check(link.count()==1,'The lesson title is missing its native card link')
        check(page.get_by_role('link',name=title,exact=True).count()==1,'The visible lesson title must be the link accessible name')
        check('Open lesson' not in card.inner_text(),'A visible Open lesson label remains on the card')
        href=link.get_attribute('href')
        check(bool(href),'The title link has no lesson destination')

        def follow_and_return(target,description):
            target.scroll_into_view_if_needed()
            box=target.bounding_box()
            check(bool(box),f'{description} has no visible pointer target')
            page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
            page.wait_for_url('**/'+href)
            page.wait_for_load_state('networkidle')
            check(page.url.endswith('/'+href),f'{description} did not navigate to the lesson')
            page.go_back(wait_until='networkidle')
            check(page.url.endswith('/tutorials.html'),f'{description} did not return to the catalogue')

        link.focus()
        page.keyboard.press('Enter')
        page.wait_for_url('**/'+href)
        page.wait_for_load_state('networkidle')
        check(page.url.endswith('/'+href),'Enter on the title link did not open its lesson')
        page.go_back(wait_until='networkidle')

        card=visible_cards(page).first
        follow_and_return(card.locator('img'),'Clicking the card image')
        card=visible_cards(page).first
        follow_and_return(card.locator('p'),'Clicking the card description')
        card=visible_cards(page).first
        card.scroll_into_view_if_needed()
        point=card.evaluate('''e=>{
          const r=e.getBoundingClientRect(),x=r.right-8,y=r.top+r.height/2;
          const hit=document.elementFromPoint(x,y);
          const occupied=[...e.querySelectorAll('img,p,h3,.hc-card-meta')].some(node=>{
            const box=node.getBoundingClientRect();
            return x>=box.left&&x<=box.right&&y>=box.top&&y<=box.bottom;
          });
          return {x,y,blank:!occupied&&!!hit&&e.contains(hit)&&!!hit.closest('a.hc-card-link')};
        }''')
        check(point['blank'],'Could not identify blank card whitespace for the click-through test')
        page.mouse.click(point['x'],point['y'])
        page.wait_for_url('**/'+href)
        page.wait_for_load_state('networkidle')
        check(page.url.endswith('/'+href),'Clicking blank card whitespace did not open its lesson')
        page.go_back(wait_until='networkidle')
        check(page.url.endswith('/tutorials.html'),'Blank-space navigation did not return to the catalogue')
        results['interactions'].append({'width':page.viewport_size['width'],'check':'title accessible name and Enter, image, description, and blank-space native lesson links','passed':True})

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
                        check(page.locator('#catalogue-level, #catalogue-format').count()==0,'Experience/format dropdowns must be removed')
                        check(page.locator('#all-tutorials-list .hc-card-prerequisite, #all-tutorials-list .hc-card-level').count()==0,'Removed prerequisite/experience panels reappeared')
                        if width==390:check_card_link_surfaces(page)
                        if width==1440:check_catalogue_images(page)
                        page.select_option('#catalogue-category','Foundations & Prerequisites')
                        check(visible_cards(page).count()==12,'Topic filter count changed')
                        page.fill('#search-input','biological data formats')
                        check(visible_cards(page).count()==1,'Category and search did not isolate the data-formats lesson')
                        check_filter_match(page)
                        state=parse_qs(urlparse(page.url).query)
                        check(state=={'category':['Foundations & Prerequisites'],'q':['biological data formats']},'Category/search URL state is incomplete')
                        page.reload(wait_until='networkidle')
                        check(visible_cards(page).count()==1 and page.locator('#catalogue-category').input_value()=='Foundations & Prerequisites' and page.locator('#search-input').input_value()=='biological data formats','Reload lost category/search state')
                        link=visible_cards(page).locator('a.hc-card-link')
                        lesson=link.get_attribute('href')
                        link.click()
                        page.wait_for_url('**/'+lesson)
                        page.wait_for_load_state('networkidle')
                        return_link=page.locator('[data-catalogue-return]').first
                        saved=parse_qs(urlparse(return_link.get_attribute('href')).query)
                        check(saved==state,'Lesson return navigation lost category/search state')
                        return_link.click()
                        page.wait_for_url('**/tutorials.html?**')
                        page.wait_for_load_state('networkidle')
                        check(visible_cards(page).count()==1,'Return to results did not restore filtered catalogue')
                        page.fill('#search-input','no-such-lesson-xyzz')
                        check(visible_cards(page).count()==0,'No-match query leaks visible results')
                        check(page.locator('#catalogue-clear-empty').is_visible(),'No-match recovery is missing')
                        page.locator('#catalogue-clear-empty').click()
                        check(visible_cards(page).count()==58 and not urlparse(page.url).query,'Reset did not clear category and search')
                        page.select_option('#catalogue-category','Metagenomics')
                        check(visible_cards(page).count()==3,'Metagenomics topic count changed')
                        page.go_back(wait_until='networkidle')
                        check(page.locator('#catalogue-category').input_value()=='all' and page.locator('#search-input').input_value()=='','History Back did not restore the prior category/search state')
                        page.locator('#catalogue-reset').click()
                        visit(page,'tutorials.html?category=Foundations%20%26%20Prerequisites&level=advanced&format=reference&q=biological%20data%20formats')
                        check(visible_cards(page).count()==1,'Legacy level/format parameters interfered with supported category/query state')
                        check(parse_qs(urlparse(page.url).query)=={'category':['Foundations & Prerequisites'],'q':['biological data formats']},'Legacy level/format URL parameters were not normalized out')
                        check_filter_match(page)
                        check_circle(page,'catalogue-hero-title')
                        results['interactions'].append({'width':width,'check':'category/search filters, URL reload, history, lesson return, legacy URL normalization, no-match recovery','passed':True})
                context.close()
                print(f'PASS homepage/catalogue layout and interaction checks at {width}px',flush=True)
            consent_cases=[(1440,1100,'index.html','site-page-title',500),(1024,900,'index.html','site-page-title',2200),(768,1024,'tutorials.html','catalogue-hero-title',500),(390,844,'tutorials.html','catalogue-hero-title',500),(320,568,'index.html','site-page-title',500)]
            for width,height,path,target,scroll_y in consent_cases:
                consent_context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce')
                consent_context.route('https://**/*',lambda route:route.abort())
                consent_page=consent_context.new_page()
                response=consent_page.goto(args.base+'/'+path,wait_until='networkidle')
                check(response.status==200,f'{path} {width}: consent-visible response status {response.status}')
                banner=consent_page.locator('#cookie-consent-banner')
                check(banner.is_visible(),f'{path} {width}: fresh context did not show the consent banner')
                consent_page.evaluate('(y)=>scrollTo({top:y,behavior:"instant"})',scroll_y)
                consent_page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                circle=consent_page.locator('#back-to-top')
                check(circle.is_visible(),f'{path} {width} at scrollY={scroll_y}: arrow is hidden with consent visible')
                geometry=circle.evaluate('''e=>{
                  const r=e.getBoundingClientRect(),b=document.querySelector('#cookie-consent-banner').getBoundingClientRect();
                  const intersects=(x,y)=>x.width>0&&x.height>0&&x.left<y.right+7&&x.right>y.left-7&&x.top<y.bottom+7&&x.bottom>y.top-7;
                  const controls=[...document.querySelectorAll('body a[href],body button,body summary,body input,body select,body textarea,body [tabindex]')].filter(x=>x!==e);
                  const controlOverlap=controls.some(x=>[...x.getClientRects()].some(q=>intersects(q,r)));
                  const text=[...document.querySelectorAll('body h1,body h2,body h3,body h4,body h5,body h6,body p,body li,body pre,body figcaption,body td,body th,body blockquote,body label,body dt,body dd,body address')];
                  const textOverlap=text.some(x=>{if(x.contains(e)||!x.getClientRects().length||!intersects(x.getBoundingClientRect(),r))return false;const q=document.createRange();q.selectNodeContents(x);return [...q.getClientRects()].some(z=>intersects(z,r));});
                  return {x:r.x,y:r.y,width:r.width,height:r.height,bannerTop:b.top,bannerOverlap:intersects(b,r),controlOverlap,textOverlap};
                }''')
                check(geometry['width']>=48 and geometry['height']>=48,f'{path} {width}: arrow is too small: {geometry}')
                check(not geometry['bannerOverlap'],f'{path} {width}: arrow overlaps the consent banner: {geometry}')
                check(not geometry['controlOverlap'] and not geometry['textOverlap'],f'{path} {width}: arrow covers content or an interactive control: {geometry}')
                circle.focus()
                consent_page.keyboard.press('Enter')
                consent_page.wait_for_function('(id)=>location.hash==="#"+id&&document.activeElement?.id===id&&scrollY<300',arg=target)
                results['interactions'].append({'page':path,'width':width,'check':'consent-visible safe arrow and keyboard return','passed':True,'scrollY':scroll_y,'x':geometry['x'],'y':geometry['y']})
                consent_context.close()
            context=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False,reduced_motion='reduce')
            context.route('https://**/*',lambda route:route.abort())
            page=context.new_page()
            page.goto(args.base+'/tutorials.html')
            check(visible_cards(page).count()==58,'Catalogue hides lessons without JavaScript')
            check(page.locator('#catalogue-level, #catalogue-format, .hc-card-prerequisite, .hc-card-level').count()==0,'Simplified catalogue regressed without JavaScript')
            first_card=visible_cards(page).first
            lesson=first_card.locator('h3 a.hc-card-link').get_attribute('href')
            check(lesson and first_card.locator('a').count()==1,'No-JavaScript catalogue card lacks its single title link')
            title=first_card.locator('h3 a.hc-card-link')
            title.evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})')
            box=title.bounding_box()
            check(bool(box),'No-JavaScript title has no visible pointer target')
            page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
            page.wait_for_url('**/'+lesson)
            check(page.url.endswith('/'+lesson),'No-JavaScript title link did not open the lesson natively')
            page.go_back(wait_until='networkidle')
            image=visible_cards(page).first.locator('img')
            image.evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})')
            box=image.bounding_box()
            check(bool(box),'No-JavaScript card image has no visible pointer target')
            page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
            page.wait_for_url('**/'+lesson)
            check(page.url.endswith('/'+lesson),'No-JavaScript image surface did not open the lesson natively')
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
