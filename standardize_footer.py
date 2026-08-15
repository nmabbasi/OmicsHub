import glob

def extract_block(filepath, start_tag, end_tag):
    with open(filepath, 'r') as f:
        content = f.read()
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag) + len(end_tag)
    
    if start_idx != -1 and end_idx != -1:
        return content[start_idx:end_idx]
    return None

footer = extract_block('index.html', '<footer class="bg-gray-900 text-white mt-16">', '</footer>')

files_to_update = ['start-here.html', 'services.html', 'about.html', 'contact.html', 'success.html']

for filepath in files_to_update:
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        old_footer = extract_block(filepath, '<footer class="bg-gray-900 text-white mt-16">', '</footer>')
        # Some files might have slightly different footer tags, let's just search for '<footer' and '</footer>'
        if not old_footer:
            old_footer = extract_block(filepath, '<footer', '</footer>')

        if old_footer and footer:
            new_content = content.replace(old_footer, footer)
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated footer in {filepath}")
        else:
            print(f"Could not find footer in {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")
