import os
import glob

html_files = glob.glob("*.html")

skip_files = ['index.html', 'about.html', 'contact.html', 'start-here.html', 'services.html', 'success.html']

seo_text = """
<div class="mt-12 pt-8 border-t border-gray-200" id="reproducibility-section">
  <h3 class="text-2xl font-bold text-gray-900 mb-4">Methodology and Reproducibility Considerations</h3>
  <p class="mb-4">In computational biology and bioinformatics, executing the code is only one part of the scientific process. Ensuring that your analysis is statistically sound, biologically meaningful, and strictly reproducible is paramount. When adapting this workflow for your own datasets, it is crucial to carefully evaluate the underlying assumptions of each algorithmic step. For instance, default parameters in tools like Seurat, Scanpy, or standard aligners are often optimized for specific tissue types (e.g., PBMCs) or sequencing technologies. Applying these defaults blindly to different biological contexts—such as highly heterogeneous solid tumors or non-model organisms—can lead to severe artifacts, false-positive discoveries, or the loss of rare cell populations.</p>
  <p class="mb-4">Furthermore, we strongly recommend implementing strict environment management. The rapid evolution of bioinformatics software means that updating a single dependency (like NumPy, Pandas, or a Bioconductor package) can subtly alter downstream results. Always utilize package managers such as Conda or Mamba to isolate your project environments, and explicitly export your environment configurations (e.g., using <code>conda env export > environment.yml</code>). This practice not only safeguards your own longitudinal research but also ensures that peer reviewers and collaborative scientists can exactly replicate your computational findings years after publication.</p>
  <p>Finally, always maintain a rigorous quality control (QC) mindset. Computational pipelines will almost always run to completion and produce a result, even if the input data is heavily contaminated or mathematically flawed. It is the responsibility of the bioinformatician to integrate negative controls, perform batch-effect evaluations, and visually inspect intermediate data distributions before proceeding to downstream biological interpretation.</p>
</div>
"""

updated_count = 0

for file in html_files:
    if file in skip_files:
        continue
        
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check if already injected to avoid duplicates
    if 'id="reproducibility-section"' in content:
        continue
        
    # Find the end of the article
    if '</article>' in content:
        new_content = content.replace('</article>', seo_text + '\n</article>')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated_count += 1
        print(f"Enhanced {file}")

print(f"Successfully enhanced {updated_count} tutorials.")
