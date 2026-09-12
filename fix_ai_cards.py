import re

with open('old_index.html', 'r', encoding='utf-8') as f:
    old_content = f.read()

# Extract the AI cards
ai_cards = re.findall(r'<article class="tutorial-card.*?data-category="AI-Driven Research & Agentic Bioinformatics".*?</article>', old_content, re.DOTALL)
ai_grid_cards = re.findall(r'<article class="tutorial-grid-card.*?data-category="AI-Driven Research & Agentic Bioinformatics".*?</article>', old_content, re.DOTALL)

ai_cards_html = '\n        '.join(ai_cards)
ai_grid_cards_html = '\n        '.join(ai_grid_cards)

# Fix the dates to have px-2.5 instead of ml-2.5 in both lists just in case
ai_cards_html = ai_cards_html.replace('text-left ml-2.5', 'text-left px-2.5')
ai_grid_cards_html = ai_grid_cards_html.replace('text-left ml-2.5', 'text-left px-2.5')

# 1. Update index.html directly
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Inject into home grid
content = re.sub(
    r'(<!-- INJECT_TUTORIALS -->.*?)(<!-- INJECT_TUTORIALS_END -->)',
    r'\g<1>\n        ' + ai_cards_html + r'\n        \g<2>',
    content,
    flags=re.DOTALL
)

# Inject into all tutorials grid
content = re.sub(
    r'(<!-- INJECT_ALL_TUTORIALS -->.*?)(<!-- INJECT_ALL_TUTORIALS_END -->)',
    r'\g<1>\n        ' + ai_grid_cards_html + r'\n        \g<2>',
    content,
    flags=re.DOTALL
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Update inject_html_cards.py so future runs don't wipe them out
with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_script = f.read()

# We need to append the AI cards logic to the generated html in the script
# Find where new_content is created and replace it
# "html_parts.append('        <!-- INJECT_TUTORIALS_END -->')"
inject_script = inject_script.replace(
    "html_parts.append('        <!-- INJECT_TUTORIALS_END -->')",
    "html_parts.append('        ' + '''" + ai_cards_html.replace('\\', '\\\\') + "''')\n        html_parts.append('        <!-- INJECT_TUTORIALS_END -->')"
)

inject_script = inject_script.replace(
    "all_tutorials_parts.append('        <!-- INJECT_ALL_TUTORIALS_END -->')",
    "all_tutorials_parts.append('        ' + '''" + ai_grid_cards_html.replace('\\', '\\\\') + "''')\n        all_tutorials_parts.append('        <!-- INJECT_ALL_TUTORIALS_END -->')"
)

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(inject_script)

print("AI tutorials injected into index.html and inject_html_cards.py successfully!")
