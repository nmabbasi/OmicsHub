---
title: "Metagenomics Assembly"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metagenomics"
excerpt: "A hands-on guide to metagenomic pipelines, covering de novo assembly with SPAdes, mapping reads with BWA, and visualizing genomic alignments in IGV."
image: "images/metagenomics-assembly-mapping.png"
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
    <li><strong>Prerequisites:</strong> Complete Quality Control Fundamentals, command-line basics, and understand paired-end reads and assemblies.</li>
    <li><strong>Objective:</strong> Plan a metagenomic assembly workflow, map reads back to contigs, and interpret coverage and assembly-quality evidence.</li>
    <li><strong>Expected Output:</strong> An assembly-and-mapping report that records input reads, assembler settings, mapping rate, coverage, and quality limitations.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Metagenomics: Assembly and Mapping

## Introduction to Metagenomics

Metagenomics is the study of genetic material recovered directly from environmental or clinical samples. Unlike traditional genomics, which sequences a single cultured organism, metagenomics sequences the entire community (the microbiome) simultaneously.

This tutorial covers a standard shotgun metagenomics workflow: assembling short reads into longer contigs using **SPAdes**, mapping reads to a reference genome (such as Human) using **BWA**, and visualizing the alignment with **IGV**.

---

## 1. Remove Host Reads Before Assembly

When a clinical or host-associated metagenome may contain human DNA, remove host-mapping read pairs **before** assembly. This protects privacy, reduces non-microbial assembly content, and keeps downstream interpretation focused on the microbial fraction. For environmental samples without a host component, document why this step is not required.

> **Privacy & ethics note:** Human-mapping reads should not be uploaded to public repositories or assembled as microbial contigs without the appropriate governance and institutional approvals.

### Step 1.1: Prepare and index the host reference

```bash
# Download a documented reference build, then preserve the URL and checksum in your project manifest.
curl -L -o GRCh38.fa.gz "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_genomic.fna.gz"
gunzip GRCh38.fa.gz
bwa index GRCh38.fa
```

### Step 1.2: Map reads and retain read pairs that do not map to the host

```bash
# Keep the alignment for an auditable host-removal summary.
bwa mem -t 8 GRCh38.fa sample_R1.fastq.gz sample_R2.fastq.gz   | samtools sort -o host_screened.bam
samtools index host_screened.bam

# Extract pairs for which both mates are unmapped, then convert them back to paired FASTQ.
samtools view -b -f 12 -F 256 host_screened.bam   | samtools sort -n -o nonhost.name_sorted.bam
samtools fastq -n   -1 microbial_R1.fastq.gz   -2 microbial_R2.fastq.gz   -0 /dev/null -s /dev/null   nonhost.name_sorted.bam
```

Record the total read pairs before and after host screening. A non-empty `microbial_R1.fastq.gz` and matching `microbial_R2.fastq.gz` are the inputs for the assembly step.

---

## 2. De Novo Assembly using metaSPAdes

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

## 3. Map the Microbial Reads Back to the Assembled Contigs

Mapping the screened reads back to `contigs.fasta` checks which contigs are supported by the observed reads and helps identify uneven coverage.

```bash
# Assemble only the non-host read pairs
mamba install -c conda-forge -c bioconda spades samtools bwa
spades.py --meta   -1 microbial_R1.fastq.gz   -2 microbial_R2.fastq.gz   -o spades_output/   -t 16   -m 64

# Map the microbial reads back to assembled contigs
bwa index spades_output/contigs.fasta
bwa mem -t 8 spades_output/contigs.fasta microbial_R1.fastq.gz microbial_R2.fastq.gz   | samtools sort -o reads_to_contigs.bam
samtools index reads_to_contigs.bam
samtools flagstat reads_to_contigs.bam
samtools depth -a reads_to_contigs.bam > contig_depth.tsv
```

The key deliverables are `spades_output/contigs.fasta`, the mapping summary from `samtools flagstat`, and `contig_depth.tsv`. Interpret low-support contigs cautiously, especially in uneven communities.

---

## 4. Visualization with IGV

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
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is read mapping back to assembled contigs important before interpreting a metagenomic assembly?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run a small test assembly or inspect supplied contigs, then map reads and summarize mapping rate and per-contig coverage. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If assembly quality is poor, how will you investigate read quality, contamination, sequencing depth, k-mer settings, and uneven community abundance?</p>
    </div>
  </div>
</div>
