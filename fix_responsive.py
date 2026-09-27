import glob
import re
import os

fixes = 0

# Fix 1: Policy pages - make the 3-col legal nav grid responsive
print("=== Fix 1: Policy page legal nav grids ===")
policy_pages = glob.glob('pages/*.html')
for pf in policy_pages:
    with open(pf, 'r') as f:
        content = f.read()
    original = content
    
    # Change grid-cols-3 to grid-cols-1 sm:grid-cols-3
    content = content.replace(
        'class="mt-8 grid grid-cols-3 gap-4 text-sm"',
        'class="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm"'
    )
    
    if content != original:
        with open(pf, 'w') as f:
            f.write(content)
        fixes += 1
        print(f"  Fixed: {os.path.basename(pf)}")

# Fix 2: Check tutorials for any tables without overflow wrappers
print("\n=== Fix 2: Tutorial tables without overflow wrapper ===")
tutorial_files = sorted(glob.glob('tutorials/*.html'))
for tf in tutorial_files:
    with open(tf, 'r') as f:
        content = f.read()
    original = content
    
    # Wrap bare <table> tags in a scrollable div
    # But only if they're not already inside an overflow wrapper
    if '<table' in content:
        # Check if table already has overflow wrapper
        # Pattern: <div...overflow...>...<table
        # We'll do a simple check: find tables that are NOT preceded by overflow
        def wrap_table(match):
            table = match.group(0)
            # Check if preceding text already has overflow wrapper
            return f'<div class="overflow-x-auto -mx-4 px-4 mb-6">{table}'
        
        # Find tables that aren't already in overflow containers
        # Simple approach: look for <table that isn't preceded by overflow-x-auto
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if '<table' in line:
                # Check if previous non-empty lines have overflow wrapper
                prev_context = '\n'.join(new_lines[-3:]) if len(new_lines) >= 3 else ''
                if 'overflow-x-auto' not in prev_context and 'overflow-auto' not in prev_context:
                    # Add wrapper before table
                    new_lines.append('<div class="overflow-x-auto -mx-4 px-4">')
                    new_lines.append(line)
                    # Find closing </table> and add closing </div>
                    while i < len(lines):
                        if '</table>' in lines[i] and i != len(new_lines) - 1:
                            new_lines.append(lines[i])
                            new_lines.append('</div>')
                            break
                        elif i == len(new_lines) - 1:
                            pass  # Already added
                        else:
                            new_lines.append(lines[i])
                        i += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        
        if content != original:
            with open(tf, 'w') as f:
                f.write(content)
            fixes += 1
            print(f"  Wrapped tables in: {os.path.basename(tf)}")

# Fix 3: Check cookie.html specifically for its table
print("\n=== Fix 3: Cookie policy table ===")
cookie_path = 'pages/cookie.html'
if os.path.exists(cookie_path):
    with open(cookie_path, 'r') as f:
        content = f.read()
    original = content
    
    if '<table' in content:
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if '<table' in line:
                prev_context = '\n'.join(new_lines[-3:]) if len(new_lines) >= 3 else ''
                if 'overflow-x-auto' not in prev_context and 'overflow-auto' not in prev_context:
                    new_lines.append('<div class="overflow-x-auto -mx-4 px-4">')
                    new_lines.append(line)
                    while i < len(lines):
                        if '</table>' in lines[i] and '</table>' not in new_lines[-1]:
                            new_lines.append(lines[i])
                            new_lines.append('</div>')
                            break
                        else:
                            new_lines.append(lines[i])
                        i += 1
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            i += 1
        
        content = '\n'.join(new_lines)
        if content != original:
            with open(cookie_path, 'w') as f:
                f.write(content)
            fixes += 1
            print(f"  Wrapped cookie table")

print(f"\nTotal fixes applied: {fixes}")
