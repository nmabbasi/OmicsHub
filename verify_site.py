import os
import glob
from bs4 import BeautifulSoup
import re

base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"

# Check 1: Broken Links and Missing Images
print("--- 1. Broken Links & Images Check ---")
html_files = glob.glob(os.path.join(base_dir, "*.html"))
missing_assets = []
broken_links = []
missing_alts = []

for filepath in html_files:
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # Check images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith(('http', 'data:', '//')):
                # Check if asset exists
                asset_path = os.path.join(base_dir, src)
                if not os.path.exists(asset_path):
                    missing_assets.append((filename, src))
            
            # Check alt text
            if not img.get('alt'):
                missing_alts.append((filename, src))
                
        # Check links
        for a in soup.find_all('a'):
            href = a.get('href')
            if href and not href.startswith(('http', 'mailto:', 'tel:', '#', 'javascript:')):
                # Remove query params or fragments
                href_clean = href.split('#')[0].split('?')[0]
                if href_clean:
                    link_path = os.path.join(base_dir, href_clean)
                    if not os.path.exists(link_path):
                        broken_links.append((filename, href))

if missing_assets:
    print(f"❌ Found {len(missing_assets)} missing images/assets:")
    for f, a in missing_assets:
        print(f"  - {f}: {a}")
else:
    print("✅ All local images and assets exist!")

if broken_links:
    print(f"❌ Found {len(broken_links)} broken internal links:")
    for f, l in set(broken_links):
        print(f"  - {f}: {l}")
else:
    print("✅ All internal links are valid!")

if missing_alts:
    print(f"⚠️ Found {len(missing_alts)} images missing 'alt' text (important for SEO/AdSense).")
else:
    print("✅ All images have alt text!")

# Check 2: Tutorial Word Count (AdSense readiness)
print("\n--- 2. Content Length Check (AdSense Readiness) ---")
tutorials = []
for filepath in html_files:
    filename = os.path.basename(filepath)
    if filename not in ['index.html', 'about.html', 'contact.html', 'services.html', 'start-here.html', 'success.html', '404.html']:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            # Assuming main content is in <article> or <main>
            main_content = soup.find('article')
            if not main_content:
                main_content = soup.find('main')
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                word_count = len(re.findall(r'\w+', text))
                tutorials.append((filename, word_count))

short_tutorials = [t for t in tutorials if t[1] < 600]
if short_tutorials:
    print(f"❌ Found {len(short_tutorials)} tutorials with < 600 words (may hurt AdSense approval):")
    for t in short_tutorials:
        print(f"  - {t[0]}: {t[1]} words")
else:
    print(f"✅ All {len(tutorials)} tutorials have sufficient word count (> 600 words) for AdSense!")

# Check 3: Essential AdSense Pages
print("\n--- 3. AdSense Policy Pages & Files ---")
required_files = ['ads.txt', 'pages/privacy.html', 'pages/terms.html', 'pages/cookie.html']
missing_policies = []
for req in required_files:
    if not os.path.exists(os.path.join(base_dir, req)):
        missing_policies.append(req)

if missing_policies:
    print(f"❌ Missing required AdSense files: {missing_policies}")
else:
    print("✅ All required AdSense policy pages (Privacy, Terms, Cookie, ads.txt) are present!")
