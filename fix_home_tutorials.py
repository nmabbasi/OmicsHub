import re

with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find the 10 AI tutorials from all-tutorials-list
ai_pattern = re.compile(r'<article class="tutorial-grid-card[^>]*data-category="AI-Driven Research & Agentic Bioinformatics"[^>]*>.*?</article>', re.DOTALL)
ai_tutorials = ai_pattern.findall(content)

converted_tutorials = []
for tut in ai_tutorials:
    tut = tut.replace('tutorial-grid-card bg-white rounded-lg shadow-md overflow-hidden transform transition-transform hover:scale-105 duration-300 cursor-pointer flex flex-col', 'tutorial-card cursor-pointer')
    
    def replace_img(match):
        img_src = match.group(1)
        alt_text = match.group(2)
        onerror_match = re.search(r'onerror="([^"]*)"', match.group(0))
        onerror_str = f' onerror="{onerror_match.group(1)}"' if onerror_match else ""
        return f'<div class="w-full aspect-video relative overflow-hidden border-b border-gray-100 bg-gray-50"><img src="{img_src}" alt="{alt_text}" loading="lazy" decoding="async" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 hover:scale-105"{onerror_str}></div>'

    tut = re.sub(r'<img src="([^"]+)" alt="([^"]+)"[^>]*>', replace_img, tut)
    tut = re.sub(r'whitespace-nowrap flex-shrink-0', 'font-medium', tut)
    tut = re.sub(r'<p class="text-gray-700 text-base mb-4 line-clamp-3">', '<p class="excerpt text-gray-600 mb-4">', tut)
    tut = re.sub(r'mt-auto block">', '">', tut)
    converted_tutorials.append(tut)

# Find where tutorials-list ends. The last article in tutorials-list is long-read-pacbio-nanopore.
# Let's find that article and insert right after its </article>
insert_marker = r'onclick="window.location.href=\'long-read-pacbio-nanopore.html\'">.*?Read More →</a>\s*</div>\s*</article>'

match = re.search(insert_marker, content, re.DOTALL)
if match:
    insert_pos = match.end()
    new_tutorials_str = "\n        " + "\n        ".join(converted_tutorials)
    new_content = content[:insert_pos] + new_tutorials_str + content[insert_pos:]
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Added {len(converted_tutorials)} AI tutorials to tutorials-list.")
else:
    print("Could not find insertion point!")
