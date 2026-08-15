import glob
import os

def extract_block(filepath, start_tag, end_tag):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except Exception:
        return None
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag) + len(end_tag)
    
    if start_idx != -1 and end_idx != -1:
        return content[start_idx:end_idx]
    return None

def update_file(filepath, new_header, new_footer, depth=0):
    with open(filepath, 'r') as f:
        content = f.read()
        
    old_header = extract_block(filepath, '<header', '</header>')
    old_footer = extract_block(filepath, '<footer', '</footer>')
    
    changed = False
    
    if old_header and new_header:
        # adjust links if depth > 0
        adj_header = new_header
        if depth > 0:
            prefix = "../" * depth
            # just simple replacements for local links
            adj_header = adj_header.replace('href="index.html"', f'href="{prefix}index.html"')
            adj_header = adj_header.replace('href="start-here.html"', f'href="{prefix}start-here.html"')
            adj_header = adj_header.replace('href="services.html"', f'href="{prefix}services.html"')
            adj_header = adj_header.replace('href="about.html"', f'href="{prefix}about.html"')
            adj_header = adj_header.replace('href="contact.html"', f'href="{prefix}contact.html"')
            adj_header = adj_header.replace('href="pages/', f'href="{prefix}pages/')
            adj_header = adj_header.replace('src="images/', f'src="{prefix}images/')
            
        if content.find(adj_header) == -1:
            content = content.replace(old_header, adj_header)
            changed = True
            
    if old_footer and new_footer:
        adj_footer = new_footer
        if depth > 0:
            prefix = "../" * depth
            adj_footer = adj_footer.replace('href="index.html', f'href="{prefix}index.html')
            adj_footer = adj_footer.replace('href="about.html"', f'href="{prefix}about.html"')
            adj_footer = adj_footer.replace('href="contact.html"', f'href="{prefix}contact.html"')
            adj_footer = adj_footer.replace('href="pages/', f'href="{prefix}pages/')
        
        if content.find(adj_footer) == -1:
            content = content.replace(old_footer, adj_footer)
            changed = True
            
    if changed:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")


header = extract_block('index.html', '<header class="bg-white border-b border-gray-200 sticky top-0 z-50">', '</header>')
footer = extract_block('index.html', '<footer class="bg-gray-900 text-white mt-16">', '</footer>')

if not header or not footer:
    print("Could not extract header/footer from index.html")
    exit(1)

# Root files
for filepath in glob.glob("*.html"):
    if filepath != 'index.html':
        update_file(filepath, header, footer, depth=0)

# Pages directory
for filepath in glob.glob("pages/*.html"):
    update_file(filepath, header, footer, depth=1)

print("Done scanning all HTML files.")
