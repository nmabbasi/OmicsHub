import os
import glob

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 1. Update branding
    content = content.replace("OmicsHub", "The Omics Hub")
    content = content.replace(">S2R<", ">BioHub<")
    content = content.replace("S2R: Shell to R Workflows", "The Omics Hub")
    content = content.replace("nmabbasi.github.io/OmicsHub", "nmabbasi.github.io/S2R")
    
    # 2. Visually improve the hero section and global elements (Tailwind classes)
    # Old gradient: bg-gradient-to-r from-blue-600 to-purple-600
    # New premium gradient: bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900
    content = content.replace("bg-gradient-to-r from-blue-600 to-purple-600", "bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900")
    
    # Modernize the button in the hero
    content = content.replace("bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors duration-200 shadow-lg", 
                              "bg-blue-600 text-white border border-blue-500 px-8 py-3 rounded-lg font-semibold text-lg hover:bg-blue-700 hover:shadow-blue-500/30 transition-all duration-300 shadow-lg transform hover:-translate-y-1")
    
    # Modernize the navbar logo box
    # It used the same gradient. Let's make it vibrant blue
    content = content.replace("bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 rounded-lg flex items-center justify-center", "bg-blue-600 rounded-lg flex items-center justify-center shadow-md shadow-blue-500/30")

    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Updated {filepath}")

# Find all HTML files
html_files = glob.glob("**/*.html", recursive=True)
for file in html_files:
    process_file(file)

