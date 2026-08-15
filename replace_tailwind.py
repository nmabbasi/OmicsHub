import os
import glob

def replace_in_files(file_pattern, rel_path):
    for filepath in glob.glob(file_pattern, recursive=True):
        if not os.path.isfile(filepath): continue
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace the Tailwind CDN tag with the minified CSS link
        import re
        new_content = re.sub(
            r'<script src="https://cdn\.tailwindcss\.com\?plugins=typography"></script>',
            f'<link href="{rel_path}tailwind.min.css" rel="stylesheet">',
            content
        )
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

replace_in_files('*.html', '')
replace_in_files('pages/*.html', '../')
