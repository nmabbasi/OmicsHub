import glob
from bs4 import BeautifulSoup
import re

def clean_spaced_hyphens(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    
    # We want to find text nodes in elements that typically contain prose
    # avoiding pre, code, script, style, etc.
    prose_tags = ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'strong', 'em', 'a', 'td', 'th', 'div']
    
    changed = False
    
    for tag in soup.find_all(prose_tags):
        # We don't want to process tags that are children of pre, code, or script
        parent = tag.parent
        skip = False
        while parent:
            if parent.name in ['pre', 'code', 'script', 'style', 'svg']:
                skip = True
                break
            parent = parent.parent
            
        if skip:
            continue
            
        # process direct text nodes of this tag
        for text_node in tag.find_all(string=True, recursive=False):
            if ' - ' in text_node:
                # Replace ' - ' with ', '
                new_text = text_node.replace(' - ', ', ')
                text_node.replace_with(new_text)
                changed = True
                
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        return True
    return False

if __name__ == '__main__':
    html_files = glob.glob('**/*.html', recursive=True)
    updated_files = 0
    for file in html_files:
        if clean_spaced_hyphens(file):
            print(f'Updated {file}')
            updated_files += 1
            
    print(f'Total files updated for spaced hyphens: {updated_files}')
