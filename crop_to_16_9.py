import os
from PIL import Image

# Map of source artifact images to target names in OmicsHub/images/
images_to_crop = {
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/bioinformatics_intro_1786692083810.png': 'bioinformatics-intro.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/command_line_terminal_1786692101935.png': 'command-line-terminal.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/conda_environment_1786692124366.png': 'conda-environment.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/mamba_micromamba_1786692138423.png': 'mamba-micromamba.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/scrna_heterogeneity_1786692202814.png': 'scrna_heterogeneity.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/scrna_metabolism_1786692216892.png': 'scrna_metabolism.png',
    '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/hpc_slurm_1786692270172.png': 'hpc.png'
}

target_dir = '/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/images'
os.makedirs(target_dir, exist_ok=True)

# 16:9 ratio calculations
# 1024 / 16 * 9 = 576. So the target size is 1024x576.
TARGET_WIDTH = 1024
TARGET_HEIGHT = 576

for src_path, target_filename in images_to_crop.items():
    if not os.path.exists(src_path):
        print(f"File not found: {src_path}")
        continue
        
    try:
        img = Image.open(src_path)
        width, height = img.size
        
        # Calculate cropping box
        left = 0
        top = (height - TARGET_HEIGHT) / 2
        right = width
        bottom = (height + TARGET_HEIGHT) / 2
        
        # Crop to 16:9 center
        img_cropped = img.crop((left, top, right, bottom))
        
        # Save to target location
        out_path = os.path.join(target_dir, target_filename)
        img_cropped.save(out_path)
        print(f"Successfully cropped and saved {target_filename}")
        
    except Exception as e:
        print(f"Error processing {src_path}: {e}")

# Copy hpc.png to sc.png (they use the same banner theme)
import shutil
shutil.copy2(os.path.join(target_dir, 'hpc.png'), os.path.join(target_dir, 'sc.png'))
print("Copied hpc.png to sc.png")
