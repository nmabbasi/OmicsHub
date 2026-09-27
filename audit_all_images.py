import os
import re
import glob

print("=" * 70)
print("COMPREHENSIVE IMAGE CONSISTENCY AUDIT")
print("=" * 70)

# 1. Catalog all image files and their dimensions
print("\n### 1. IMAGE FILE INVENTORY ###")
image_files = set()
for ext in ['*.webp', '*.jpg', '*.png']:
    for f in glob.glob(f'images/{ext}'):
        image_files.add(f)
print(f"Total image files in images/: {len(image_files)}")

# 2. Check tutorials.html grid cards
print("\n### 2. TUTORIALS.HTML GRID CARD IMAGES ###")
with open('tutorials.html', 'r') as f:
    tut_content = f.read()

# Extract all img tags from tutorial grid cards
grid_imgs = re.findall(r'<div class="aspect-video[^"]*">(.*?)</div>', tut_content)
grid_img_classes = []
grid_img_srcs = []
issues = []

for i, div_content in enumerate(grid_imgs):
    img_match = re.search(r'<img[^>]+>', div_content)
    if img_match:
        img_tag = img_match.group(0)
        cls_match = re.search(r'class="([^"]+)"', img_tag)
        src_match = re.search(r'src="([^"]+)"', img_tag)
        cls = cls_match.group(1) if cls_match else "NO CLASS"
        src = src_match.group(1) if src_match else "NO SRC"
        grid_img_classes.append(cls)
        grid_img_srcs.append(src)
        
        # Check if file exists
        if not os.path.exists(src):
            issues.append(f"  MISSING FILE: {src}")
        
        # Check class consistency
        expected = "w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
        if cls != expected:
            issues.append(f"  INCONSISTENT CLASS on {src}: '{cls}'")

unique_classes = set(grid_img_classes)
print(f"Total grid card images: {len(grid_img_srcs)}")
print(f"Unique class sets: {len(unique_classes)}")
for c in unique_classes:
    count = grid_img_classes.count(c)
    print(f"  [{count}x] {c}")

if issues:
    print("ISSUES:")
    for issue in issues:
        print(issue)
else:
    print("✅ All grid card images are consistent")

# 3. Check index.html homepage cards
print("\n### 3. INDEX.HTML HOMEPAGE CARD IMAGES ###")
with open('index.html', 'r') as f:
    idx_content = f.read()

home_imgs = re.findall(r'<div class="aspect-video[^"]*">(.*?)</div>', idx_content)
home_issues = []
home_classes = []

for div_content in home_imgs:
    img_match = re.search(r'<img[^>]+>', div_content)
    if img_match:
        img_tag = img_match.group(0)
        cls_match = re.search(r'class="([^"]+)"', img_tag)
        src_match = re.search(r'src="([^"]+)"', img_tag)
        cls = cls_match.group(1) if cls_match else "NO CLASS"
        src = src_match.group(1) if src_match else "NO SRC"
        home_classes.append(cls)
        
        if not os.path.exists(src):
            home_issues.append(f"  MISSING FILE: {src}")
        
        expected = "w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
        if cls != expected:
            home_issues.append(f"  INCONSISTENT CLASS on {src}: '{cls}'")

print(f"Total homepage card images: {len(home_classes)}")
unique_home = set(home_classes)
for c in unique_home:
    count = home_classes.count(c)
    print(f"  [{count}x] {c}")

if home_issues:
    print("ISSUES:")
    for issue in home_issues:
        print(issue)
else:
    print("✅ All homepage card images are consistent")

# 4. Check all tutorial inner page hero images
print("\n### 4. TUTORIAL INNER PAGE HERO IMAGES ###")
tutorial_files = sorted(glob.glob('tutorials/*.html'))
hero_issues = []
hero_classes = []
hero_containers = []
missing_heroes = []

for tf in tutorial_files:
    basename = os.path.basename(tf)
    with open(tf, 'r') as f:
        content = f.read()
    
    # Find hero image (loading="eager")
    hero_match = re.search(r'<img[^>]+loading="eager"[^>]*>', content)
    if hero_match:
        img_tag = hero_match.group(0)
        cls_match = re.search(r'class="([^"]+)"', img_tag)
        src_match = re.search(r'src="([^"]+)"', img_tag)
        cls = cls_match.group(1) if cls_match else "NO CLASS"
        src = src_match.group(1) if src_match else "NO SRC"
        hero_classes.append(cls.strip())
        
        # Check if file exists
        actual_path = src.replace('../', '')
        if not os.path.exists(actual_path):
            hero_issues.append(f"  MISSING FILE: {actual_path} (in {basename})")
        
        # Check onerror fallback
        if 'onerror' in img_tag:
            hero_issues.append(f"  HAS ONERROR FALLBACK: {basename} -> means image might be missing/unreliable")
    else:
        missing_heroes.append(basename)
    
    # Find hero container div
    container_match = re.search(r'<div class="([^"]*mb-12 rounded-2xl[^"]*)">', content)
    if container_match:
        hero_containers.append(container_match.group(1))

unique_hero_classes = set(hero_classes)
unique_containers = set(hero_containers)

print(f"Total tutorial pages: {len(tutorial_files)}")
print(f"Pages with hero image: {len(hero_classes)}")
print(f"Pages missing hero image: {len(missing_heroes)}")
if missing_heroes:
    for m in missing_heroes:
        print(f"  ⚠ No hero image: {m}")

print(f"\nUnique hero image class sets: {len(unique_hero_classes)}")
for c in unique_hero_classes:
    count = hero_classes.count(c)
    print(f"  [{count}x] '{c}'")

print(f"\nUnique hero container class sets: {len(unique_containers)}")
for c in unique_containers:
    count = hero_containers.count(c)
    print(f"  [{count}x] '{c}'")

if hero_issues:
    print("\nISSUES:")
    for issue in hero_issues:
        print(issue)
else:
    print("\n✅ All hero images are consistent")

# 5. Check for images referenced but not existing
print("\n### 5. MISSING IMAGE FILES ###")
all_html = glob.glob('*.html') + glob.glob('tutorials/*.html') + glob.glob('pages/*.html')
all_refs = set()
for hf in all_html:
    with open(hf, 'r') as f:
        content = f.read()
    srcs = re.findall(r'src="([^"]*\.(webp|jpg|png))"', content)
    for src, ext in srcs:
        # Normalize path
        if hf.startswith('tutorials/') or hf.startswith('pages/'):
            actual = src.replace('../', '')
        else:
            actual = src
        all_refs.add((actual, hf))

missing = []
for ref, source in all_refs:
    if not os.path.exists(ref) and not ref.startswith('http'):
        missing.append(f"  {ref} (referenced in {source})")

if missing:
    print(f"Missing files: {len(missing)}")
    for m in sorted(missing):
        print(m)
else:
    print("✅ All referenced images exist on disk")

# 6. Check ai_home_cards.html and ai_grid_cards.html
print("\n### 6. AI CARD FILES ###")
for card_file in ['ai_home_cards.html', 'ai_grid_cards.html']:
    if os.path.exists(card_file):
        with open(card_file, 'r') as f:
            content = f.read()
        ai_imgs = re.findall(r'<img[^>]+>', content)
        ai_classes = []
        ai_issues = []
        for img_tag in ai_imgs:
            cls_match = re.search(r'class="([^"]+)"', img_tag)
            src_match = re.search(r'src="([^"]+)"', img_tag)
            cls = cls_match.group(1) if cls_match else "NO CLASS"
            src = src_match.group(1) if src_match else "NO SRC"
            ai_classes.append(cls)
            if not os.path.exists(src) and not src.startswith('http'):
                ai_issues.append(f"  MISSING: {src}")
        
        unique_ai = set(ai_classes)
        print(f"\n{card_file}: {len(ai_imgs)} images")
        for c in unique_ai:
            count = ai_classes.count(c)
            print(f"  [{count}x] '{c}'")
        if ai_issues:
            for i in ai_issues:
                print(i)

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
