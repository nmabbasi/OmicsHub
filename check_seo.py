import glob

all_html = glob.glob('**/*.html', recursive=True)
errors = []

for file in all_html:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '<title>' not in content or '</title>' not in content:
        errors.append(f"Missing title tag in {file}")
    if 'name="description"' not in content:
        errors.append(f"Missing meta description in {file}")

if errors:
    for e in errors: print(e)
else:
    print("All SEO tags are present!")
