import os
import glob
import shutil
import subprocess

base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"
images_dir = os.path.join(base_dir, "images")
desktop_dir = "/home/nmabbasi/Desktop/OmicsHub_Unused_Images"

if not os.path.exists(desktop_dir):
    os.makedirs(desktop_dir)

all_images = set(os.listdir(images_dir))
source_files = glob.glob(os.path.join(base_dir, "*.html")) + \
               glob.glob(os.path.join(base_dir, "*.css")) + \
               glob.glob(os.path.join(base_dir, "*.js"))

used_images = set()

for file in source_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        for img in all_images:
            if img in content:
                used_images.add(img)

unused_images = all_images - used_images

# Special exclusions just in case
exclusions = {"hero-image-light-navy-clean.webp"}
unused_images = unused_images - exclusions

print(f"Found {len(unused_images)} unused images to move.")

moved_count = 0
for img in unused_images:
    src = os.path.join(images_dir, img)
    dst = os.path.join(desktop_dir, img)
    
    # Copy to desktop
    shutil.copy2(src, dst)
    
    # Git rm
    subprocess.run(["git", "rm", "-f", f"images/{img}"], cwd=base_dir, stdout=subprocess.DEVNULL)
    moved_count += 1

print(f"Successfully moved {moved_count} unused images to {desktop_dir} and removed them from git.")
