import os
import glob
from bs4 import BeautifulSoup

html_files = glob.glob('*.html') + glob.glob('pages/*.html')

adsense_code = """
  <!-- Google AdSense Publisher Code -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
"""

for filepath in html_files:
    with open(filepath, 'r') as f:
        content = f.read()
        
    if 'pagead2.googlesyndication.com' not in content:
        # Insert before </head>
        content = content.replace('</head>', adsense_code + '</head>')
        
        with open(filepath, 'w') as f:
            f.write(content)
            
print("AdSense scripts added to all HTML files.")
