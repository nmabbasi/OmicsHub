import os
import re

lessons_dir = "lessons"

files_to_split = {
    "single-cell-rnaseq-introduction.md": {
        "prefix": "single-cell-rnaseq",
        "breakpoints": [
            "## The scRNA-seq Analysis Workflow",
            "## Advanced Analysis Techniques"
        ]
    },
    "command-line-basics-detailed.md": {
        "prefix": "command-line",
        "breakpoints": [
            "## Text Processing: The Bioinformatician's Superpower",
            "## Advanced Text Processing with `awk`"
        ]
    },
    "conda-mamba-installation-guide.md": {
        "prefix": "conda-mamba",
        "breakpoints": [
            "## Creating Environments"
        ]
    },
    "3-Writing_a_Submission_Script.md": {
        "prefix": "hpc-submission",
        "breakpoints": [
            "## Managing Jobs"
        ]
    }
}

new_tutorial_files = []

for filename, config in files_to_split.items():
    filepath = os.path.join(lessons_dir, filename)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Extract frontmatter
    frontmatter_match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not frontmatter_match:
        continue
        
    frontmatter_str = frontmatter_match.group(1)
    frontmatter = {}
    for line in frontmatter_str.split('\n'):
        m = re.match(r"^(\w+):\s*(.+)$", line)
        if m:
            frontmatter[m.group(1)] = m.group(2).strip('"\'')
            
    body = content[frontmatter_match.end():]
    
    # Split the body by the breakpoints
    parts = []
    current_part = []
    part_idx = 1
    
    for line in body.split('\n'):
        if line in config["breakpoints"]:
            parts.append('\n'.join(current_part))
            current_part = [line]
            part_idx += 1
        else:
            current_part.append(line)
            
    if current_part:
        parts.append('\n'.join(current_part))
        
    # Write the new files
    for i, part_content in enumerate(parts):
        new_filename = f"{config['prefix']}-part{i+1}.md"
        new_filepath = os.path.join(lessons_dir, new_filename)
        
        # Adjust title for parts
        part_title = f"{frontmatter.get('title', filename)} - Part {i+1}"
        
        new_frontmatter = f"""---
title: "{part_title}"
date: "{frontmatter.get('date', '2025-08-12')}"
author: "{frontmatter.get('author', 'Shell2R Team')}"
category: "{frontmatter.get('category', 'Bioinformatics')}"
excerpt: "Part {i+1} of the {frontmatter.get('title', 'tutorial')} series."
image: "{frontmatter.get('image', 'images/default.png')}"
---
"""
        with open(new_filepath, 'w') as f:
            f.write(new_frontmatter + "\n" + part_content)
            
        new_tutorial_files.append(new_filename)
        
    # Remove old file
    os.remove(filepath)
    print(f"Split {filename} into {len(parts)} parts.")

print("New files created:", new_tutorial_files)

# Update script.js with the new files list
script_path = "script.js"
with open(script_path, 'r') as f:
    script_content = f.read()

# We need to replace the tutorialFiles array in script.js
import ast

# The old list includes the files we didn't split, let's just get all .md files in lessons/
all_md_files = [f for f in os.listdir(lessons_dir) if f.endswith('.md')]

files_array_str = "        const tutorialFiles = [\n"
for md_file in all_md_files:
    files_array_str += f"            '{md_file}',\n"
files_array_str += "        ];"

# Find the start and end of tutorialFiles array
start_idx = script_content.find('const tutorialFiles = [')
if start_idx != -1:
    end_idx = script_content.find('];', start_idx) + 2
    script_content = script_content[:start_idx] + files_array_str + script_content[end_idx:]

with open(script_path, 'w') as f:
    f.write(script_content)

print("Updated script.js with new file list.")
