from pathlib import Path
from bs4 import BeautifulSoup
import re, json
ROOT=Path('/home/ubuntu/OmicsHub')
errors=[]; warnings=[]
html_files=sorted(ROOT.glob('*.html'))
tutorial_ids={p.stem for p in html_files if p.name not in {'index.html','about.html','contact.html','services.html','start-here.html','success.html'}}

def fail(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

for p in html_files:
    text=p.read_text(errors='ignore'); soup=BeautifulSoup(text,'html.parser')
    if 'Coming Soon' in text or 'currently in active development' in text:
        fail(f'placeholder remains: {p.name}')
    if p.name in tutorial_ids:
        cans=soup.find_all('link',rel='canonical')
        if len(cans)!=1: fail(f'{p.name}: canonical count {len(cans)}')
        elif cans[0].get('href') != f'https://theomicshub.com/{p.stem}.html': fail(f'{p.name}: wrong canonical {cans[0].get("href")}')
        if soup.find(string=re.compile(r'\\n\\n')): fail(f'{p.name}: literal newline artifact')
        if text.count('application/ld+json') < 1: fail(f'{p.name}: missing JSON-LD')
        for required in ['Knowledge Check & Assessment','Concept Verification','Practical Execution','Troubleshooting']:
            if required not in text: fail(f'{p.name}: missing {required}')
        if not re.search(r'nav-desktop-tutorials"(?: aria-current="page")? class="px-4 py-2 text-sm font-semibold bg-blue-600', text):
            fail(f'{p.name}: Tutorials desktop tab not active')
        if re.search(r'nav-desktop-home"(?: aria-current="page")? class="px-4 py-2 text-sm font-semibold bg-blue-600', text):
            fail(f'{p.name}: Home incorrectly active')
        if 'nav-desktop-starthere" class="px-4 py-2 text-sm font-semibold bg-blue-600' in text:
            fail(f'{p.name}: Start Here incorrectly active')
    for href in re.findall(r'(?:href|src)=["\']([^"\']+)', text):
        if href.startswith(('http://','https://','mailto:','#','javascript:','data:')): continue
        clean=href.split('#')[0].split('?')[0]
        if not clean: continue
        if clean.endswith('.md'): fail(f'{p.name}: stale markdown link {clean}')
        target=ROOT/clean
        if not target.exists() and not clean.endswith(('.woff','.woff2')): fail(f'{p.name}: missing local resource {clean}')

idx=(ROOT/'index.html').read_text(); start=(ROOT/'start-here.html').read_text()
if not re.search(r'nav-desktop-home"(?: aria-current="page")? class="px-4 py-2 text-sm font-semibold bg-blue-600', idx): fail('index: Home tab not active')
if not re.search(r'nav-desktop-starthere"(?: aria-current="page")? class="px-4 py-2 text-sm font-semibold bg-blue-600', start): fail('start-here: Start Here tab not active')
for slug in ['computer-data-fundamentals','biological-data-formats','quality-control-fundamentals','git-github-bioinformatics','python-fundamentals-bioinformatics','r-tidyverse-fundamentals','statistics-for-bioinformatics','experimental-design-batch-effects','reference-genomes-annotation','data-visualization-fundamentals','reproducible-project-structure','research-reporting-interpretation']:
    if f'href="{slug}.html"' not in start: fail(f'start-here: missing foundation link {slug}')
if not (ROOT/'ads.txt').exists(): fail('missing ads.txt')
if not (ROOT/'images/favicon.svg').exists(): fail('missing favicon.svg')
robots=(ROOT/'robots.txt').read_text()
if 'Sitemap: https://theomicshub.com/sitemap.xml' not in robots: fail('robots: missing sitemap')
# Source lessons should be clean too.
for p in (ROOT/'lessons').glob('*.md'):
    t=p.read_text(errors='ignore')
    if 'Coming Soon' in t or '.md)' in t: fail(f'{p.name}: source placeholder/stale link')

print(json.dumps({'html_pages':len(html_files),'tutorial_pages':len(tutorial_ids),'errors':errors,'warnings':warnings},indent=2))
raise SystemExit(1 if errors else 0)
