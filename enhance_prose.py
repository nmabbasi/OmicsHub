#!/usr/bin/env python3
"""
Enhance tutorial prose for AdSense approval.

For each tutorial HTML file, this script injects additional explanatory
paragraphs AFTER each existing <p> tag that precedes a <pre> code block.
It also adds a "Why This Matters" intro and "Key Takeaways" summary
section before the Knowledge Check.

The content is topic-aware: each tutorial slug maps to custom prose.
"""

import re
import os
import sys

# ─── Per-tutorial enhancement content ───────────────────────────────────────
# Each key is the HTML filename (without .html).
# Each value is a dict with:
#   "section_prose": dict mapping h2 text (substring) -> list of <p> strings to inject after that section's intro paragraph
#   "why_matters":   HTML string for the "Why This Matters" callout
#   "takeaways":     list of bullet strings for "Key Takeaways"

ENHANCEMENTS = {

"scrna-seq-basics": {
    "section_prose": {
        "From Raw Counts": [
            "<p>Single-cell RNA sequencing has fundamentally transformed our ability to study cellular heterogeneity within complex tissues. Unlike traditional bulk RNA-seq, which averages gene expression across millions of cells and masks rare cell populations, scRNA-seq captures the transcriptome of each individual cell. This resolution is critical for understanding how distinct cell types contribute to tissue function, disease progression, and therapeutic response. Researchers working with tumor microenvironments, developing immune atlases, or studying stem cell differentiation all rely on scRNA-seq to reveal biological complexity that bulk methods simply cannot detect.</p>",
            "<p>The computational workflow described in this tutorial follows a well-established analytical paradigm that has been refined over years of community development. The pipeline begins with quality control to remove technical artifacts such as empty droplets and damaged cells, then proceeds through normalization to correct for sequencing depth differences, dimensionality reduction to identify the most informative genes, and finally clustering to group cells with similar transcriptional profiles. Each step involves critical parameter choices that can significantly affect downstream biological interpretations, which is why understanding the rationale behind each step is just as important as knowing which function to call.</p>",
        ],
        "Loading the Data": [
            "<p>The 10x Genomics filtered feature-barcode matrix typically contains three files: <code>barcodes.tsv.gz</code> (cell identifiers), <code>features.tsv.gz</code> (gene names and IDs), and <code>matrix.mtx.gz</code> (the sparse count matrix in Market Exchange format). This sparse representation is essential because most gene-cell combinations have zero counts, and storing only the non-zero entries dramatically reduces memory usage. When working with datasets containing hundreds of thousands of cells, efficient data structures become a practical necessity rather than an optimization. The AnnData object in Python and the Seurat object in R both implement compressed sparse storage internally, enabling analyses that would otherwise require hundreds of gigabytes of RAM.</p>",
        ],
        "Quality Control": [
            "<p>Quality control in single-cell experiments is fundamentally different from bulk RNA-seq QC because the unit of analysis is an individual cell rather than a pooled sample. Each droplet in a 10x Chromium experiment may contain a healthy cell, a dying cell, an empty droplet with only ambient RNA, or even two cells captured together (a doublet). Mitochondrial gene percentage serves as a proxy for cell viability because damaged cells with compromised membranes lose cytoplasmic mRNA while retaining mitochondrial transcripts, leading to artificially elevated mitochondrial fractions. However, the appropriate threshold varies substantially between tissue types: metabolically active cells such as cardiomyocytes naturally express higher mitochondrial levels, so blindly applying a 5% cutoff would eliminate biologically relevant cells. Always visualize the distribution of QC metrics before setting thresholds, and consider using adaptive methods such as median absolute deviation filtering for unbiased cutoff selection.</p>",
        ],
        "Normalization, Scaling": [
            "<p>Library-size normalization addresses the technical reality that different droplets capture different quantities of mRNA molecules, making raw counts between cells incomparable. The standard approach of scaling each cell to a common total (typically 10,000 counts) followed by log transformation has proven robust across most experimental designs, though alternative methods such as scran pooling-based normalization or sctransform variance-stabilizing transformation may perform better in specific contexts. The log transformation serves dual purposes: it reduces the dynamic range of expression values so that highly expressed genes do not dominate the analysis, and it makes the data approximately normally distributed, which is an implicit assumption of many downstream statistical methods including PCA. Highly variable gene selection is a critical dimensionality reduction step that focuses the analysis on genes whose expression varies meaningfully across cells, filtering out both housekeeping genes with uniform expression and lowly detected genes dominated by technical noise.</p>",
        ],
        "Neighborhood Graph": [
            "<p>The k-nearest neighbors graph is the mathematical foundation upon which both clustering and visualization depend. For each cell, the algorithm identifies its k most similar neighbors based on Euclidean distance in PCA space, then constructs a weighted graph where edge weights reflect the strength of similarity between connected cells. The Leiden algorithm (or its predecessor Louvain) then partitions this graph into communities of densely connected cells, which we interpret as biologically distinct cell types or states. The resolution parameter directly controls the granularity of clustering: lower values produce fewer, broader clusters, while higher values produce more fine-grained subdivisions. There is no universally correct resolution, and the appropriate choice depends on the biological question being asked. UMAP embedding provides a two-dimensional visualization of the high-dimensional graph structure, but it is important to remember that UMAP distances between clusters are not directly interpretable as biological distances, and the visualization should be used for qualitative assessment rather than quantitative comparison.</p>",
        ],
    },
    "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">🔬 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Single-cell RNA sequencing is now the gold standard for dissecting cellular heterogeneity in virtually every area of biomedical research, from developmental biology to cancer immunology. Understanding the standard computational workflow is an essential skill for any bioinformatician or computational biologist entering this field.</p>
  <p class="text-amber-800">This tutorial provides a complete, reproducible foundation that you will build upon in every subsequent single-cell analysis. The choices you make here regarding quality control thresholds, normalization strategy, and clustering resolution will propagate through all downstream analyses including trajectory inference, cell-cell communication, and differential expression testing.</p>
</div>""",
    "takeaways": [
        "scRNA-seq captures individual cell transcriptomes, revealing heterogeneity invisible to bulk methods",
        "QC thresholds must be adapted per dataset by inspecting metric distributions, not copied blindly",
        "Library-size normalization and log transformation make cells comparable despite sequencing depth variation",
        "The k-nearest neighbors graph is the core data structure driving both clustering and UMAP visualization",
        "Resolution parameter tuning determines cluster granularity and should match your biological question",
        "Always document software versions, parameter choices, and filtering decisions for reproducibility",
    ],
},

"scrna-seq-integration-strategies": {
    "section_prose": {
        "batch": [
            "<p>Batch effects represent one of the most pervasive challenges in single-cell genomics. Whenever samples are processed on different days, sequenced on different lanes, or prepared using different reagent lots, systematic technical variation is introduced that can confound biological signal. Without proper correction, these batch effects can cause cells to cluster by sample origin rather than by cell type, leading to false biological conclusions. The mathematical strategies for removing batch effects while preserving genuine biological variation have been the subject of intense methodological development, and choosing the right approach depends on the experimental design, the nature of the batches, and the biological questions being asked.</p>",
            "<p>Harmony, RPCA, and CCA represent three fundamentally different mathematical philosophies for solving the integration problem. Harmony operates in PCA space and iteratively adjusts cell embeddings using soft k-means clustering and ridge regression, making it fast and memory-efficient for large datasets. Reciprocal PCA (RPCA) identifies shared biological variation by projecting each dataset into the other's PCA space and finding mutual nearest neighbors, which is more conservative and less likely to over-correct genuine biological differences between conditions. Canonical Correlation Analysis (CCA) identifies correlated gene programs across datasets by maximizing the correlation between shared canonical variates, making it powerful when datasets share cell types but have substantial technical differences. Each method has trade-offs in speed, memory usage, and the risk of over-correction versus under-correction.</p>",
        ],
    },
    "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">🔬 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Nearly every modern single-cell experiment involves combining data from multiple samples, patients, or conditions. Without rigorous batch integration, downstream analyses will be dominated by technical artifacts rather than biological signal, potentially leading to incorrect conclusions about cell type composition, disease mechanisms, or treatment effects.</p>
  <p class="text-amber-800">Understanding the mathematical principles behind Harmony, RPCA, and CCA empowers you to select the appropriate method for your specific experimental design and to critically evaluate whether integration has been successful or has introduced distortions.</p>
</div>""",
    "takeaways": [
        "Batch effects can dominate biological signal if not properly addressed during integration",
        "Harmony is fast and works well for most standard multi-sample experiments",
        "RPCA is more conservative and better preserves condition-specific differences",
        "CCA maximizes correlation and works well when datasets share cell types but differ technically",
        "Always validate integration success using quantitative metrics like LISI scores, not just UMAP visuals",
    ],
},

"command-line-part1": {
    "section_prose": {
        "essential": [
            "<p>The Unix command line is the foundational interface through which virtually all bioinformatics analysis is conducted. While graphical tools exist for many common tasks, the command line provides unmatched flexibility, reproducibility, and scalability that are essential for processing the large datasets typical of modern genomics. Learning to navigate the file system, manage directories, and manipulate files from the terminal is not merely a technical skill but a prerequisite for every subsequent bioinformatics workflow, from read alignment to statistical analysis. Mastering these core commands will save you countless hours and enable you to work efficiently on both local machines and remote high-performance computing clusters.</p>",
            "<p>Understanding the hierarchical file system structure of Unix-like operating systems is the first conceptual hurdle for biologists transitioning to computational work. Unlike graphical file managers where you click through folder icons, the terminal requires you to specify file locations using paths. An absolute path begins from the root directory and uniquely identifies any file on the system, while a relative path describes a location in relation to your current working directory. The distinction between these two path types is critical for writing reproducible scripts, because absolute paths ensure your commands work regardless of where they are executed, while relative paths make your code portable across different systems where the directory structure may vary.</p>",
        ],
    },
    "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">💻 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Every bioinformatics pipeline, from genome assembly to single-cell analysis, ultimately runs through the command line. Whether you are submitting jobs on an HPC cluster, connecting to a cloud server, or processing sequencing data locally, proficiency with basic shell navigation is a non-negotiable requirement.</p>
  <p class="text-amber-800">The commands covered in this tutorial form the vocabulary of all subsequent computational work. Investing time to internalize these fundamentals now will make every future tutorial, pipeline, and troubleshooting session dramatically more efficient.</p>
</div>""",
    "takeaways": [
        "The command line provides reproducibility and scalability that GUI tools cannot match",
        "Understanding absolute versus relative paths is essential for writing portable scripts",
        "Core commands like cd, ls, cp, mv, and rm form the foundation of all bioinformatics workflows",
        "Tab completion and command history dramatically improve terminal productivity",
        "File permissions control who can read, write, and execute files on shared systems",
    ],
},

"command-line-part2": {
    "section_prose": {
        "grep": [
            "<p>Text processing is arguably the most practically useful skill in the bioinformatics command-line toolkit. Biological data files such as FASTA sequences, VCF variant calls, GTF gene annotations, and SAM alignment records are all structured text formats that can be efficiently queried, filtered, and transformed using standard Unix utilities. Rather than loading a multi-gigabyte file into a spreadsheet or writing a custom Python script for simple operations, experienced bioinformaticians use grep, sed, cut, and sort to accomplish in seconds what might otherwise take minutes or hours.</p>",
            "<p>The <code>grep</code> command (Global Regular Expression Print) searches input for lines matching a specified pattern and prints them to standard output. In bioinformatics, grep is indispensable for tasks such as extracting all entries for a specific chromosome from a BED file, counting the number of reads mapping to a particular gene, or searching log files for error messages. Regular expressions extend grep's power by allowing pattern matching with wildcards, character classes, and quantifiers, enabling sophisticated queries like finding all gene symbols that begin with 'HOX' followed by any letter and digit combination.</p>",
        ],
        "sed": [
            "<p>The stream editor <code>sed</code> performs text transformations on input streams without opening files in an interactive editor. Its most common use in bioinformatics is search-and-replace operations across large files: converting chromosome naming conventions between UCSC and Ensembl formats, standardizing sample identifiers in metadata files, or removing header lines from data files before piping them into analysis tools. Understanding sed's substitution syntax allows you to perform complex batch transformations that would be tedious and error-prone to do manually.</p>",
        ],
        "cut": [
            "<p>The <code>cut</code> command extracts specific columns from tabular data, which is essential for working with the column-based file formats that pervade bioinformatics. When you need to extract just the gene names from a GTF file, pull specific INFO fields from a VCF, or isolate sample columns from an expression matrix, cut provides a fast and memory-efficient solution. Combined with <code>sort</code> and <code>uniq</code>, you can quickly compute frequency tables, identify duplicate entries, and perform basic data summarization entirely from the command line.</p>",
        ],
    },
    "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">💻 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Text processing commands are the Swiss Army knife of bioinformatics. The ability to quickly filter, extract, and transform biological data files directly from the terminal saves hours of work compared to loading files into R, Python, or spreadsheet applications.</p>
  <p class="text-amber-800">These skills become especially valuable when working on HPC clusters where graphical tools are unavailable, when debugging pipeline failures by inspecting intermediate files, or when performing quick sanity checks on large datasets before committing to computationally expensive analyses.</p>
</div>""",
    "takeaways": [
        "grep searches for patterns in text and is essential for filtering biological data files",
        "sed performs stream-based text transformations without loading entire files into memory",
        "cut extracts specific columns from tabular formats like BED, VCF, and TSV files",
        "sort and uniq together enable frequency counting and deduplication operations",
        "Combining these tools with pipes creates powerful one-liner data processing workflows",
    ],
},

"command-line-part3": {
    "section_prose": {
        "awk": [
            "<p>Advanced shell scripting transforms the command line from a tool for individual tasks into a platform for building complete, automated analysis pipelines. While basic commands handle simple operations, real bioinformatics workflows require conditional logic, loop constructs, variable substitution, and error handling. AWK, in particular, is a complete programming language designed specifically for processing structured text data, making it exceptionally well-suited for biological file formats where each line contains multiple tab-separated fields with different data types.</p>",
            "<p>Pipes and redirects are the connective tissue that links individual commands into coherent workflows. The pipe operator sends the output of one command directly as input to the next, creating processing chains that can filter, transform, and summarize data in a single compound command. Output redirection writes results to files, while input redirection feeds file contents to commands expecting standard input. Understanding these I/O mechanisms is essential for constructing the multi-step data processing pipelines that are the backbone of modern computational biology.</p>",
        ],
    },
    "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">💻 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Advanced shell scripting is what separates occasional terminal users from productive bioinformaticians. The ability to write reusable scripts with proper error handling, logging, and parameterization is essential for creating reproducible analyses that can be shared with collaborators and reviewers.</p>
  <p class="text-amber-800">AWK in particular remains one of the most efficient tools for processing the columnar text files that dominate bioinformatics, often outperforming equivalent Python scripts by an order of magnitude for simple data extraction and transformation tasks.</p>
</div>""",
    "takeaways": [
        "AWK is a specialized language for processing columnar text data in biological file formats",
        "Pipes chain commands together, enabling complex data processing in single compound statements",
        "Shell scripts with proper error handling ensure reproducible and robust analysis pipelines",
        "Variables and loops enable parameterized scripts that adapt to different datasets",
        "Well-structured scripts with logging make troubleshooting and auditing straightforward",
    ],
},

}

# ─── Generic enhancement for tutorials without specific content ──────────────
# Maps slug prefixes/categories to generic prose that's still topically relevant

CATEGORY_PROSE = {
    "scrna-seq": {
        "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">🔬 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Single-cell genomics is one of the fastest-evolving fields in computational biology, with new methods, tools, and best practices emerging regularly. Mastering the analytical techniques covered in this tutorial positions you at the forefront of a discipline that is reshaping our understanding of cellular biology, disease mechanisms, and therapeutic development.</p>
  <p class="text-amber-800">The skills learned here directly transfer to real-world research applications including tumor microenvironment characterization, immune cell profiling, developmental biology, and drug discovery programs that increasingly rely on single-cell resolution data.</p>
</div>""",
        "generic_prose": "<p>Single-cell analysis techniques have undergone rapid evolution since the first scRNA-seq protocols were published. Modern experimental platforms such as 10x Genomics Chromium, Parse Biosciences, and BD Rhapsody can profile tens of thousands to millions of cells in a single experiment, generating datasets of unprecedented scale and complexity. This explosion in data generation has driven parallel advances in computational methods, with the Scanpy and Seurat ecosystems continuously expanding to incorporate new algorithms for normalization, integration, clustering, and interpretation. Staying current with best practices in this field requires understanding not just the mechanics of running code, but the statistical and biological assumptions that underpin each analytical choice.</p>",
        "takeaways": [
            "Single-cell methods reveal cellular heterogeneity invisible to bulk approaches",
            "Parameter choices at each analysis step can significantly impact biological conclusions",
            "Reproducibility requires documenting software versions, parameters, and filtering decisions",
            "Visual validation should always complement quantitative assessment metrics",
            "Understanding the mathematical foundations helps troubleshoot unexpected results",
        ],
    },
    "command-line": {
        "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">💻 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Command-line proficiency is the single most transferable technical skill in bioinformatics. Regardless of which specific tools, pipelines, or programming languages you ultimately adopt, the ability to navigate file systems, process text data, and automate repetitive tasks through the shell remains universally essential.</p>
  <p class="text-amber-800">These foundational skills will serve you throughout your computational biology career, whether you work in academic research, pharmaceutical development, clinical genomics, or biotechnology.</p>
</div>""",
        "generic_prose": "<p>The Unix command line has remained the primary interface for bioinformatics work for decades, and its dominance shows no signs of waning. This longevity reflects fundamental advantages: shell commands are inherently scriptable and therefore reproducible, they can process data streams without loading entire files into memory, and they compose naturally through pipes and redirects. For biologists transitioning from graphical interfaces, the initial learning curve can feel steep, but the investment pays dividends almost immediately in terms of efficiency, scalability, and the ability to work on remote servers and high-performance computing clusters where graphical interfaces are typically unavailable.</p>",
        "takeaways": [
            "Command-line skills are essential for all bioinformatics workflows",
            "Shell commands are inherently reproducible and scriptable",
            "Text processing tools handle large biological files efficiently",
            "Practice with real data files accelerates learning significantly",
        ],
    },
    "metagenomics": {
        "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">🦠 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Metagenomics and metatranscriptomics have opened windows into microbial communities that were previously inaccessible through culture-based methods. Understanding the computational approaches for analyzing these complex, multi-organism datasets is increasingly important across fields ranging from environmental science to human health and precision medicine.</p>
  <p class="text-amber-800">The analytical skills covered here are directly applicable to microbiome research, environmental monitoring, infectious disease surveillance, and agricultural biotechnology.</p>
</div>""",
        "generic_prose": "<p>Metagenomic and metatranscriptomic analyses present unique computational challenges compared to single-organism genomics. The data contains reads from potentially thousands of different species mixed together, with widely varying genome sizes, GC content, and abundance levels. Computational tools must handle this complexity while maintaining sensitivity for detecting low-abundance organisms and specificity for avoiding false taxonomic assignments. The choice of reference database, classification algorithm, and abundance estimation method can substantially influence biological conclusions, making it essential to understand the strengths and limitations of each approach rather than treating any single tool as a black box.</p>",
        "takeaways": [
            "Metagenomics reveals microbial community composition without requiring culture",
            "Database choice significantly impacts taxonomic classification accuracy",
            "Functional profiling complements taxonomic analysis for biological interpretation",
            "Quality control must account for host contamination in clinical samples",
            "Statistical frameworks designed for compositional data are essential for valid comparisons",
        ],
    },
    "default": {
        "why_matters": """<div class="p-6 bg-amber-50 border border-amber-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-amber-900 mb-3">📘 Why This Tutorial Matters</h3>
  <p class="text-amber-800 mb-2">Bioinformatics is an inherently interdisciplinary field that requires combining biological domain knowledge with computational skills and statistical reasoning. Each tutorial in this series builds upon previous concepts while introducing new tools and analytical frameworks, creating a comprehensive learning path from fundamental skills to advanced research-grade analyses.</p>
  <p class="text-amber-800">The techniques and best practices covered here reflect current community standards and are directly applicable to real research projects in genomics, transcriptomics, proteomics, and multi-omics integration.</p>
</div>""",
        "generic_prose": "<p>Modern bioinformatics workflows increasingly require practitioners to understand not just which buttons to press, but why each analytical step is performed and how parameter choices affect downstream results. This conceptual understanding is what separates routine data processing from genuine scientific analysis, enabling researchers to make informed decisions when standard approaches fail, when results are ambiguous, or when novel experimental designs require adapted analytical strategies. By grounding technical procedures in their underlying rationale, this tutorial aims to build both competence and confidence in your bioinformatics practice.</p>",
        "takeaways": [
            "Understanding the rationale behind each step is as important as knowing the commands",
            "Parameter choices should be justified and documented for reproducibility",
            "Visualization is a critical component of quality assessment at every stage",
            "Combining computational skills with biological knowledge produces the best analyses",
            "Community-developed best practices continuously evolve as methods improve",
        ],
    },
}


def get_category(slug):
    """Determine category for a tutorial slug."""
    for prefix in ["scrna-seq", "command-line", "metagenomics", "metatranscriptomics"]:
        if slug.startswith(prefix):
            cat = prefix.replace("metatranscriptomics", "metagenomics")
            if cat in CATEGORY_PROSE:
                return cat
    return "default"


def build_takeaways_html(items):
    """Build a Key Takeaways HTML section."""
    bullets = "\n".join(f'      <li>{item}</li>' for item in items)
    return f"""<div class="p-6 bg-green-50 border border-green-200 rounded-xl mb-8">
  <h3 class="text-lg font-bold text-green-900 mb-3">✅ Key Takeaways</h3>
  <ul class="list-disc list-inside text-green-800 space-y-2">
{bullets}
  </ul>
</div>"""


def enhance_file(filepath):
    """Enhance a single tutorial HTML file with additional prose."""
    slug = os.path.basename(filepath).replace(".html", "")
    
    with open(filepath, "r") as f:
        html = f.read()

    category = get_category(slug)
    specific = ENHANCEMENTS.get(slug, {})
    cat_data = CATEGORY_PROSE.get(category, CATEGORY_PROSE["default"])

    changed = False

    # 1) Inject "Why This Matters" after the learning objectives box
    why_html = specific.get("why_matters", cat_data["why_matters"])
    marker = '</div>\n\n<h2>'  # End of objectives box, start of first h2
    if why_html and marker in html and "Why This Tutorial Matters" not in html:
        html = html.replace(marker, f'</div>\n\n{why_html}\n\n<h2>', 1)
        changed = True

    # 2) Inject section-specific prose
    section_prose = specific.get("section_prose", {})
    for heading_substr, paragraphs in section_prose.items():
        for para in paragraphs:
            if para not in html:
                # Find the h2 containing this substring, then inject after its first <p>...</p>
                pattern = re.compile(
                    r'(<h2>[^<]*' + re.escape(heading_substr) + r'[^<]*</h2>\s*<p>.*?</p>)',
                    re.DOTALL
                )
                match = pattern.search(html)
                if match:
                    html = html[:match.end()] + "\n" + para + html[match.end():]
                    changed = True

    # 3) Inject generic category prose if word count is still low
    prose_matches = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
    prose_text = ' '.join(re.sub(r'<[^>]+>', ' ', p) for p in prose_matches)
    word_count = len(prose_text.split())

    generic = cat_data.get("generic_prose", "")
    if word_count < 600 and generic and generic not in html:
        # Insert before the Conclusion h2
        conclusion_pattern = re.compile(r'(<h2>Conclusion</h2>)')
        match = conclusion_pattern.search(html)
        if match:
            html = html[:match.start()] + generic + "\n" + html[match.start():]
            changed = True
        else:
            # Insert before Knowledge Check
            kc_pattern = re.compile(r'(<div class="mt-10 p-8 bg-gray-50)')
            match = kc_pattern.search(html)
            if match:
                html = html[:match.start()] + generic + "\n" + html[match.start():]
                changed = True

    # 4) Inject Key Takeaways before Knowledge Check
    takeaways = specific.get("takeaways", cat_data.get("takeaways", []))
    if takeaways and "Key Takeaways" not in html:
        takeaways_html = build_takeaways_html(takeaways)
        kc_pattern = re.compile(r'(<div class="mt-10 p-8 bg-gray-50)')
        match = kc_pattern.search(html)
        if match:
            html = html[:match.start()] + takeaways_html + "\n" + html[match.start():]
            changed = True

    if changed:
        with open(filepath, "w") as f:
            f.write(html)
        # Recount
        prose_matches = re.findall(r'<p>(.*?)</p>', html, re.DOTALL)
        prose_text = ' '.join(re.sub(r'<[^>]+>', ' ', p) for p in prose_matches)
        new_count = len(prose_text.split())
        return new_count
    return None


def main():
    tutorial_dir = os.path.dirname(os.path.abspath(__file__))
    skip = {"index.html", "about.html", "contact.html", "services.html", "start-here.html", "success.html"}
    
    files = sorted(f for f in os.listdir(tutorial_dir)
                   if f.endswith(".html") and f not in skip)
    
    enhanced = 0
    for f in files:
        path = os.path.join(tutorial_dir, f)
        result = enhance_file(path)
        if result is not None:
            print(f"  ✅ {f}: now {result} prose words")
            enhanced += 1
        else:
            print(f"  ⏭️  {f}: already enhanced or no changes needed")
    
    print(f"\nEnhanced {enhanced}/{len(files)} tutorials")


if __name__ == "__main__":
    main()
