import os
import glob
import re
from bs4 import BeautifulSoup

def analyze_tutorials():
    all_html = glob.glob('*.html')
    ignore_list = ['index.html', 'about.html', 'contact.html', 'services.html', 'start-here.html', '404.html', 'success.html']
    tutorial_files = [f for f in all_html if f not in ignore_list]
    results = []
    
    for filepath in tutorial_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            tutorial_content = soup.find(class_='prose')
            if not tutorial_content:
                results.append((filepath, 0, "No prose article found!"))
                continue
                
            text = tutorial_content.get_text(separator=' ')
            words = text.split()
            word_count = len(words)
            results.append((filepath, word_count, "OK"))

    # Sort by word count ascending to find the shortest ones
    results.sort(key=lambda x: x[1])
    
    print("--- 5 SHORTEST TUTORIALS ---")
    for r in results[:5]:
        print(f"{r[0]}: {r[1]} words - {r[2]}")
        
    print("\n--- 5 LONGEST TUTORIALS ---")
    for r in results[-5:]:
        print(f"{r[0]}: {r[1]} words - {r[2]}")

if __name__ == '__main__':
    analyze_tutorials()
