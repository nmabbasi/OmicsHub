import os
import glob
import re

html_files = glob.glob('*.html') + glob.glob('pages/*.html')

for filepath in html_files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove the script tags
    content = re.sub(r'<script src="cookie-consent\.js"\s*>\s*</script>\n?', '', content)
    content = re.sub(r'<script src="\.\./cookie-consent\.js"\s*>\s*</script>\n?', '', content)
    
    # Remove the banner HTML
    # We can use regex to match the banner and the panel since they are well-defined
    # Or simpler: remove everything from <div id="cookie-consent-banner" to the end of the panel div
    # Let's use a robust regex
    pattern = r'<div id="cookie-consent-banner"[\s\S]*?<div id="cookie-preferences-panel"[\s\S]*?</div>\s*</div>'
    content = re.sub(pattern, '', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Cleaned {filepath}")
    else:
        print(f"No changes in {filepath}")
