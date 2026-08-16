import os
import glob

lessons_dir = '/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/lessons'
md_files = glob.glob(os.path.join(lessons_dir, '*.md'))

ref_block = """
## References

1. Official tool documentation and package vignettes.
2. Stuart, T., et al. (2019). Comprehensive Integration of Single-Cell Data. *Cell*, 177(7), 1888-1902.e21. (For Seurat-based workflows)
3. Orchestrating Single-Cell Analysis with Bioconductor (OSCA) - A comprehensive guide to single-cell data analysis.
4. [Bioconductor](https://bioconductor.org/) and [CRAN](https://cran.r-project.org/) package manuals.
"""

for file_path in md_files:
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if a references section already exists
    if "## References" in content or "# References" in content or "## Further Reading" in content:
        continue

    # Inject right before the Knowledge Check block
    target = '<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">'

    if target in content:
        new_content = content.replace(target, ref_block + "\n" + target)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Added references to {os.path.basename(file_path)}")
