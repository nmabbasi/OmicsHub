with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_content = content.replace('text-left ml-1', 'text-left ml-2.5')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_content = f.read()

new_inject_content = inject_content.replace('text-left ml-1', 'text-left ml-2.5')

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(new_inject_content)

print("Updated ml-1 to ml-2.5")
