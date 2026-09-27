import os
import re
import glob

# Fix 1: Remove onerror fallbacks from tutorial hero images (all files exist)
# Fix 2: Normalize hero image classes to 'w-full h-auto' consistently
# Fix 3: Fix ai_grid_cards.html to use consistent aspect-video layout

print("=== FIX 1 & 2: Normalize all tutorial hero images ===")
tutorial_files = sorted(glob.glob('tutorials/*.html'))
fixed_count = 0

for tf in tutorial_files:
    with open(tf, 'r') as f:
        content = f.read()
    
    original = content
    
    # Find any img with loading="eager" (hero images)
    def fix_hero_img(match):
        img_tag = match.group(0)
        # Remove onerror attribute
        img_tag = re.sub(r'\s*onerror="[^"]*"', '', img_tag)
        # Normalize classes to just 'w-full h-auto'
        img_tag = re.sub(r'class="[^"]*"', 'class="w-full h-auto"', img_tag)
        return img_tag
    
    # Match hero images - they have loading="eager" or are inside mb-12 rounded-2xl container
    # Some have loading="eager" embedded differently, so let's be broader
    content = re.sub(r'<img[^>]+loading="eager"[^>]*>', fix_hero_img, content)
    
    # Also fix images that have aspect-video in their class (the two problematic pages)
    def fix_aspect_hero(match):
        img_tag = match.group(0)
        img_tag = re.sub(r'\s*onerror="[^"]*"', '', img_tag)
        img_tag = re.sub(r'class="[^"]*"', 'class="w-full h-auto"', img_tag)
        # Make sure loading="eager" is present
        if 'loading=' not in img_tag:
            img_tag = img_tag.replace('>', ' loading="eager" decoding="async">', 1)
        return img_tag

    # Find imgs inside the hero container that DON'T have loading="eager"
    # These are the two pages: ai-coding-cursor-aider.html and hpc-support.html
    def fix_hero_container(match):
        div_tag = match.group(1)
        img_tag = match.group(2)
        img_tag = re.sub(r'\s*onerror="[^"]*"', '', img_tag)
        img_tag = re.sub(r'class="[^"]*"', 'class="w-full h-auto"', img_tag)
        if 'loading=' not in img_tag:
            img_tag = img_tag.rstrip('/>').rstrip('>') 
            if img_tag.endswith('/'):
                img_tag = img_tag[:-1]
            img_tag += ' loading="eager" decoding="async">'
        return div_tag + '\n' + img_tag

    content = re.sub(
        r'(<div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100">)\s*\n?\s*(<img[^>]+>)',
        fix_hero_container,
        content
    )
    
    if content != original:
        with open(tf, 'w') as f:
            f.write(content)
        fixed_count += 1
        print(f"  Fixed: {os.path.basename(tf)}")

print(f"Total files fixed: {fixed_count}")

# Fix 3: Update ai_grid_cards.html
print("\n=== FIX 3: Normalize ai_grid_cards.html ===")
if os.path.exists('ai_grid_cards.html'):
    with open('ai_grid_cards.html', 'r') as f:
        content = f.read()
    
    # Replace old h-48 object-cover with aspect-video container
    def fix_ai_grid_img(match):
        img_tag = match.group(0)
        # Change class to match tutorials.html grid
        img_tag = re.sub(
            r'class="w-full h-48 object-cover"',
            'class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"',
            img_tag
        )
        return f'<div class="aspect-video relative overflow-hidden bg-gray-50 border-b border-gray-100">{img_tag}</div>'
    
    # Find standalone img tags (not already wrapped in aspect-video div)
    if 'aspect-video' not in content:
        content = re.sub(r'<img[^>]+class="w-full h-48 object-cover"[^>]*>', fix_ai_grid_img, content)
        with open('ai_grid_cards.html', 'w') as f:
            f.write(content)
        print("  Fixed: ai_grid_cards.html")
    else:
        print("  Already consistent")

print("\nAll fixes applied.")
