import glob
import os
import re

print("--- 1. SITEMAP VALIDATION ---")
with open("sitemap.xml", "r", encoding="utf-8") as f:
    sitemap_content = f.read()

urls = re.findall(r'<loc>(.*?)</loc>', sitemap_content)
print(f"Total URLs in sitemap: {len(urls)}")
if len(urls) != 67:
    print("❌ ERROR: Sitemap does not have 67 URLs!")
else:
    print("✅ Sitemap URL count is correct (67).")

print("\n--- 2. INDEX.HTML GRID VALIDATION ---")
with open("index.html", "r", encoding="utf-8") as f:
    index_content = f.read()

home_grid_match = re.search(r'id="tutorials-list">(.*?)<!-- INJECT_TUTORIALS_END -->', index_content, re.DOTALL)
if home_grid_match:
    home_cards = re.findall(r'<article class="tutorial-card', home_grid_match.group(1))
    print(f"Total cards in Homepage Grid: {len(home_cards)}")
    if len(home_cards) != 58: print("❌ ERROR: Homepage grid does not have 58 cards!")
    else: print("✅ Homepage grid count is correct (58).")

all_grid_match = re.search(r'id="all-tutorials-list">(.*?)<!-- INJECT_ALL_TUTORIALS_END -->', index_content, re.DOTALL)
if all_grid_match:
    all_cards = re.findall(r'<article class="tutorial-grid-card', all_grid_match.group(1))
    print(f"Total cards in All Tutorials Tab: {len(all_cards)}")
    if len(all_cards) != 58: print("❌ ERROR: All Tutorials tab does not have 58 cards!")
    else: print("✅ All Tutorials tab count is correct (58).")

print("\n--- 3. BUTTON COUNT VALIDATION ---")
buttons = re.findall(r'aria-label="58 tutorials">58</span>', index_content)
if len(buttons) >= 2:
    print("✅ All Tutorials button correctly displays '58'.")
else:
    print("❌ ERROR: All Tutorials button count is wrong!")

print("\n--- 4. IMAGE LINK VALIDATION ---")
images_in_index = re.findall(r'<img src="(images/.*?)"', index_content)
missing_images = []
for img in set(images_in_index):
    if not os.path.exists(img):
        missing_images.append(img)
if missing_images:
    print(f"❌ ERROR: Found {len(missing_images)} missing images referenced in index.html!")
    for mi in missing_images: print(f"  - {mi}")
else:
    print("✅ All images referenced in index.html physically exist on disk.")

print("\n--- 5. ADSENSE TAG VALIDATION ---")
html_files = glob.glob("*.html") + glob.glob("pages/*.html")
missing_adsense = []
adsense_script = "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"
for hf in html_files:
    try:
        with open(hf, "r", encoding="utf-8") as f:
            content = f.read()
            if adsense_script not in content:
                missing_adsense.append(hf)
    except Exception as e:
        pass
if missing_adsense:
    print(f"❌ ERROR: Missing AdSense tags in {len(missing_adsense)} files!")
    for ma in missing_adsense: print(f"  - {ma}")
else:
    print(f"✅ AdSense tag is successfully embedded in all {len(html_files)} HTML files.")

