import glob
from bs4 import BeautifulSoup
import re

def find_em_dashes(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Find text nodes containing em dashes or common patterns
    found = []
    
    # Check for actual em-dash
    if '—' in content:
        found.append("Contains literal '—'")
    
    # Check for en-dash
    if '–' in content:
        found.append("Contains literal '–'")
        
    if '&mdash;' in content:
        found.append("Contains '&mdash;'")

    if '&#8212;' in content:
        found.append("Contains '&#8212;'")
        
    return found

if __name__ == '__main__':
    html_files = glob.glob('**/*.html', recursive=True)
    total_found = 0
    for file in html_files:
        matches = find_em_dashes(file)
        if matches:
            print(f'{file}: {", ".join(matches)}')
            total_found += 1
            
    print(f'Total files with dashes: {total_found}')
