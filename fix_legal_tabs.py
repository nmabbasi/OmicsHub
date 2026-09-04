import os

pages = {
    'privacy.html': 'Privacy Policy',
    'terms.html': 'Terms of Service',
    'disclaimer.html': 'Disclaimer',
    'cookie.html': 'Cookie Policy'
}

tab_data = [
    ('privacy.html', 'Privacy Policy'),
    ('terms.html', 'Terms of Service'),
    ('disclaimer.html', 'Disclaimer'),
    ('cookie.html', 'Cookie Policy')
]

for filename, active_tab_name in pages.items():
    filepath = os.path.join('pages', filename)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find the start and end of the legal-tabs div
    start_str = '<div class="legal-tabs'
    end_str = '</div>'
    
    start_idx = content.find(start_str)
    if start_idx == -1:
        continue
        
    # Find the matching closing div
    temp_idx = start_idx
    open_divs = 0
    end_idx = -1
    
    while temp_idx < len(content):
        if content[temp_idx:temp_idx+4] == '<div':
            open_divs += 1
        elif content[temp_idx:temp_idx+6] == '</div>':
            open_divs -= 1
            if open_divs == 0:
                end_idx = temp_idx + 6
                break
        temp_idx += 1
        
    if end_idx == -1:
        continue
        
    # Generate the new tabs HTML
    new_tabs = '    <div class="flex overflow-x-auto border-b border-gray-100 bg-gray-50 p-2 gap-2 hide-scrollbar items-center justify-start sm:justify-center">\n'
    
    for tab_file, tab_name in tab_data:
        if tab_name == active_tab_name:
            # Active tab
            new_tabs += f'      <a href="{tab_file}" class="inline-flex items-center justify-center whitespace-nowrap px-5 py-2.5 text-sm font-bold bg-[#123B5D] text-white rounded-lg shadow-md transition-transform transform scale-100">{tab_name}</a>\n'
        else:
            # Inactive tab
            new_tabs += f'      <a href="{tab_file}" class="inline-flex items-center justify-center whitespace-nowrap px-5 py-2.5 text-sm font-medium text-gray-600 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg transition-colors">{tab_name}</a>\n'
            
    new_tabs += '    </div>'
    
    new_content = content[:start_idx] + new_tabs + content[end_idx:]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
print("Updated all legal tabs in pages directory.")
