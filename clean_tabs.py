import os
import re

files = [
    "lessons/scrna-seq-basics.md",
    "lessons/scrna-seq-trajectory-inference.md",
    "lessons/scrna-seq-downstream-analysis.md"
]

for f in files:
    with open(f, 'r') as file:
        content = file.read()

    # Remove HTML tags associated with tabs
    content = re.sub(r'<div class="code-tab-container"[^>]*>', '', content)
    content = re.sub(r'<div class="code-tab-header">', '', content)
    content = re.sub(r'<button class="code-tab-btn"[^>]*>.*?</button>', '', content)
    content = re.sub(r'<div class="code-tab-content"[^>]*>', '', content)
    content = re.sub(r'</div>', '', content)

    # Remove excess blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    with open(f, 'w') as file:
        file.write(content)

