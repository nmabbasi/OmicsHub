import glob

for filepath in glob.glob("pages/*.html"):
    with open(filepath, 'r') as f:
        content = f.read()

    new_content = content.replace('href="services.html"', 'href="../services.html"')

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
