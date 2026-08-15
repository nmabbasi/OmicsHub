---
title: "Metagenomics Assembly"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metagenomics"
excerpt: "A hands-on guide to metagenomic pipelines, covering de novo assembly with SPAdes, mapping reads with BWA, and visualizing genomic alignments in IGV."
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



# Metagenomics: Assembly and Mapping

## Introduction to Metagenomics

Metagenomics is the study of genetic material recovered directly from environmental or clinical samples. Unlike traditional genomics, which sequences a single cultured organism, metagenomics sequences the entire community (the microbiome) simultaneously.

This tutorial covers a standard shotgun metagenomics workflow: assembling short reads into longer contigs using **SPAdes**, mapping reads to a reference genome (such as Human) using **BWA**, and visualizing the alignment with **IGV**.

---

## 1. De Novo Assembly using SPAdes

When you sequence a metagenome, you get millions of short reads (e.g., 150bp from Illumina). **De novo assembly** pieces these short reads together into longer contiguous sequences (contigs) without needing a reference genome.

**metaSPAdes** is a specialized module within the SPAdes assembler designed specifically to handle the uneven coverage and complex strain variation found in metagenomic data.

### Installation and Execution

```bash
# Install SPAdes via Mamba
mamba install -c bioconda spades

# Run metaSPAdes with paired-end reads
spades.py --meta \
          -1 sample_R1.fastq.gz \
          -2 sample_R2.fastq.gz \
          -o spades_output/ \
          -t 16 \
          -m 64
```
*   `--meta`: Activates the metagenome-specific algorithm.
*   `-t 16`: Uses 16 CPU threads.
*   `-m 64`: Allocates 64GB of RAM.

The most important output file will be `spades_output/contigs.fasta`, which contains your assembled metagenome.

---

## 2. Mapping to the Human Genome with BWA

In clinical metagenomics (e.g., gut or skin microbiomes), the sample often contains massive amounts of "host contamination" (human DNA). A critical preprocessing step is mapping the reads to the human reference genome to identify and remove the human DNA, leaving only the microbial reads.

We use **BWA (Burrows-Wheeler Aligner)**, specifically `bwa mem`, which is the standard for mapping high-quality short reads.

### Step 2.1: Indexing the Reference Genome

Before mapping, BWA requires an index of the reference genome.

> **Privacy & Ethics Note:** When working with human microbiome samples, the reads will contain human DNA (host contamination). It is critical to remove these reads before assembly or uploading to public repositories to protect patient privacy.

```bash
# Example: Downloading the human reference genome from NCBI
wget ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.39_GRCh38.p13/GCF_000001405.39_GRCh38.p13_genomic.fna.gz -O GRCh38.fasta.gz
gunzip GRCh38.fasta.gz

# Index the genome
bwa index GRCh38.fasta
```

### Step 2.2: Mapping Reads

```bash
# Map paired-end reads to the human genome
bwa mem -t 8 GRCh38.fasta sample_R1.fastq.gz sample_R2.fastq.gz > aligned_reads.sam
```

### Step 2.3: Processing with Samtools

The raw `.sam` file is large and plain text. We use **Samtools** to convert it to a compressed binary format (`.bam`), sort it, and index it for fast retrieval.

```bash
# Convert SAM to BAM, sort, and index
samtools view -S -b aligned_reads.sam > aligned_reads.bam
samtools sort aligned_reads.bam -o aligned_reads_sorted.bam
samtools index aligned_reads_sorted.bam
```

*Note: To extract only the unmapped (non-human) reads for downstream microbial analysis, you would use `samtools view -b -f 4`.*

---

## 3. Visualization with IGV

The **Integrative Genomics Viewer (IGV)** is an interactive tool for exploring large, integrated genomic datasets. It allows you to visually inspect how your reads aligned to the reference genome.

### How to use IGV

1.  **Download IGV:** Install the desktop application from the Broad Institute website.
2.  **Load the Genome:** Go to `Genomes > Load Genome from File` and select your `GRCh38.fasta`.
3.  **Load the Data:** Go to `File > Load from File` and select your `aligned_reads_sorted.bam`. (Ensure the `.bam.bai` index file is in the same directory).
4.  **Explore:** Type a gene name or genomic coordinate in the search bar.

### What to Look For
*   **Coverage depth:** The gray bar chart at the top shows how many reads cover a specific base.
*   **SNPs/Variants:** If a read differs from the reference genome, IGV highlights the mismatch in color (A=green, T=red, C=blue, G=orange).
*   **Insertions/Deletions:** Look for purple `I` symbols (insertions) or black horizontal lines within a read (deletions).

By mastering SPAdes, BWA, and IGV, you establish the foundation for any robust genomics or metagenomics pipeline.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
