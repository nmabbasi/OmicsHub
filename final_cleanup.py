import os
import glob
import subprocess

base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"
images_dir = os.path.join(base_dir, "images")

all_images = set(os.listdir(images_dir))
source_files = glob.glob(os.path.join(base_dir, "*.*"))

used_images = set()

for file in source_files:
    if os.path.isfile(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            for img in all_images:
                if img in content:
                    used_images.add(img)
        except Exception:
            pass

unused_images = all_images - used_images

print(f"Found {len(unused_images)} TRULY unused images.")

for img in unused_images:
    subprocess.run(["git", "rm", "-f", f"images/{img}"], cwd=base_dir, stdout=subprocess.DEVNULL)

