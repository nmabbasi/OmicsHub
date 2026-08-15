import os
import re

lessons_dir = "lessons"
for filename in os.listdir(lessons_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(lessons_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        # Replace author in frontmatter
        new_content = re.sub(
            r'^author:\s*".*?"',
            'author: "Nasir Mahmood Abbasi, PhD"',
            content,
            flags=re.MULTILINE
        )
        new_content = re.sub(
            r'^author:\s*OmicsHub Team',
            'author: "Nasir Mahmood Abbasi, PhD"',
            new_content,
            flags=re.MULTILINE
        )
        
        if new_content != content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated {filename}")
