import glob
import re
import os

fixes = 0
tutorial_files = sorted(glob.glob('tutorials/*.html'))

for tf in tutorial_files:
    with open(tf, 'r') as f:
        content = f.read()
    original = content
    
    # We want to change the hero image class from 'w-full h-auto' to 'w-full aspect-video object-cover'
    # This will ensure ALL hero images have the exact same 16:9 proportions on the page, preventing 
    # 1:1 images from taking up massive vertical space and looking "zoomed".
    
    def fix_hero(match):
        img_tag = match.group(0)
        img_tag = re.sub(r'class="[^"]*"', 'class="w-full aspect-video object-cover"', img_tag)
        return img_tag

    # Replace the img tag class inside the hero container
    # Hero images have loading="eager"
    content = re.sub(r'<img[^>]+loading="eager"[^>]*>', fix_hero, content)
    
    if content != original:
        with open(tf, 'w') as f:
            f.write(content)
        fixes += 1

print(f"Updated {fixes} tutorial hero images to use consistent aspect-video object-cover.")
