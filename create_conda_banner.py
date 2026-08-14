from PIL import Image, ImageDraw, ImageFont
import os

# Create a 1920x820 image (approx 21:9 ratio)
width, height = 1920, 820
img = Image.new('RGB', (width, height), color=(240, 244, 248))
draw = ImageDraw.Draw(img)

# Try to load a nice font, fallback to default
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 140)
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 60)
except IOError:
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()

# Draw a dark terminal-like box in the center right
box_x, box_y = 700, 200
box_w, box_h = 1000, 450
draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=20, fill=(30, 41, 59))
# Terminal top bar
draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + 40)], radius=20, fill=(51, 65, 85))
draw.rectangle([(box_x, box_y + 20), (box_x + box_w, box_y + 40)], fill=(51, 65, 85))
# Terminal buttons
draw.ellipse([(box_x + 20, box_y + 12), (box_x + 36, box_y + 28)], fill=(239, 68, 68))
draw.ellipse([(box_x + 46, box_y + 12), (box_x + 62, box_y + 28)], fill=(234, 179, 8))
draw.ellipse([(box_x + 72, box_y + 12), (box_x + 88, box_y + 28)], fill=(34, 197, 94))

# Terminal text
terminal_text = """$ conda create -n sc_env python=3.10
Collecting package metadata (current_repodata.json): done
Solving environment: done
==> WARNING: A newer version of conda exists. <==

## Package Plan ##
  environment location: /opt/miniconda3/envs/sc_env

Proceed ([y]/n)? y
"""
draw.text((box_x + 40, box_y + 70), terminal_text, fill=(74, 222, 128), font=font_medium)

# Draw the word CONDA on the left in large green text
draw.text((150, 320), "conda", fill=(34, 197, 94), font=font_large)

img.save('images/conda-environment.png')
print("Conda banner generated successfully.")
