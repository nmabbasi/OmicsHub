import glob
import re
import os

all_html = glob.glob('**/*.html', recursive=True)
all_html_names = set([os.path.basename(f) for f in all_html])
all_html_paths = set(all_html)

errors = []
missing_alt = []

for file in all_html:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for missing internal links
    links = re.findall(r'href="([^"]+)"', content)
    for link in links:
        if link.startswith('http') or link.startswith('#') or link.startswith('mailto:') or link == '':
            continue
        
        # Clean query strings and anchors
        clean_link = link.split('?')[0].split('#')[0]
        
        # Resolve path
        base_dir = os.path.dirname(file)
        target_path = os.path.normpath(os.path.join(base_dir, clean_link))
        
        if not os.path.exists(target_path):
            errors.append(f"Broken link in {file}: {link} -> {target_path} does not exist.")

    # Check for images without alt tags
    img_tags = re.findall(r'<img[^>]+>', content)
    for img in img_tags:
        if 'alt=' not in img:
            errors.append(f"Missing alt tag on image in {file}: {img}")

if errors:
    for e in set(errors):
        print(e)
else:
    print("No broken links or missing alt tags found!")
