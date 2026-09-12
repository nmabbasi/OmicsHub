import re

with open('old_index.html', 'r', encoding='utf-8') as f:
    old_content = f.read()

# Extract the AI cards
ai_cards = re.findall(r'<article class="tutorial-card.*?data-category="AI-Driven Research & Agentic Bioinformatics".*?</article>', old_content, re.DOTALL)
ai_grid_cards = re.findall(r'<article class="tutorial-grid-card.*?data-category="AI-Driven Research & Agentic Bioinformatics".*?</article>', old_content, re.DOTALL)

ai_cards_html = '\n        '.join(ai_cards)
ai_grid_cards_html = '\n        '.join(ai_grid_cards)

# Fix the dates to have px-2.5 instead of ml-2.5 in both lists
ai_cards_html = ai_cards_html.replace('text-left ml-2.5', 'text-left px-2.5')
ai_grid_cards_html = ai_grid_cards_html.replace('text-left ml-2.5', 'text-left px-2.5')
ai_cards_html = ai_cards_html.replace('text-left ml-1', 'text-left px-2.5')
ai_grid_cards_html = ai_grid_cards_html.replace('text-left ml-1', 'text-left px-2.5')

# Save them to small HTML snippet files so inject_html_cards.py can read them
with open('ai_home_cards.html', 'w', encoding='utf-8') as f:
    f.write('        ' + ai_cards_html)

with open('ai_grid_cards.html', 'w', encoding='utf-8') as f:
    f.write('        ' + ai_grid_cards_html)

# Update inject_html_cards.py
with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_script = f.read()

# Append the AI cards to home_cards_html and grid_cards_html
injection_logic = """
# Appending the manually-added AI tutorials to the dynamic strings
try:
    with open('ai_home_cards.html', 'r', encoding='utf-8') as f:
        home_cards_html += '\\n' + f.read()
    with open('ai_grid_cards.html', 'r', encoding='utf-8') as f:
        grid_cards_html += '\\n' + f.read()
except FileNotFoundError:
    print('Warning: AI tutorial snippets not found.')

with open('index.html', 'r') as f:
"""

inject_script = inject_script.replace("with open('index.html', 'r') as f:", injection_logic)

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(inject_script)

print("Setup completed successfully.")
