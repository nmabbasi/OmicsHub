---
title: "Taxonomic Profiling with Kraken2 and Bracken"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metagenomics"
excerpt: "Learn how to perform ultra-fast taxonomic classification of shotgun metagenomic reads using the k-mer based algorithms Kraken2 and Bracken."
image: "images/bioinformatics-intro.png"
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



# Taxonomic Profiling with Kraken2 and Bracken

## Introduction

In shotgun metagenomics, one of the primary goals is answering: **"Who is in this sample, and in what proportions?"** 

Unlike 16S amplicon sequencing, shotgun data contains fragmented DNA from every organism present. To classify millions of these short reads efficiently, we cannot use traditional alignment tools like BLAST—it would take months. Instead, we use ultra-fast **k-mer based classifiers**, with the undisputed industry standard being **Kraken2**, followed by **Bracken** for abundance estimation.

---

## 1. How Kraken2 Works

Kraken2 breaks down your reads into short sequences called *k-mers* (typically 35-mers). It then compares these k-mers against a massive pre-built database of known genomes. 

Instead of full alignment, Kraken2 maps the k-mer to the Lowest Common Ancestor (LCA) in the taxonomic tree.

### Running Kraken2

Kraken2 is heavily memory-bound. You need a machine with enough RAM to hold the database you choose (the standard PlusPFP database requires ~50GB of RAM).

```bash
# Run Kraken2 on paired-end Illumina reads
kraken2 --db /path/to/kraken2_database/ \
        --threads 16 \
        --paired reads_1.fastq.gz reads_2.fastq.gz \
        --report kraken2_report.txt \
        --output kraken2_output.txt
```

**Key Outputs:**
*   `kraken2_output.txt`: Contains the classification for *every single read*.
*   `kraken2_report.txt`: A human-readable summary of the percentage of reads assigned to each taxonomic level.

---

## 2. Correcting Abundances with Bracken

While Kraken2 is excellent at classification, its Lowest Common Ancestor (LCA) approach causes a problem: many reads are classified at higher taxonomic levels (like Genus or Family) because they match multiple species equally well. 

This means your raw Species-level counts in Kraken2 are mathematically underestimated.

**Bracken** (Bayesian Reestimation of Abundance with KrakEN) fixes this. It uses Bayesian probabilities to accurately push those Genus-level assignments down to the Species level, giving you highly accurate abundance estimations.

### Running Bracken

```bash
# Run Bracken using the Kraken2 report to estimate Species level (-l S) abundances
bracken -d /path/to/kraken2_database/ \
        -i kraken2_report.txt \
        -o bracken_species_abundances.tsv \
        -r 150 \
        -l S 
```
*(Note: `-r 150` should match your Illumina read length).*

---

## 3. Visualization

Once you have your Bracken outputs across multiple samples, you can merge them and visualize the community composition.

Tools like **Krona** create beautiful interactive HTML pie charts from Kraken2/Bracken reports.

```bash
# Install Krona tools
mamba install -c bioconda krona

# Generate an interactive Krona plot from the Kraken2 report
ktImportText kraken2_report.txt -o krona_visualization.html
```

By combining the blazing speed of Kraken2 with the statistical rigor of Bracken, you can profile complex microbial communities in minutes rather than months.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
