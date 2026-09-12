import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the flex container
# Pattern: <div class="flex items-start justify-between gap-2 mb-3">
#         <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
pattern = r'<div class="flex items-start justify-between gap-2 mb-3">\s*<span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">'
replacement = r'<div class="flex flex-col items-start gap-1 mb-3">\n                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full truncate max-w-full inline-block">'
new_content, count = re.subn(pattern, replacement, content)

print(f"Replaced {count} occurrences in index.html")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

# Update inject_html_cards.py
with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_content = f.read()

inject_pattern = r'<div class="flex items-center justify-between mb-3">\s*<span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">\{t\["category"\]\}</span>\s*<span class="text-sm text-gray-500">\{t\["date"\]\}</span>'
inject_replacement = r'<div class="flex flex-col items-start gap-1 mb-3">\n                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full truncate max-w-full inline-block">{t["category"]}</span>\n                    <span class="text-sm text-gray-500 whitespace-nowrap flex-shrink-0">{t["date"]}</span>'

new_inject_content, count_inject = re.subn(inject_pattern, inject_replacement, inject_content)
print(f"Replaced {count_inject} occurrences in inject_html_cards.py")

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(new_inject_content)

