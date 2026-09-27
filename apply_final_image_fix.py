import os
import re
import glob

# 1. Update the grid cards in HTML files back to object-cover
html_files = ['index.html', 'tutorials.html', 'ai_home_cards.html', 'ai_grid_cards.html']
for file_path in html_files:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace object-contain object-center with object-cover in grid cards
        # We previously added: object-contain object-center
        content = content.replace('object-contain object-center', 'object-cover')
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated {file_path}")

# 2. Update all tutorials/*.html hero images to remove aspect-video and use h-auto
tutorial_files = glob.glob('tutorials/*.html')
for file_path in tutorial_files:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # We want to find the hero image div. It currently looks like:
    # <div class="bg-gray-50 mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100 aspect-video relative">
    # OR
    # <div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100 aspect-video relative">
    # We need to remove "aspect-video relative" and "bg-gray-50".
    
    def clean_hero_div(match):
        div_opening = match.group(0)
        div_opening = div_opening.replace(' aspect-video', '')
        div_opening = div_opening.replace(' relative', '')
        div_opening = div_opening.replace('bg-gray-50 ', '')
        return div_opening
        
    content = re.sub(r'<div class="[^"]*mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100[^"]*">', clean_hero_div, content)
    
    # Now replace the img tag inside the hero to be w-full h-auto instead of w-full h-full object-contain object-center
    def clean_hero_img(match):
        img_tag = match.group(0)
        img_tag = img_tag.replace('h-full', 'h-auto')
        img_tag = img_tag.replace('object-cover', '')
        img_tag = img_tag.replace('object-contain', '')
        img_tag = img_tag.replace('object-center', '')
        # remove double spaces
        img_tag = re.sub(r'\s+', ' ', img_tag)
        return img_tag
        
    content = re.sub(r'<img[^>]+loading="eager"[^>]*>', clean_hero_img, content)
    
    with open(file_path, 'w') as f:
        f.write(content)

print("Updated all tutorial pages.")
