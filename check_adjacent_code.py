import glob, re

md_files = glob.glob("lessons/*.md")
for f in md_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find all code blocks
    code_blocks = re.finditer(r'```(python|r)\n(.*?)\n```', content, re.DOTALL)
    
    blocks = []
    for match in code_blocks:
        blocks.append((match.group(1), match.start(), match.end()))
    
    for i in range(len(blocks) - 1):
        lang1, start1, end1 = blocks[i]
        lang2, start2, end2 = blocks[i+1]
        
        if lang1 in ['python', 'r'] and lang2 in ['python', 'r'] and lang1 != lang2:
            # Check what is between end1 and start2
            between = content[end1:start2].strip()
            if not between:
                print(f"✅ Adjacent {lang1} and {lang2} found in {f}")
            else:
                print(f"⚠️  Separated {lang1} and {lang2} in {f} (distance: {len(between)} chars). Between text: {repr(between[:50])}")

