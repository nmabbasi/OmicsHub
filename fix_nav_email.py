import os
import glob

html_files = glob.glob('**/*.html', recursive=True)

for file in html_files:
    if 'node_modules' in file:
        continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the nav link
    new_content = content.replace('href="index.html#all-tutorials"', 'href="tutorials.html"')
    
    # Special case for contact email
    if file == 'contact.html':
        new_content = new_content.replace('nmabbasi@gmail.com', 'contact@theomicshub.com')
        new_content = new_content.replace('nmabbasi12020@gmail.com', 'contact@theomicshub.com')

    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")

print("Done")
