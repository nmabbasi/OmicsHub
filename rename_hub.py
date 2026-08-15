import os
import glob

# Walk through the directory and replace text in all relevant files
search_text = "The Omics Hub"
replace_text = "The Omics Hub"

# Define the file extensions to process
extensions = ['*.html', '*.py', '*.js', '*.md', '*.txt']

files_to_process = []
for ext in extensions:
    files_to_process.extend(glob.glob(f"**/{ext}", recursive=True))

count = 0
for filepath in files_to_process:
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if search_text in content:
            new_content = content.replace(search_text, replace_text)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            count += 1
            print(f"Updated: {filepath}")

# Also replace the lowercase version just in case
search_text_lower = "the omics hub"
replace_text_lower = "the omics hub"

for filepath in files_to_process:
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if search_text_lower in content:
            new_content = content.replace(search_text_lower, replace_text_lower)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated lowercase: {filepath}")

print(f"Total files updated: {count}")
