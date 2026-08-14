from PIL import Image, ImageDraw, ImageFont

width, height = 1920, 1080
img = Image.new('RGB', (width, height), color=(248, 250, 252))
draw = ImageDraw.Draw(img)

try:
    font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 36) # Much smaller font for realism
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 40)
except IOError:
    font_medium = ImageFont.load_default()
    font_large = ImageFont.load_default()

# Centered large terminal box
box_w, box_h = 1400, 700
box_x, box_y = (width - box_w) // 2, (height - box_h) // 2

# Terminal Background
draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)], radius=20, fill=(30, 41, 59))
# Terminal top bar
draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + 50)], radius=20, fill=(51, 65, 85))
draw.rectangle([(box_x, box_y + 25), (box_x + box_w, box_y + 50)], fill=(51, 65, 85))

# Terminal buttons (macOS style)
draw.ellipse([(box_x + 25, box_y + 15), (box_x + 45, box_y + 35)], fill=(239, 68, 68))
draw.ellipse([(box_x + 55, box_y + 15), (box_x + 75, box_y + 35)], fill=(234, 179, 8))
draw.ellipse([(box_x + 85, box_y + 15), (box_x + 105, box_y + 35)], fill=(34, 197, 94))

# Terminal text
terminal_text = """(base) user@omics-hub:~$ conda create -n sc_env python=3.10 scanpy seurat
Collecting package metadata (current_repodata.json): done
Solving environment: done

## Package Plan ##

  environment location: /opt/miniconda3/envs/sc_env

  added / updated specs:
    - python=3.10
    - scanpy
    - seurat

Proceed ([y]/n)? y

Preparing transaction: done
Verifying transaction: done
Executing transaction: done
#
# To activate this environment, use
#
#     $ conda activate sc_env
#
"""

draw.text((box_x + 50, box_y + 80), terminal_text, fill=(74, 222, 128), font=font_medium)

img.save('images/conda-environment.png')
print("Conda banner updated to single large terminal.")
