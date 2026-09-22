with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

# We will inject the author section right before the "Browse Full Catalogue CTA"
# which is marked by <!-- Browse Full Catalogue CTA -->

author_section = """
<!-- Meet the Author Section -->
<section class="py-20 bg-slate-50 border-t border-gray-100">
    <div class="container mx-auto px-6">
        <div class="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
            <div class="w-48 h-48 md:w-64 md:h-64 flex-shrink-0">
                <img src="images/bioinformatics-expert.webp" alt="Nasir Mahmood Abbasi, PhD" class="w-full h-full object-cover rounded-full shadow-2xl border-4 border-white" onerror="this.src='https://placehold.co/400x400/123B5D/FFF?text=NA'" loading="lazy">
            </div>
            <div>
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-bold mb-4">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
                    Verified Expert
                </div>
                <h2 class="text-3xl font-extrabold text-slate-900 mb-2">Meet the Author: **Abbasi N**, PhD</h2>
                <h3 class="text-xl text-blue-600 font-medium mb-4">Computational Biologist & Data Scientist</h3>
                <p class="text-slate-600 mb-6 leading-relaxed text-lg">
                    Welcome to The Omics Hub. I hold a Ph.D. in Bioinformatics and specialize in single-cell transcriptomics, metagenomics, and HPC cluster management. I built this platform because I noticed a massive gap between academic theory and practical, command-line execution in biological research. 
                </p>
                <p class="text-slate-600 mb-8 leading-relaxed">
                    Every tutorial on this site is born from real-world challenges I've solved in the lab. Whether you are struggling with Seurat integration, debugging a Nextflow pipeline on a Slurm cluster, or annotating a reference genome, these guides are designed to give you the exact, reproducible code you need to succeed. My goal is to demystify complex data analysis so you can focus on the biology.
                </p>
                <a href="about.html" class="inline-flex items-center gap-2 text-blue-600 font-bold hover:text-blue-800 transition-colors">
                    Read my full academic journey &rarr;
                </a>
            </div>
        </div>
    </div>
</section>

<!-- Browse Full Catalogue CTA -->
"""

if "Meet the Author Section" not in content:
    new_content = content.replace("<!-- Browse Full Catalogue CTA -->", author_section)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Added Author Section to index.html")
else:
    print("Author Section already exists.")
