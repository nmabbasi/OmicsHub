import glob
import re

for filepath in glob.glob('*.py'):
    with open(filepath, 'r') as f:
        content = f.read()

    new_content = re.sub(
        r'<script src="https://cdn\.tailwindcss\.com\?plugins=typography"></script>',
        r'<link href="tailwind.min.css" rel="stylesheet">',
        content
    )

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
