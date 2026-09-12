import re
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Match <span class="text-sm text-gray-500..." ...>2026-08-15</span>
pattern = r'(<span class="text-sm text-gray-500)([^"]*)(">)(202[0-9]-[0-9]{2}-[0-9]{2}</span>)'
# Make sure we don't add ml-1 twice
def repl(m):
    classes = m.group(2)
    if 'text-left' not in classes:
        classes += ' text-left ml-1'
    return m.group(1) + classes + m.group(3) + m.group(4)

new_content, count = re.subn(pattern, repl, content)
print(f"Index.html: Replaced date spans: {count}")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_content)
