import os
from PIL import Image

src_path = '/home/nmabbasi/.gemini/antigravity/brain/a3ad854c-703c-499a-bee6-bc081079c57a/hero_workflow_sketch_cohesive_1786695787298.png'
target_dir = '/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/images'
target_filename = 'hero-bg.png'
os.makedirs(target_dir, exist_ok=True)

# 21:9 ratio calculations
# 1024 / 21 * 9 = 438. So target size is 1024x438.
# Actually, the user wants to see the top and bottom text maybe? Let's crop to 16:9 (1024x576) instead to preserve more of the beautiful infographic.
TARGET_WIDTH = 1024
TARGET_HEIGHT = 576

try:
    img = Image.open(src_path)
    width, height = img.size
    
    # Calculate cropping box
    left = 0
    top = (height - TARGET_HEIGHT) / 2
    right = width
    bottom = (height + TARGET_HEIGHT) / 2
    
    # Crop to center
    img_cropped = img.crop((left, top, right, bottom))
    
    # Save to target location
    out_path = os.path.join(target_dir, target_filename)
    img_cropped.save(out_path)
    print(f"Successfully cropped and saved {target_filename}")
    
except Exception as e:
    print(f"Error processing {src_path}: {e}")
