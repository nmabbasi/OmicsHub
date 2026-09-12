with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    '<span class="text-sm text-gray-500 whitespace-nowrap flex-shrink-0">{t["date"]}</span>',
    '<span class="text-sm text-gray-500 whitespace-nowrap flex-shrink-0 font-medium text-left px-2.5">{t["date"]}</span>'
)

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(content)
