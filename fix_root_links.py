import os
import glob

# Get all tutorial filenames
tutorials = [os.path.basename(f) for f in glob.glob("tutorials/*.html")]

# Root HTML files
root_htmls = glob.glob("*.html")

for f in root_htmls:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    modified = False
    for tut in tutorials:
        old_link = f'href="{tut}"'
        new_link = f'href="tutorials/{tut}"'
        if old_link in content:
            content = content.replace(old_link, new_link)
            modified = True
            
        old_link_hash = f'href="{tut}#'
        new_link_hash = f'href="tutorials/{tut}#'
        if old_link_hash in content:
            content = content.replace(old_link_hash, new_link_hash)
            modified = True

    if modified:
        with open(f, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Fixed links in {f}")

print("Done fixing root links.")
