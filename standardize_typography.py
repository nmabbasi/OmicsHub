import glob
import re

files = glob.glob('pages/*.html')

for file in files:
    with open(file, 'r') as f:
        content = f.read()

    # Add legal-content class to the wrapper
    content = content.replace('<div class="p-8 md:p-12">', '<div class="p-8 md:p-12 legal-content">')
    
    # Strip hardcoded Tailwind classes from paragraphs
    content = re.sub(r'<p class="[^"]*text-gray-600[^"]*">', '<p>', content)
    content = re.sub(r'<p class="[^"]*text-gray-700[^"]*">', '<p>', content)
    
    # Strip hardcoded Tailwind classes from h2 and h3
    content = re.sub(r'<h2 class="[^"]*text-xl[^"]*">', '<h2>', content)
    content = re.sub(r'<h2 class="[^"]*font-bold[^"]*">', '<h2>', content)
    content = re.sub(r'<h3 class="[^"]*font-bold[^"]*">', '<h3>', content)
    
    # Strip from ul and li
    content = re.sub(r'<ul class="[^"]*list-disc[^"]*">', '<ul>', content)
    content = re.sub(r'<li class="[^"]*text-gray-600[^"]*">', '<li>', content)

    with open(file, 'w') as f:
        f.write(content)
        
print("Legal pages typography standardized to use .legal-content")
