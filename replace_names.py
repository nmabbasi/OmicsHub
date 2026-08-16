import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

replacements = [
    ("OmicsHub Team", "OmicsHub Team"),
    ("OmicsHub", "OmicsHub"),
    ("nmabbasi.github.io/OmicsHub", "nmabbasi.github.io/OmicsHub"),
    ("OmicsHub", "OmicsHub"),
    ("omicshub-logo.png", "omicshub-logo.png"),
    ("OmicsHub", "OmicsHub"),
    ("omicshub", "omicshub")
]

for root, _, files in os.walk('.'):
    if '.git' in root:
        continue
    for file in files:
        if file.endswith(('.html', '.md', '.js', '.css', '.py', '.txt')):
            replace_in_file(os.path.join(root, file), replacements)

# Also check if image needs renaming
if os.path.exists('images/omicshub-logo.png'):
    os.rename('images/omicshub-logo.png', 'images/omicshub-logo.png')
    print("Renamed images/omicshub-logo.png to images/omicshub-logo.png")
