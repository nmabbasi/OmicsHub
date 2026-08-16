import glob

def extract_block(filepath, start_tag, end_tag):
    with open(filepath, 'r') as f:
        content = f.read()

    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag) + len(end_tag)

    if start_idx != -1 and end_idx != -1:
        return content[start_idx:end_idx]
    return None

header = extract_block('index.html', '<header class="bg-white border-b border-gray-200 sticky top-0 z-50">', '</header>')

files_to_update = ['start-here.html', 'services.html', 'about.html', 'contact.html', 'success.html']

for filepath in files_to_update:
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        old_header = extract_block(filepath, '<header class="bg-white border-b border-gray-200 sticky top-0 z-50">', '</header>')
        if old_header and header:
            new_content = content.replace(old_header, header)
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated header in {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")
