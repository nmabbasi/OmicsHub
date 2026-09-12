import os
import glob
import re

# Directory containing the website source
base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"
images_dir = os.path.join(base_dir, "images")

# All tracked image files in images/ directory
# Let's list all files in images/
all_images = set(os.listdir(images_dir))

# All html, css, js files
source_files = glob.glob(os.path.join(base_dir, "*.html")) + \
               glob.glob(os.path.join(base_dir, "*.css")) + \
               glob.glob(os.path.join(base_dir, "*.js"))

used_images = set()

# Regex to find anything that looks like an image filename (e.g. some-image.webp)
# Also look for images/some-image.webp
for file in source_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all occurrences of image filenames in the content
        for img in all_images:
            if img in content:
                used_images.add(img)

unused_images = all_images - used_images

print("Total images:", len(all_images))
print("Used images:", len(used_images))
print("Unused images:", len(unused_images))

print("\nList of unused images:")
for img in sorted(list(unused_images)):
    print(img)
