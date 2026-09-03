#!/usr/bin/env python3
"""Pass 3: Inject topic-specific prose before Knowledge Check for tutorials still below 700 words."""
import re, os

# slug -> list of paragraphs to inject before Knowledge Check
BOOST = {
"reproducible-project-structure": [
    "Reproducibility is a cornerstone of scientific integrity, yet computational analyses frequently fail to meet even basic reproducibility standards. Studies have shown that a substantial proportion of published bioinformatics analyses cannot be independently replicated due to incomplete documentation, missing software version information, and disorganized file structures. Establishing a standardized project structure from the outset addresses these challenges systematically by creating a clear, self-documenting framework that facilitates both internal reproducibility and external review.",
    "A well-organized project directory separates raw input data, processing scripts, intermediate results, and final outputs into clearly labeled subdirectories. Raw data should be treated as immutable and stored separately from any processed derivatives, ensuring that the original inputs can always be traced and the analysis can be re-executed from scratch if needed. Scripts should be numbered or ordered to reflect the analytical workflow, with each script reading from and writing to predictable locations. This organizational discipline is particularly important for collaborative projects where multiple researchers need to navigate the same file structure.",
    "Investing time in project organization at the beginning of an analysis yields substantial returns throughout the project lifecycle. Structured projects are easier to debug when results are unexpected, simpler to extend when reviewers request additional analyses, and more straightforward to archive for long-term preservation. For graduate students and postdoctoral researchers, maintaining well-organized project repositories also facilitates the knowledge transfer that occurs when leaving a laboratory, ensuring that years of analytical work remain accessible and usable by future team members.",
],
"python-fundamentals-bioinformatics": [
    "Python has emerged as one of the two dominant programming languages in bioinformatics, alongside R, owing to its readable syntax, extensive scientific computing ecosystem, and strong community support. For biologists beginning their computational journey, Python offers a gentle learning curve that does not sacrifice power or flexibility. The language's design philosophy emphasizes code readability and simplicity, which makes Python scripts more accessible to collaborators who may not be experienced programmers. In the bioinformatics context, Python serves as the foundation for major analysis frameworks including Scanpy for single-cell analysis, Biopython for sequence manipulation, and pandas for tabular data processing.",
    "Understanding fundamental data types and data structures is essential before attempting to write bioinformatics scripts. Variables in Python can hold different types of data including strings for DNA sequences and gene names, integers for read counts and chromosome positions, floating-point numbers for expression values and p-values, and boolean values for logical filtering operations. Collections such as lists, dictionaries, and sets provide organized ways to store and access multiple related values, which is critical when working with biological data that inherently involves collections of genes, samples, and measurements.",
    "Mastering Python fundamentals opens the door to the vast ecosystem of bioinformatics libraries that handle everything from sequence alignment to machine learning-based cell type annotation. The skills covered in this tutorial, including variable manipulation, file input and output, function definition, and basic string processing, form the building blocks for increasingly sophisticated analyses. Proficiency with these foundations enables you to read, modify, and debug existing bioinformatics scripts, which is often more valuable in practice than writing code from scratch.",
],
"r-tidyverse-fundamentals": [
    "R is the statistical programming language of choice for a large proportion of the bioinformatics community, particularly for statistical analysis, data visualization, and genomics applications. The Bioconductor repository provides thousands of specialized packages for genomic data analysis, including Seurat for single-cell RNA-seq, DESeq2 for differential expression, and clusterProfiler for functional enrichment. Understanding R fundamentals is therefore not merely an academic exercise but a practical necessity for any computational biologist who needs to interact with the broader bioinformatics ecosystem.",
    "R's fundamental data structures, including vectors, data frames, matrices, and factors, are designed with statistical analysis in mind. Vectors are the atomic data type in R, and understanding how vectorized operations work is essential for writing efficient and idiomatic R code. Data frames, and their modern tidyverse equivalent tibbles, provide the tabular data structure that maps naturally to biological experiment metadata, gene expression matrices, and variant annotation tables. Factors encode categorical variables with defined levels, which is important for correctly specifying experimental conditions, tissue types, and treatment groups in statistical models.",
    "The tidyverse collection of packages, including dplyr for data manipulation, ggplot2 for visualization, and tidyr for data reshaping, provides a consistent and readable grammar for data analysis that has become the standard approach in modern R programming. Learning to compose analytical workflows using pipe operators creates self-documenting code that reads like a description of the analysis steps, which significantly improves reproducibility and collaboration.",
],
"reference-genomes-annotation": [
    "The choice of reference genome and gene annotation is one of the most consequential decisions in any genomics workflow, yet it is frequently treated as an afterthought. Using an outdated genome build, an incompatible annotation version, or mismatched identifier systems can introduce systematic errors that propagate through every subsequent analysis step, from read alignment to differential expression to functional interpretation.",
    "Major genome assembly versions such as GRCh37 and GRCh38 for human differ in coordinate systems, chromosome naming conventions, and the inclusion of alternative haplotype sequences and patch scaffolds. Mixing coordinates from different assemblies without proper liftover conversion is a common source of errors that can cause genes to be assigned incorrect genomic positions or missed entirely. Gene annotation databases including Ensembl, GENCODE, and RefSeq use different gene models, transcript definitions, and identifier systems, which means that gene counts produced using one annotation are not directly comparable to those produced using another.",
    "Documenting the exact genome build, annotation version, and identifier mapping used in an analysis is a non-negotiable requirement for reproducible research. This information should be recorded in the methods section of any publication and preserved alongside the analysis code and results.",
],
"data-visualization-fundamentals": [
    "Data visualization serves dual purposes in bioinformatics: it is both an analytical tool for exploring data and discovering patterns, and a communication tool for presenting findings to collaborators and reviewers. Effective visualization requires understanding not just the technical mechanics of generating plots, but also the perceptual principles that determine how humans interpret visual information. Color choices, axis scaling, aspect ratios, and annotation placement all influence whether a figure accurately conveys the underlying data or inadvertently misleads the viewer.",
    "Quality control visualizations are among the most important plots in any bioinformatics workflow because they inform the filtering decisions that shape all downstream results. Distribution plots of key metrics such as library size, gene detection rate, and mitochondrial content reveal sample quality and help identify outlier cells or failed samples. PCA plots and their nonlinear counterparts such as UMAP and t-SNE provide low-dimensional summaries of high-dimensional data, but these embeddings involve information loss and parameter sensitivity that must be acknowledged when drawing biological conclusions.",
    "The distinction between exploratory visualization and publication-ready figures is important for efficient workflow management. During analysis, quick diagnostic plots with default aesthetics are sufficient for decision-making. Final figures for manuscripts and presentations require careful attention to color accessibility, font sizes appropriate for the target display medium, and consistent styling across all panels.",
],
"research-reporting-interpretation": [
    "Scientific communication is the mechanism through which experimental findings enter the shared knowledge base of the research community. For computational analyses in particular, the methods section must contain sufficient detail to enable independent replication, including software versions, parameter settings, reference datasets, and any manual curation steps.",
    "Writing reproducible methods descriptions requires balancing completeness with readability. Every analytical choice that could affect the results should be documented, but the narrative should flow logically rather than reading as a parameter dump. Effective strategies include organizing the methods in the order of the analytical workflow, grouping related tools and parameters together, and providing brief justifications for non-standard choices. Figure legends should describe what is shown, how it was generated, and what statistical tests were applied, enabling readers to evaluate the evidence independently.",
    "Biological interpretation is the most intellectually demanding aspect of computational research because it requires integrating quantitative results with domain-specific knowledge to generate meaningful conclusions. Over-interpreting statistical associations as causal relationships, drawing conclusions from underpowered analyses, or ignoring confounding variables are common pitfalls that undermine the credibility of otherwise technically sound work.",
],
"git-github-bioinformatics": [
    "Version control is a foundational practice for reproducible computational research that has been widely adopted from software engineering into bioinformatics. Git tracks every change made to every file in a project, creating a complete history that enables researchers to understand how an analysis evolved over time, revert to previous states when experiments fail, and identify exactly when a particular result was generated.",
    "GitHub extends Git's local version control capabilities with remote hosting, collaboration features, and project management tools that are increasingly important for scientific computing. Public repositories serve as supplementary materials for publications, providing reviewers and readers with access to the exact code used to generate published results. Issues and pull requests create documented records of analytical decisions and code review processes.",
    "Adopting version control early in a research career pays compounding dividends over time. The initial investment in learning Git commands and workflows is modest compared to the long-term benefits of having a complete, searchable record of every analytical decision, a reliable backup system for code and documentation, and a professional portfolio of computational work that demonstrates technical competence to future employers and collaborators.",
],
"biological-data-formats": [
    "Understanding the standard file formats used in bioinformatics is a prerequisite for every computational analysis, from quality control through to biological interpretation. Each format was designed to encode specific types of biological information efficiently, and the conventions governing field ordering, coordinate systems, and header specifications are not arbitrary but reflect practical requirements for interoperability between tools.",
    "The FASTA and FASTQ formats represent nucleotide and protein sequences, with FASTQ additionally encoding per-base quality scores that reflect the confidence of each base call. Understanding Phred quality scores and their relationship to base call error probabilities is essential for setting appropriate quality filtering thresholds during read preprocessing. SAM and BAM formats encode read alignments against a reference genome and contain rich metadata including mapping quality, CIGAR strings describing the alignment structure, and optional tags for mate pair status and duplicate marking.",
    "Familiarity with these formats enables you to inspect intermediate files at any stage of a pipeline, which is invaluable for debugging unexpected results. Tools such as samtools, bcftools, bedtools, and tabix provide efficient random access and manipulation capabilities. Developing the habit of examining file contents directly rather than relying solely on downstream tool output builds the diagnostic intuition that distinguishes proficient bioinformaticians from those who treat their workflows as opaque systems.",
],
"quality-control-fundamentals": [
    "Quality control is the analytical gatekeeper that determines whether downstream results reflect genuine biology or are dominated by technical artifacts. In genomics experiments, sources of technical variation include library preparation efficiency, sequencing depth, sample degradation, reagent lot effects, and instrument performance fluctuations. QC procedures must be applied at every stage of the analytical workflow because different types of artifacts manifest at different stages and require distinct detection strategies.",
    "Read-level quality assessment using tools such as FastQC and MultiQC examines the distribution of base quality scores, GC content, adapter contamination, sequence duplication levels, and overrepresented sequences across all reads in a sequencing run. These metrics collectively characterize the technical quality of the sequencing data and can reveal problems such as failed flow cell tiles, contamination from adapter dimers, or library complexity issues that affect the interpretability of downstream analyses.",
    "The philosophy underlying quality control in bioinformatics is fundamentally about establishing confidence in the data before investing computational resources in analysis and biological interpretation. Spending time on thorough QC at the beginning of a project prevents the far more costly scenario of discovering data quality issues after weeks of analysis.",
],
"experimental-design-batch-effects": [
    "Experimental design is arguably the most critical determinant of whether a genomics study will yield reliable and interpretable results. No amount of computational sophistication can rescue a poorly designed experiment, because confounding between biological variables of interest and technical batch effects renders the data fundamentally uninterpretable.",
    "Biological replicates capture the natural variation between independent experimental units, such as individual patients, separate tissue samples, or independently cultured cell populations. This variation is essential for statistical inference because it defines the denominator of hypothesis tests and determines the generalizability of findings. Technical replicates, which measure the same biological sample multiple times, quantify measurement precision but do not contribute to estimating biological variability.",
    "Batch effect mitigation strategies should be implemented at the experimental design stage rather than relying solely on computational correction methods. Balanced designs that distribute biological conditions evenly across processing batches ensure that batch effects and biological effects are orthogonal and therefore separable.",
],
"statistics-for-bioinformatics": [
    "Statistical reasoning is the framework that enables bioinformaticians to distinguish genuine biological signals from technical noise and random variation. Genomics datasets are characterized by high dimensionality, complex correlation structures, and heterogeneous noise profiles that violate the assumptions of many classical statistical tests.",
    "Probability distributions provide the mathematical models that describe the expected behavior of biological measurements under null hypotheses. Gene expression count data from RNA-seq experiments typically follow negative binomial distributions, which account for both the Poisson sampling noise inherent in sequencing and the biological overdispersion observed across samples.",
    "Multiple testing correction is perhaps the most important statistical concept for genomics researchers to internalize. When testing thousands of genes simultaneously for differential expression, the expected number of false positives under the null hypothesis scales linearly with the number of tests. Methods such as the Benjamini-Hochberg procedure control the false discovery rate by adjusting p-values to account for the multiplicity of comparisons.",
],
}

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    enhanced = 0
    for slug, paragraphs in BOOST.items():
        fpath = os.path.join(base, slug + ".html")
        if not os.path.exists(fpath):
            print(f"  SKIP {slug}.html (not found)")
            continue
        with open(fpath) as f:
            html = f.read()
        
        # Check if already injected
        if paragraphs[0][:60] in html:
            print(f"  ⏭️  {slug}.html: already has pass3 content")
            continue
        
        # Find injection point: before Knowledge Check or Next Steps
        for marker in ['<h2>Knowledge Check', '<h2>Next Steps', '<div class="mt-10 p-8']:
            idx = html.find(marker)
            if idx > 0:
                block = "\n".join(f"<p>{p}</p>" for p in paragraphs)
                html = html[:idx] + block + "\n" + html[idx:]
                with open(fpath, 'w') as f:
                    f.write(html)
                # Recount
                prose = ' '.join(re.findall(r'<p>(.*?)</p>', html, re.DOTALL))
                prose = re.sub(r'<[^>]+>', ' ', prose)
                pw = len(prose.split())
                print(f"  ✅ {slug}.html: now {pw} prose words")
                enhanced += 1
                break
        else:
            print(f"  ⚠️  {slug}.html: no insertion marker found")
    
    print(f"\nPass 3 enhanced: {enhanced} tutorials")

if __name__ == "__main__":
    main()
