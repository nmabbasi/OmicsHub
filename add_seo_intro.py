with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

seo_section = """
<!-- SEO Introduction Section -->
<section class="py-12 bg-white">
    <div class="container mx-auto px-6 max-w-4xl text-center">
        <h2 class="text-2xl md:text-3xl font-extrabold text-slate-900 mb-6">Master Computational Biology and Bioinformatics</h2>
        <p class="text-lg text-slate-600 leading-relaxed">
            Welcome to the premier resource for biological data science. The Omics Hub provides comprehensive, reproducible, and highly technical tutorials designed specifically for researchers. From foundational Linux command-line skills and High-Performance Computing (HPC) cluster management, to advanced <strong>single-cell RNA-seq (scRNA-seq)</strong>, metagenomics, and multi-omics integration workflows. Learn how to deploy modern pipelines using Nextflow and Snakemake, analyze spatial transcriptomics data, and leverage AI agents to accelerate your genomic discoveries.
        </p>
    </div>
</section>

<section class="py-20 bg-slate-50" id="topics">
"""

if "Master Computational Biology and Bioinformatics" not in content:
    # Replace the opening of the topics section with our injected section + topics section
    new_content = content.replace('<section class="py-20 bg-white" id="topics">', seo_section)
    if new_content != content:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Added SEO Intro to index.html")
else:
    print("SEO Intro already exists.")
