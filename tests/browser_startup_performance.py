#!/usr/bin/env python3
"""Bounded before/after static lesson profiling; local copies only, no consent actions.

Fresh browser contexts and gzip responses approximate public asset delivery.
External HTTPS is blocked through CDP, not Playwright routing, so normal caching
remains available. Controlled numbers are not production/owner-device timings.
"""
from __future__ import annotations
import argparse
from collections import Counter
from functools import partial
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
import mimetypes
from pathlib import Path
import statistics
import threading
from urllib.parse import unquote, urlsplit
from playwright.sync_api import sync_playwright

INIT = """(() => {
  window.__startup = {dcl:null, ready:null, load:null, longtasks:[], shifts:[]};
  document.addEventListener('DOMContentLoaded',()=>window.__startup.dcl=performance.now(),{once:true});
  document.addEventListener('tutorial-code-ready',()=>window.__startup.ready=performance.now(),{once:true});
  addEventListener('load',()=>window.__startup.load=performance.now(),{once:true});
  try { new PerformanceObserver(list=>list.getEntries().forEach(e=>window.__startup.longtasks.push({start:e.startTime,duration:e.duration}))).observe({type:'longtask',buffered:true}); } catch (_) {}
  try { new PerformanceObserver(list=>list.getEntries().filter(e=>!e.hadRecentInput).forEach(e=>window.__startup.shifts.push(e.value))).observe({type:'layout-shift',buffered:true}); } catch (_) {}
})();"""

class StaticHandler(BaseHTTPRequestHandler):
    def __init__(self,*args,root,**kwargs):
        self.root=root
        super().__init__(*args,**kwargs)
    def do_GET(self):
        path=(self.root/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            self.send_error(404);return
        data=path.read_bytes()
        content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        tag='"'+hashlib.sha256(data).hexdigest()+'"'
        if self.headers.get('If-None-Match')==tag:
            self.send_response(304);self.send_header('ETag',tag);self.end_headers();return
        compress='gzip' in self.headers.get('Accept-Encoding','') and (content_type.startswith('text/') or path.suffix in {'.js','.json','.svg'})
        if compress:data=gzip.compress(data,mtime=0)
        self.send_response(200)
        self.send_header('Content-Type',content_type)
        self.send_header('Cache-Control','no-cache' if path.suffix=='.html' else 'public, max-age=600')
        self.send_header('ETag',tag)
        self.send_header('Vary','Accept-Encoding')
        if compress:self.send_header('Content-Encoding','gzip')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):self.send_error(405)
    def log_message(self,*args):pass

def summarize(rows):
    out={}
    for label in sorted({r['label'] for r in rows}):
        for slug in sorted({r['slug'] for r in rows if r['label']==label}):
            for phase in ['cold','warm_reload']:
                group=[r for r in rows if r['label']==label and r['slug']==slug and r['phase']==phase]
                if not group:continue
                metrics={}
                for key in ['dcl_ms','code_ready_ms','load_ms','fcp_ms','long_task_total_ms','largest_long_task_ms','observed_content_two_frames_ms','first_party_encoded_bytes','first_party_decoded_bytes','script_encoded_bytes']:
                    values=sorted(r[key] for r in group if r.get(key) is not None)
                    if values:metrics[key]={'median':statistics.median(values),'min':min(values),'max':max(values),'n':len(values)}
                out[f'{label}:{slug}:{phase}']=metrics
    return out

def measure(browser,base,label,slug,iteration,args):
    context=browser.new_context(viewport={'width':1440,'height':1000})
    context.add_init_script(INIT)
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    cdp=context.new_cdp_session(page)
    cdp.send('Network.enable')
    cdp.send('Network.setBlockedURLs',{'urls':['https://*']})
    cdp.send('Network.setCacheDisabled',{'cacheDisabled':False})
    cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':args.latency_ms,'downloadThroughput':args.mbps*1_000_000/8,'uploadThroughput':1_000_000/8})
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':args.cpu})
    records=[]
    try:
        for phase in ['cold','warm_reload']:
            if phase=='warm_reload' and not args.warm:continue
            cdp.send('Profiler.enable');cdp.send('Profiler.start')
            response=page.goto(base+'/tutorials/'+slug+'.html',wait_until='commit') if phase=='cold' else page.reload(wait_until='commit')
            assert response and response.status==200
            page.wait_for_function('document.documentElement.dataset.tutorialCodeReady === "true"',timeout=30000)
            page.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
            content_ms=page.evaluate('performance.now()')
            page.wait_for_function('document.readyState === "complete"',timeout=30000)
            page.wait_for_timeout(100)
            profile=cdp.send('Profiler.stop')['profile']
            data=page.evaluate("""() => {
              const n=performance.getEntriesByType('navigation')[0];
              return {metrics:window.__startup, nav:n.toJSON(), resources:performance.getEntriesByType('resource').filter(e=>e.name.startsWith(location.origin)).map(e=>({path:new URL(e.name).pathname,initiator:e.initiatorType,start_ms:e.startTime,response_end_ms:e.responseEnd,duration_ms:e.duration,encoded:e.encodedBodySize,decoded:e.decodedBodySize,transferred:e.transferSize})),fcp:performance.getEntriesByName('first-contentful-paint')[0]?.startTime??null,groups:document.querySelectorAll('[data-code-tabs]').length,frames:document.querySelectorAll('article .tutorial-code-frame').length};
            }""")
            by_id={n['id']:n for n in profile['nodes']};function_hits=Counter()
            for hit in profile.get('samples',[]):
                f=by_id[hit]['callFrame'];url=f.get('url','')
                if url.startswith(base):function_hits[(urlsplit(url).path,f.get('functionName') or '(anonymous)',f.get('lineNumber',-1)+1)]+=1
            m=data['metrics'];resources=data['resources']
            row={'label':label,'slug':slug,'iteration':iteration,'phase':phase,'dcl_ms':m['dcl'],'code_ready_ms':m['ready'],'load_ms':m['load'],'fcp_ms':data['fcp'],'observed_content_two_frames_ms':content_ms,'long_task_total_ms':sum(t['duration'] for t in m['longtasks']),'largest_long_task_ms':max((t['duration'] for t in m['longtasks']),default=0),'layout_shift_sum':sum(m['shifts']),'first_party_encoded_bytes':sum(r['encoded'] for r in resources)+data['nav']['encodedBodySize'],'first_party_decoded_bytes':sum(r['decoded'] for r in resources)+data['nav']['decodedBodySize'],'script_encoded_bytes':sum(r['encoded'] for r in resources if r['initiator']=='script'),'resource_count':len(resources),'groups':data['groups'],'copy_frames':data['frames'],'navigation':data['nav'],'resources':resources,'script_profile_self_samples':[{'path':k[0],'function':k[1],'line':k[2],'samples':v} for k,v in function_hits.most_common(15)],'page_errors':list(errors)}
            assert not errors,errors
            records.append(row)
            print(f"{label} {slug} {iteration} {phase}: ready={m['ready']:.1f}ms DCL={m['dcl']:.1f}ms load={m['load']:.1f}ms",flush=True)
    finally:context.close()
    return records

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',action='append',required=True,help='label=/absolute/root; repeat for before/after')
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--trials',type=int,default=5)
    ap.add_argument('--cpu',type=float,default=6)
    ap.add_argument('--latency-ms',type=float,default=100)
    ap.add_argument('--mbps',type=float,default=5)
    ap.add_argument('--warm',action='store_true')
    ap.add_argument('--slug',action='append')
    args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    roots=[(s.split('=',1)[0],Path(s.split('=',1)[1]).resolve()) for s in args.root]
    servers=[];bases={};rows=[]
    output={'kind':'controlled_local_before_after_not_field_timings','cpu_throttle':args.cpu,'latency_ms':args.latency_ms,'bandwidth_mbps':args.mbps,'gzip_text_responses':True,'third_party_https_blocked':True,'cache_allowed':True,'consent_actions':False,'roots':{k:str(v) for k,v in roots},'rows':rows}
    try:
        for label,root in roots:
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(StaticHandler,root=root));server.daemon_threads=True
            threading.Thread(target=server.serve_forever,daemon=True).start();servers.append(server);bases[label]=f'http://127.0.0.1:{server.server_port}'
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-background-networking','--disable-component-update'])
            output['browser_version']=browser.version
            for iteration in range(args.trials):
                order=roots if iteration%2==0 else list(reversed(roots))
                for slug in args.slug or ['statistics-for-bioinformatics','data-visualization-fundamentals','hpc-submission-part1']:
                    for label,_ in order:rows.extend(measure(browser,bases[label],label,slug,iteration+1,args))
            browser.close()
        output['passed']=True
    except Exception as error:
        output['passed']=False;output['error']=str(error);raise
    finally:
        for server in servers:server.shutdown();server.server_close()
        output['summary']=summarize(rows)
        args.output.write_text(json.dumps(output,indent=2)+'\n')
        print('Evidence: '+str(args.output),flush=True)

if __name__=='__main__':main()
