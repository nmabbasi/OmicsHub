#!/usr/bin/env python3
"""Comprehensive site audit: images, links, content quality, em dashes, AdSense."""
import re, os, glob

print("=" * 70)
print("COMPREHENSIVE OMICSHUB SITE AUDIT")
print("=" * 70)

errors = []
warnings = []

# ===== 1. CHECK ALL TUTORIAL IMAGES EXIST =====
print("\n--- 1. TUTORIAL IMAGE VERIFICATION ---")
with open("index.html", "r", encoding="utf-8") as f:
    index = f.read()

images = re.findall(r'<img[^>]+src="(images/[^"]+)"', index)
unique_images = sorted(set(images))
missing = [img for img in unique_images if not os.path.exists(img)]
print(f"  Unique images referenced in index.html: {len(unique_images)}")
if missing:
    for m in missing:
        errors.append(f"MISSING IMAGE: {m}")
        print(f"  ❌ MISSING: {m}")
else:
    print(f"  ✅ All {len(unique_images)} images exist on disk.")

# ===== 2. CHECK GENERATED TUTORIAL HTML PAGES =====
print("\n--- 2. GENERATED TUTORIAL HTML PAGES ---")
tutorial_htmls = [f for f in glob.glob("*.html") if f not in [
    "index.html", "old_index.html", "start-here.html", "services.html",
    "about.html", "contact.html", "404.html", "success.html",
    "ai_home_cards.html", "ai_grid_cards.html"
]]
print(f"  Total tutorial HTML pages: {len(tutorial_htmls)}")

for html_file in sorted(tutorial_htmls):
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for images in the tutorial page
    page_images = re.findall(r'<img[^>]+src="(images/[^"]+)"', content)
    for img in page_images:
        if not os.path.exists(img):
            errors.append(f"MISSING IMAGE in {html_file}: {img}")
    
    # Check for em dashes
    if '—' in content:
        errors.append(f"EM DASH found in {html_file}")
    
    # Check for title tag
    if not re.search(r'<title>', content):
        errors.append(f"MISSING TITLE in {html_file}")
    
    # Check for meta description
    if not re.search(r'meta.*description', content):
        errors.append(f"MISSING META DESCRIPTION in {html_file}")
    
    # Check for canonical URL
    if not re.search(r'rel="canonical"', content):
        errors.append(f"MISSING CANONICAL in {html_file}")
    
    # Check for H1
    if not re.search(r'<h1', content):
        errors.append(f"MISSING H1 in {html_file}")
    
    # Check for AdSense
    if 'pagead2.googlesyndication.com' not in content:
        errors.append(f"MISSING ADSENSE in {html_file}")
    
    # Check for maintenance block
    if 'Reviewed: September 2026' not in content:
        warnings.append(f"MISSING MAINTENANCE BLOCK in {html_file}")

# ===== 3. CHECK INTERNAL LINKS =====
print("\n--- 3. INTERNAL LINK VERIFICATION ---")
all_links = re.findall(r'href="([^"#]+\.html)"', index)
unique_links = sorted(set(all_links))
broken_links = []
for link in unique_links:
    if not os.path.exists(link):
        broken_links.append(link)
        errors.append(f"BROKEN LINK: {link}")

if broken_links:
    print(f"  ❌ {len(broken_links)} broken links found!")
    for bl in broken_links:
        print(f"     - {bl}")
else:
    print(f"  ✅ All {len(unique_links)} internal links resolve correctly.")

# ===== 4. SITEMAP VERIFICATION =====
print("\n--- 4. SITEMAP VERIFICATION ---")
with open("sitemap.xml", "r", encoding="utf-8") as f:
    sitemap = f.read()
sitemap_urls = re.findall(r'<loc>(.*?)</loc>', sitemap)
print(f"  URLs in sitemap: {len(sitemap_urls)}")
if len(sitemap_urls) == 67:
    print("  ✅ Sitemap count is correct (67).")
else:
    errors.append(f"SITEMAP COUNT WRONG: {len(sitemap_urls)} (expected 67)")

# ===== 5. EM DASH CHECK (ALL FILES) =====
print("\n--- 5. EM DASH VERIFICATION ---")
em_dash_files = []
for f in glob.glob("*.html") + glob.glob("pages/*.html") + glob.glob("lessons/*.md"):
    try:
        with open(f, "r", encoding="utf-8") as fh:
            if '—' in fh.read():
                em_dash_files.append(f)
    except: pass
if em_dash_files:
    for edf in em_dash_files:
        errors.append(f"EM DASH found in {edf}")
    print(f"  ❌ Em dashes found in {len(em_dash_files)} files")
else:
    print("  ✅ No em dashes found in any file.")

# ===== 6. ADSENSE & ADS.TXT CHECK =====
print("\n--- 6. ADSENSE & ADS.TXT CHECK ---")
if os.path.exists("ads.txt"):
    with open("ads.txt", "r") as f:
        print(f"  ads.txt content: {f.read().strip()}")
    print("  ✅ ads.txt exists.")
else:
    errors.append("MISSING: ads.txt")

# ===== 7. ROBOTS.TXT CHECK =====
print("\n--- 7. ROBOTS.TXT CHECK ---")
if os.path.exists("robots.txt"):
    with open("robots.txt", "r") as f:
        print(f"  {f.read().strip()}")
    print("  ✅ robots.txt exists.")
else:
    errors.append("MISSING: robots.txt")

# ===== 8. LEGAL PAGES CHECK =====
print("\n--- 8. LEGAL PAGES CHECK ---")
legal = ["pages/privacy.html", "pages/terms.html", "pages/disclaimer.html", "pages/cookie.html"]
for lp in legal:
    if os.path.exists(lp):
        print(f"  ✅ {lp} exists")
    else:
        errors.append(f"MISSING LEGAL PAGE: {lp}")

# ===== 9. TUTORIAL WORD COUNT AUDIT =====
print("\n--- 9. TUTORIAL WORD COUNTS ---")
md_files = sorted(glob.glob("lessons/*.md"))
under_700 = []
for md in md_files:
    with open(md, "r", encoding="utf-8") as f:
        words = len(f.read().split())
    if words < 700:
        under_700.append((md, words))

if under_700:
    print(f"  ⚠️  {len(under_700)} tutorials still under 700 words:")
    for path, wc in under_700:
        warnings.append(f"SHORT TUTORIAL: {path} ({wc} words)")
        print(f"     - {os.path.basename(path)}: {wc} words")
else:
    print("  ✅ All tutorials are 700+ words.")

# ===== 10. TUTORIAL CARD COUNTS =====
print("\n--- 10. TUTORIAL CARD COUNTS ---")
home_cards = len(re.findall(r'<article class="tutorial-card', index))
grid_cards = len(re.findall(r'<article class="tutorial-grid-card', index))
print(f"  Homepage grid cards: {home_cards}")
print(f"  All Tutorials grid cards: {grid_cards}")

# ===== 11. CATEGORY BUTTONS CHECK =====
print("\n--- 11. CATEGORY FILTER BUTTONS ---")
cat_buttons = re.findall(r'data-category="([^"]+)"', index)
unique_cats = sorted(set(cat_buttons))
print(f"  Categories found: {len(unique_cats)}")
for c in unique_cats:
    print(f"    - {c}")

# ===== 12. IMAGE ALT TEXT CHECK =====
print("\n--- 12. IMAGE ALT TEXT AUDIT ---")
all_imgs = re.findall(r'<img([^>]+)>', index)
missing_alt = [img for img in all_imgs if 'alt=' not in img]
if missing_alt:
    errors.append(f"{len(missing_alt)} images missing alt text")
    print(f"  ❌ {len(missing_alt)} images missing alt text")
else:
    print(f"  ✅ All images have alt text.")

# ===== FINAL SUMMARY =====
print("\n" + "=" * 70)
print("AUDIT SUMMARY")
print("=" * 70)
print(f"  ❌ Errors:   {len(errors)}")
print(f"  ⚠️  Warnings: {len(warnings)}")

if errors:
    print("\n--- ERRORS (must fix) ---")
    for e in errors:
        print(f"  ❌ {e}")

if warnings:
    print("\n--- WARNINGS (should review) ---")
    for w in warnings:
        print(f"  ⚠️  {w}")

if not errors and not warnings:
    print("\n  🎉 PERFECT SCORE: The site passes all checks!")
elif not errors:
    print("\n  ✅ No critical errors. Warnings are informational.")
