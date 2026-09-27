import os
import re
import glob

# 1. Update the grid cards in HTML files
html_files = ['index.html', 'tutorials.html', 'ai_home_cards.html', 'ai_grid_cards.html']
for file_path in html_files:
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
        
        # We look for aspect-video containers and their images.
        # In tutorials.html we injected:
        # <div class="aspect-video relative overflow-hidden bg-gray-50 border-b border-gray-100"><img ... class="... object-cover ..."></div>
        # Let's just blindly replace 'object-cover' with 'object-contain object-center scale-95' in the grid images to give them a little breathing room.
        # But wait, scale-95 might break hover scale. Let's stick to object-contain object-center.
        # We need to make sure we don't hit the author portrait (which uses object-cover rounded-full).
        
        # Find all <img> tags inside aspect-video divs that have object-cover
        def replace_cover_in_card(match):
            img_tag = match.group(0)
            if 'rounded-full' not in img_tag:
                return img_tag.replace('object-cover', 'object-contain object-center')
            return img_tag
            
        new_content = re.sub(r'<img[^>]+class="[^"]*object-cover[^"]*"[^>]*>', replace_cover_in_card, content)
        
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Updated {file_path}")

# 2. Update all tutorials/*.html hero images
tutorial_files = glob.glob('tutorials/*.html')
for file_path in tutorial_files:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # The hero image is usually:
    # <div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100 aspect-video relative">
    # <img src="../images/..." alt="..." class="w-full h-full object-cover" loading="eager" decoding="async">
    # Let's add a nice background to the div and change object-cover to object-contain.
    
    def replace_hero_div(match):
        div_opening = match.group(1)
        if 'bg-' not in div_opening:
            div_opening = div_opening.replace('class="', 'class="bg-gray-50 ')
        return div_opening
        
    content = re.sub(r'(<div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100 aspect-video relative"[^>]*>)', replace_hero_div, content)
    
    # Now replace object-cover on the hero image (it's eager loaded or just the first image after the title)
    def replace_hero_img(match):
        img_tag = match.group(0)
        return img_tag.replace('object-cover', 'object-contain object-center')
        
    # Find images that are w-full h-full object-cover
    content = re.sub(r'<img[^>]+class="w-full h-full object-cover"[^>]*>', replace_hero_img, content)
    
    with open(file_path, 'w') as f:
        f.write(content)

print("Updated all tutorial pages.")
