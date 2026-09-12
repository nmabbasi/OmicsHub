import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace category span to ensure text-left
pattern = r'(<span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full truncate max-w-full inline-block)(">)([^<]+)</span>'
# Add text-left
replacement = r'\1 text-left"\2\3</span>'
new_content, count1 = re.subn(pattern, replacement, content)

# Replace date span
# Some are <span class="text-sm text-gray-500 font-medium">2026-08-15</span>
# Some are <span class="text-sm text-gray-500 whitespace-nowrap flex-shrink-0 font-medium">2026-09-08</span>
# Some are <span class="text-sm text-gray-500">2026-08-15</span>
# We can just inject "text-left pl-1" into all of them that are immediately inside the flex col
# Actually, let's just do a blanket replace for the date span under that div
date_pattern = r'(<div class="flex flex-col items-start gap-1 mb-3">\s*<span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full truncate max-w-full inline-block text-left">[^<]+</span>\s*<span class="text-sm text-gray-500)([^"]*)(")'
# wait, date class ends with quote.
date_replacement = r'\1\2 text-left ml-1\3'
new_content, count2 = re.subn(date_pattern, date_replacement, new_content)

print(f"Index.html: Replaced category spans: {count1}, Replaced date spans: {count2}")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

# Update inject_html_cards.py
with open('inject_html_cards.py', 'r', encoding='utf-8') as f:
    inject_content = f.read()

inject_pattern = r'(<span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full truncate max-w-full inline-block)(">\{t\["category"\]\}</span>)'
inject_replacement = r'\1 text-left\2'
new_inject_content, count_inject1 = re.subn(inject_pattern, inject_replacement, inject_content)

date_inject_pattern = r'(<span class="text-sm text-gray-500 whitespace-nowrap flex-shrink-0 font-medium)(">\{t\["date"\]\}</span>)'
date_inject_replacement = r'\1 text-left ml-1\2'
new_inject_content, count_inject2 = re.subn(date_inject_pattern, date_inject_replacement, new_inject_content)

print(f"Inject: Replaced category spans: {count_inject1}, Replaced date spans: {count_inject2}")

with open('inject_html_cards.py', 'w', encoding='utf-8') as f:
    f.write(new_inject_content)

