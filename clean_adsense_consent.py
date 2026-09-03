import glob
import re

html_files = glob.glob('*.html') + glob.glob('pages/*.html')

for filepath in html_files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove the adsense-consent script tag
    content = re.sub(r'<script src="adsense-consent\.js"\s*>\s*</script>\n?', '', content)
    content = re.sub(r'<script src="\.\./adsense-consent\.js"\s*>\s*</script>\n?', '', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Cleaned adsense-consent from {filepath}")
    else:
        print(f"No changes in {filepath}")
