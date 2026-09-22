import os
import glob
from html.parser import HTMLParser

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs = dict(attrs)
            if 'href' in attrs:
                self.links.append(attrs['href'])

tutorials_dir = "tutorials"
tutorial_files = glob.glob(f"{tutorials_dir}/*.html")

all_good = True
broken_links = []

# Get list of valid tutorial filenames
valid_tutorials = [os.path.basename(f) for f in tutorial_files]

for file_path in tutorial_files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    parser = LinkParser()
    parser.feed(content)
    
    for link in parser.links:
        # Ignore external links, anchor links, and root-level links
        if link.startswith('http') or link.startswith('mailto:') or link.startswith('#') or link.startswith('../'):
            continue
            
        # Ignore query params or hash fragments in the file check
        file_part = link.split('?')[0].split('#')[0]
        
        # Check if the file exists in the valid tutorials list
        if file_part not in valid_tutorials:
            broken_links.append((file_path, link))
            all_good = False

if all_good:
    print("SUCCESS: All internal tutorial links are perfectly valid and point to existing files!")
else:
    print(f"FOUND {len(broken_links)} BROKEN LINKS:")
    for file, link in broken_links:
        print(f"  In {file}: Broken link -> {link}")
