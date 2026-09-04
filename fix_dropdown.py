import glob

def fix_legal_dropdown():
    html_files = glob.glob('**/*.html', recursive=True)
    target_string = "group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible"
    
    count = 0
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if target_string in content:
            new_content = content.replace(target_string, "")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            
    print(f"Fixed dropdown in {count} HTML files.")

if __name__ == '__main__':
    fix_legal_dropdown()
