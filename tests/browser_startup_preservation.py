#!/usr/bin/env python3
"""Compare local before/after rendering and static-page navigation; no consent actions."""
import argparse
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from browser_startup_performance import StaticHandler

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline',required=True,type=Path)
    ap.add_argument('--candidate',type=Path,default=ROOT)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    servers=[];bases={};results={'visual_cases':[],'interactions':[],'errors':[],'consent_actions':False}
    routes=['index.html','tutorials.html','start-here.html','tutorials/statistics-for-bioinformatics.html','tutorials/data-visualization-fundamentals.html','tutorials/hpc-submission-part1.html','tutorials/mcp-zotero.html','tutorials/autonomous-research-orchestrator.html']
    def check(value,message):
        if not value:raise AssertionError(message)
    def ready(page,base,path):
        response=page.goto(base+'/'+path,wait_until='load');check(response.status==200,path)
        if path.startswith('tutorials/'):page.wait_for_selector('html[data-tutorial-code-ready=true]')
        page.evaluate('document.fonts.ready')
        page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
        page.wait_for_function("[...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth}).every(i=>i.complete)")
        page.evaluate("Promise.all([...document.images].filter(i=>{const r=i.getBoundingClientRect();return r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth}).map(i=>i.decode().catch(()=>{})))")
    try:
        for label,root in [('baseline',args.baseline),('candidate',args.candidate)]:
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(StaticHandler,root=root.resolve()));server.daemon_threads=True
            threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server);bases[label]=f'http://127.0.0.1:{server.server_port}'
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-background-networking'])
            results['browser_version']=browser.version
            for width in [1440,390]:
                for path in routes:
                    shots={}
                    for label in ['baseline','candidate']:
                        context=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
                        context.route('https://**/*',lambda route:route.abort())
                        page=context.new_page();page.on('pageerror',lambda error:results['errors'].append(str(error)))
                        ready(page,bases[label],path)
                        targets=['top']
                        if path.startswith('tutorials/'):targets+=['code']
                        for target in targets:
                            if target=='code':
                                code=page.locator('[data-code-tabs]').first if page.locator('[data-code-tabs]').count() else page.locator('article pre').first
                                if not code.count():continue
                                code.evaluate("el=>window.scrollTo({top:scrollY+el.getBoundingClientRect().top-120,behavior:'instant'})")
                                page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
                            file=args.output/f'{path.replace("/","_")}-{width}-{target}-{label}.png'
                            page.screenshot(path=str(file),animations='disabled',caret='hide');shots[(label,target)]=file
                        context.close()
                    for target in ['top','code']:
                        if ('baseline',target) not in shots:continue
                        before=Image.open(shots[('baseline',target)]).convert('RGB');after=Image.open(shots[('candidate',target)]).convert('RGB')
                        diff=ImageChops.difference(before,after)
                        pixels=sum(1 for pixel in diff.getdata() if pixel!=(0,0,0))
                        max_delta=max(high for _,high in diff.getextrema())
                        # Only byte-pinned catalogue thumbnail clip edges get a
                        # tiny raster allowance. Every lesson remains pixel-exact.
                        raster_variance=path=='tutorials.html' and max_delta<=5 and pixels<=int(before.width*before.height*0.0001)
                        results['visual_cases'].append({'path':path,'width':width,'target':target,'changed_pixels':pixels,'max_channel_delta':max_delta,'total_pixels':before.width*before.height,'identical':pixels==0,'accepted_subpixel_raster_variance':pixels>0 and raster_variance,'baseline':str(shots[('baseline',target)]),'candidate':str(shots[('candidate',target)])})
                        print(f'{path} {width} {target}: {pixels} changed pixels',flush=True)
            context=browser.new_context(viewport={'width':390,'height':1000})
            context.route('https://**/*',lambda route:route.abort())
            page=context.new_page();page.on('pageerror',lambda error:results['errors'].append(str(error)))
            ready(page,bases['candidate'],'tutorials/statistics-for-bioinformatics.html')
            trigger=page.locator('button[aria-controls=mobile-menu]');menu=page.locator('#mobile-menu')
            trigger.click();check(trigger.get_attribute('aria-expanded')=='true','Mobile open state')
            page.keyboard.press('Escape');check(trigger.get_attribute('aria-expanded')=='false','Mobile Escape dismissal')
            check(trigger.evaluate('el=>document.activeElement===el'),'Mobile Escape focus')
            trigger.click();page.locator('#tutorial-title').click();check(trigger.get_attribute('aria-expanded')=='false','Mobile outside dismissal')
            trigger.click();page.locator('#mobile-menu a[href="../tutorials.html"]').click()
            page.wait_for_url('**/tutorials.html');check('hidden' in page.locator('#mobile-menu').get_attribute('class'),'Mobile destination menu closed')
            results['interactions']+=['mobile open','Escape close and focus','outside-click close','native mobile menu catalogue link']
            legal=[p for p in (args.candidate/'tutorials').glob('*.html') if 'id="legal-menu-button"' in p.read_text()]
            page.set_viewport_size({'width':1440,'height':1000})
            for path in legal:
                ready(page,bases['candidate'],'tutorials/'+path.name)
                button=page.locator('#legal-menu-button');button.click();check(button.get_attribute('aria-expanded')=='true',path.name+' Legal open')
                page.keyboard.press('Escape');check(button.get_attribute('aria-expanded')=='false',path.name+' Legal close')
                check(button.evaluate('el=>document.activeElement===el'),path.name+' Legal focus')
                results['interactions'].append(path.name+': Legal click/Escape/focus')
            context.close();browser.close()
        check(not results['errors'],str(results['errors']))
        # Only the explicitly recorded catalogue subpixel case has a tolerance.
        mismatches=[r for r in results['visual_cases'] if not r['identical'] and not r['accepted_subpixel_raster_variance']]
        results['visual_mismatches']=mismatches
        check(not mismatches,'Before/after pixel mismatch: '+str([(r['path'],r['width'],r['target'],r['changed_pixels']) for r in mismatches]))
        results['passed']=True
    except Exception as error:
        results['passed']=False;results['failure']=str(error);raise
    finally:
        for server in servers:server.shutdown();server.server_close()
        (args.output/'preservation-results.json').write_text(json.dumps(results,indent=2)+'\n')
        print('Evidence: '+str(args.output/'preservation-results.json'),flush=True)

if __name__=='__main__':main()
