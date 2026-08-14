from PIL import Image

def pad_to_16_9(filename):
    try:
        img = Image.open(filename)
        # Target aspect ratio 16:9
        target_ratio = 16.0 / 9.0
        w, h = img.size
        
        # We assume the image is square or less wide than 16:9
        # So we pad the width.
        new_h = h
        new_w = int(h * target_ratio)
        
        if w >= new_w:
            print(f"{filename} is already wide enough.")
            return

        new_img = Image.new("RGB", (new_w, new_h), color=(255, 255, 255))
        
        # Paste centered
        offset = ((new_w - w) // 2, 0)
        new_img.paste(img, offset)
        
        new_img.save(filename)
        print(f"Padded {filename} to 16:9")
    except Exception as e:
        print(f"Error padding {filename}: {e}")

pad_to_16_9('images/scrna_heterogeneity.png')
pad_to_16_9('images/scrna_metabolism.png')
pad_to_16_9('images/bioinformatics-intro.png')
