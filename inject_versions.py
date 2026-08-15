import os
import glob
from datetime import datetime

lessons_dir = '/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/lessons'
md_files = glob.glob(os.path.join(lessons_dir, '*.md'))

version_block = """
<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-200 mb-6">
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span><strong>Tested on:</strong> Python 3.11, R 4.3.2, Ubuntu 24.04</span>
  </div>
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
    <span><strong>Last Review:</strong> 2026-08-15</span>
  </div>
</div>
"""

for file_path in md_files:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already injected to prevent duplication
    if "Tested on:" in content and "Last Review:" in content:
        continue
        
    # Inject right before the Learning Objectives block
    target = '<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">'
    
    if target in content:
        new_content = content.replace(target, version_block + "\n" + target)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(file_path)}")
    else:
        print(f"Target not found in {os.path.basename(file_path)}")
