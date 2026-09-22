import urllib.request
import urllib.error
from html.parser import HTMLParser
from urllib.parse import urljoin

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        elif tag == 'link' and 'href' in attrs and attrs.get('rel') == 'stylesheet':
            self.assets.append(attrs['href'])
        elif tag == 'img' and 'src' in attrs:
            self.assets.append(attrs['src'])
        elif tag == 'script' and 'src' in attrs:
            self.assets.append(attrs['src'])

def check_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.status == 200, ""
    except urllib.error.URLError as e:
        return False, str(e)

base_url = "https://theomicshub.com/"
pages_to_check = [
    "", 
    "tutorials.html",
    "tutorials/16s-rrna-prokka-annotation.html",
    "about.html",
    "contact.html"
]

print("Starting live site validation...")
all_passed = True

for page in pages_to_check:
    url = urljoin(base_url, page)
    print(f"\nChecking page: {url}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            parser = LinkParser()
            parser.feed(html)
            
            print(f"  [OK] Page loads successfully.")
            
            # Check a sample of assets
            for asset in parser.assets[:5]:  # Just check first 5 to be quick
                asset_url = urljoin(url, asset)
                if not asset_url.startswith('http'):
                    continue
                ok, err = check_url(asset_url)
                if ok:
                    print(f"  [OK] Asset loaded: {asset}")
                else:
                    print(f"  [FAIL] Asset failed: {asset} - {err}")
                    all_passed = False
                    
    except urllib.error.URLError as e:
        print(f"  [FAIL] Page failed to load: {url} - {e}")
        all_passed = False

print(f"\nOverall Status: {'PASSED' if all_passed else 'FAILED'}")
