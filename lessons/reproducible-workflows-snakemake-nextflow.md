---
title: "Snakemake & Nextflow"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Workflow & Containerization"
excerpt: "Learn how to transition from messy bash scripts to highly scalable, reproducible bioinformatics pipelines using Snakemake and Nextflow."
image: "images/command-line-terminal.png"
---


<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-200 mb-6">
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span><strong>Tested on:</strong> Python 3.11, R 4.3.2, Ubuntu 24.04</span>
  </div>
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
    <span><strong>Last Review:</strong> 2026-08-15</span>
  </div>
</div>

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Reproducible Bioinformatics Workflows

## The Problem with Bash Scripts

When analyzing a single dataset, a simple Bash script (e.g., running FastQC, then BWA, then Samtools) works fine. However, as your projects grow to hundreds of samples, simple scripts fail:
*   If the pipeline crashes halfway, you have to manually figure out where to restart.
*   They don't automatically parallelize across High-Performance Computing (HPC) nodes.
*   They are difficult for other researchers to reproduce.

The solution is using a **Workflow Manager**. The two absolute industry standards in bioinformatics are **Snakemake** and **Nextflow**.

---

## 1. Snakemake: Python-Based Pipelines

**Snakemake** is built on top of Python. If you already know Python, the syntax will feel incredibly familiar. It uses a "make-like" logic: you define the final *output* files you want, and Snakemake works backward to find the *rules* required to create them.

### Basic Structure of a Snakefile

You define pipelines in a file called `Snakefile`.

```python
# A simple Snakemake rule to align reads using BWA
rule bwa_map:
    input:
        ref="genome.fa",
        reads="data/samples/{sample}.fastq.gz"
    output:
        "mapped_reads/{sample}.bam"
    threads: 8
    shell:
        "bwa mem -t {threads} {input.ref} {input.reads} | samtools view -Sb - > {output}"
```

### Running Snakemake

```bash
# Run the pipeline locally using 16 cores
snakemake --cores 16

# Submit the pipeline to an HPC cluster (Slurm)
snakemake --profile slurm
```

Snakemake automatically tracks which samples have been processed. If sample 5 fails, you just re-run the exact same command, and Snakemake will *only* process sample 5!

---

## 2. Nextflow: Enterprise-Grade Scalability

**Nextflow** uses a Groovy-based Domain Specific Language (DSL2). While the learning curve is slightly steeper than Snakemake, Nextflow is the backbone of massive institutional pipelines (such as the nf-core project).

Nextflow excels at "dataflow" programming. You define *processes*, and data flows between them through *channels*.

### Basic Structure of a Nextflow Script (`main.nf`)

```groovy
// Define a process
process BWA_ALIGN {
    cpus 8
    
    input:
    tuple val(sample_id), path(reads)
    path reference
    
    output:
    path "${sample_id}.bam"
    
    script:
    """
    bwa mem -t ${task.cpus} $reference $reads | samtools view -Sb - > ${sample_id}.bam
    """
}

// Define the workflow pipeline
workflow {
    read_ch = Channel.fromFilePairs('data/samples/*_{1,2}.fastq.gz')
    ref_ch  = file('genome.fa')
    
    BWA_ALIGN(read_ch, ref_ch)
}
```

### nf-core: The True Power of Nextflow

The biggest advantage of Nextflow is **nf-core**: a massive community repository of highly curated, peer-reviewed pipelines. 
Instead of writing your own RNA-seq pipeline, you can simply run the community standard:

```bash
# Run the gold-standard nf-core RNA-seq pipeline directly from GitHub
nextflow run nf-core/rnaseq -profile docker --input samplesheet.csv --outdir results/
```

## Summary

*   Use **Snakemake** if you want to quickly wrap your existing Python/Bash scripts into a robust pipeline.
*   Use **Nextflow** if you are building enterprise-level pipelines, or if you want to utilize the incredible pre-built `nf-core` pipelines.


---


## References

1. Official tool documentation and package vignettes.
2. Stuart, T., et al. (2019). Comprehensive Integration of Single-Cell Data. *Cell*, 177(7), 1888-1902.e21. (For Seurat-based workflows)
3. Orchestrating Single-Cell Analysis with Bioconductor (OSCA) - A comprehensive guide to single-cell data analysis.
4. [Bioconductor](https://bioconductor.org/) and [CRAN](https://cran.r-project.org/) package manuals.

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
