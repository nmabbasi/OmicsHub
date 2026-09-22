import glob

files = glob.glob("tutorials/*.html")
fixed_count = 0

for f in files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = content.replace("<imgalt=", "<img alt=")
    new_content = new_content.replace("\"/ class=", "\" class=")
    
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        fixed_count += 1
        print(f"Fixed {f}")

print(f"Total files fixed: {fixed_count}")
