import os
import glob
import shutil

base_dir = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"
html_files = glob.glob(os.path.join(base_dir, "*.html"))
desktop_dir = "/home/nmabbasi/Desktop/OmicsHub_Unused_Images"
images_dir = os.path.join(base_dir, "images")

images = set(os.listdir(desktop_dir))
used = set()

for f in html_files:
    with open(f, "r", encoding="utf-8") as fh:
        content = fh.read()
    for img in images:
        if img in content:
            used.add(img)

print(f"Restoring {len(used)} incorrectly deleted images...")

for img in used:
    src = os.path.join(desktop_dir, img)
    dst = os.path.join(images_dir, img)
    shutil.copy2(src, dst)
    print(f"Restored: {img}")
