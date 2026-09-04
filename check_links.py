import os
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def check_broken_links():
    html_files = glob.glob('**/*.html', recursive=True)
    valid_files = set([os.path.basename(f) for f in html_files])
    
    # Also valid are #anchors, mailto:, http/https links, and images/css/js
    valid_assets = set([os.path.basename(f) for f in glob.glob('**/*.*', recursive=True)])
    
    broken_links = []
    
    for file in html_files:
        with open(file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Skip external links, mailto, tel, anchors
            if href.startswith(('http://', 'https://', 'mailto:', 'tel:', '#')):
                continue
                
            # Parse internal URL
            parsed = urlparse(href)
            path = parsed.path
            
            # If path is empty, it's just an anchor on current page which is skipped above or handled
            if not path:
                continue
                
            basename = os.path.basename(path)
            
            if basename and basename not in valid_files and basename not in valid_assets:
                broken_links.append(f"Broken link '{href}' found in {file}")
                
    return broken_links

if __name__ == '__main__':
    broken = check_broken_links()
    if broken:
        for b in broken:
            print(b)
        print(f"Total broken links: {len(broken)}")
    else:
        print("All internal links are valid!")
