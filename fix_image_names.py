import os
import glob

replacements = {
    "images/notebooklm-research-brain.webp": "images/notebooklm.webp",
    "images/deterministic-gget.webp": "images/gget-ai.webp",
    "images/protein-structure-design-alphafold.webp": "images/alphafold-esmfold.webp",
    "images/single-cell-foundation-models.webp": "images/foundation-models.webp",
    "images/advanced-ai-orchestration-bioinformatics.webp": "images/advanced-ai-orchestration.webp"
}

html_files = glob.glob("*.html")
for file in html_files:
    with open(file, "r") as f:
        content = f.read()
    
    modified = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            modified = True
            
    if modified:
        with open(file, "w") as f:
            f.write(content)
        print(f"Updated {file}")
