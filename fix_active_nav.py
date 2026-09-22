import glob
import re
import os

html_files = glob.glob("*.html") + glob.glob("tutorials/*.html")

# Mapping of filename to the nav IDs that should be active
nav_mapping = {
    "index.html": "home",
    "start-here.html": "starthere",
    "tutorials.html": "tutorials",
    "services.html": "services",
    "about.html": "about",
    "contact.html": "contact"
}

def remove_aria_current(content):
    # Remove aria-current="page" from any link in the nav
    content = re.sub(r'\s*aria-current="page"', '', content)
    return content

def set_aria_current(content, active_id):
    # Add aria-current="page" to the specific ID
    # E.g., id="nav-desktop-tutorials"
    content = re.sub(f'(id="nav-desktop-{active_id}")', r'\1 aria-current="page"', content)
    content = re.sub(f'(id="nav-mobile-{active_id}")', r'\1 aria-current="page"', content)
    return content

count = 0
for f in html_files:
    basename = os.path.basename(f)
    
    # Determine the active nav id
    if basename in nav_mapping:
        active_id = nav_mapping[basename]
    elif f.startswith("tutorials/"):
        active_id = "tutorials"
    else:
        continue # like 404.html, old_index.html, etc.

    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = remove_aria_current(content)
    new_content = set_aria_current(new_content, active_id)
    
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        count += 1
        print(f"Fixed active nav state in {f} -> {active_id}")

print(f"Total files updated: {count}")
