import glob

desktop_target = '<a href="index.html#all-tutorials" id="nav-desktop-tutorials" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all cursor-pointer">Tutorials</a>'
desktop_replacement = desktop_target + '\n<a href="https://nmabbasi.github.io/HPC" target="_blank" id="nav-desktop-hpc" class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all flex items-center gap-1">HPC Guide <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>'

mobile_target = '<a href="index.html#all-tutorials" id="nav-mobile-tutorials" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer">Tutorials</a>'
mobile_replacement = mobile_target + '\n<a href="https://nmabbasi.github.io/HPC" target="_blank" id="nav-mobile-hpc" class="px-4 py-2 text-sm text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors flex items-center gap-1">HPC Guide <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>'


for filepath in glob.glob('*.html'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if desktop_target in content and 'nav-desktop-hpc' not in content:
            content = content.replace(desktop_target, desktop_replacement)
            
        if mobile_target in content and 'nav-mobile-hpc' not in content:
            content = content.replace(mobile_target, mobile_replacement)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")
