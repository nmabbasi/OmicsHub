import glob
import re

root_htmls = glob.glob("*.html")
pattern = re.compile(r"onclick=\"window\.location\.href='([^/]+?\.html)'\"")

for f in root_htmls:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    # We only want to prepend 'tutorials/' if it's one of the 58 tutorials.
    # What are the 58 tutorials?
    import os
    valid_tutorials = [os.path.basename(t) for t in glob.glob("tutorials/*.html")]
    
    modified = False
    
    def replacer(match):
        filename = match.group(1)
        if filename in valid_tutorials:
            return f"onclick=\"window.location.href='tutorials/{filename}'\""
        return match.group(0)

    new_content = pattern.sub(replacer, content)
    
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Fixed onclicks in {f}")

print("Done fixing onclicks.")
