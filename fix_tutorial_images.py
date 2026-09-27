import re

with open("tutorials.html", "r") as f:
    content = f.read()

def replace_img(match):
    article_tag = match.group(1)
    img_tag = match.group(2)
    
    # Remove the old class attribute completely from the img tag
    img_tag_cleaned = re.sub(r'\s*class="[^"]+"', '', img_tag)
    
    if img_tag_cleaned.endswith("/>"):
        new_img = img_tag_cleaned[:-2] + ' class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700">'
    else:
        new_img = img_tag_cleaned[:-1] + ' class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700">'
    
    return f'{article_tag}<div class="aspect-video relative overflow-hidden bg-gray-50 border-b border-gray-100">{new_img}</div>'

new_content = re.sub(r'(<article class="tutorial-grid-card[^>]*>\s*)(<img[^>]+>)', replace_img, content)

with open("tutorials.html", "w") as f:
    f.write(new_content)

print("Updated tutorials.html")
