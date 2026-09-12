import os
import glob
import re

base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"
html_files = glob.glob(os.path.join(base_dir, "*.html"))
images_dir = os.path.join(base_dir, "images")
images = set(os.listdir(images_dir))

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    def replacer(match):
        img_name = match.group(1)
        ext = match.group(2)
        webp_name = img_name + ".webp"
        if webp_name in images:
            return "images/" + webp_name
        return match.group(0)

    new_content = re.sub(r'images/([^"\'\>\?]+)\.(png|jpg|jpeg)', replacer, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated extensions in {os.path.basename(filepath)}")
