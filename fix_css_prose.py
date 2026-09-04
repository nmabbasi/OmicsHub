import re

with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Replace all `.tutorial-content` with `.prose`
css = css.replace('.tutorial-content', '.prose')

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Replaced .tutorial-content with .prose in style.css")
