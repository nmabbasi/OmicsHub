---
title: "Metatranscriptomics Basics"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metatranscriptomics"
excerpt: "A guide to analyzing metatranscriptomic data, distinguishing active from dormant microbes, and using modern tools like HUMAnN3 and SAMSA2."
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
    <li><strong>Prerequisites:</strong> Complete Metagenomics Assembly or Taxonomic Profiling and understand RNA-seq read processing.</li>
    <li><strong>Objective:</strong> Distinguish microbial community composition from gene-expression activity and outline a metatranscriptomic preprocessing workflow.</li>
    <li><strong>Expected Output:</strong> A workflow plan that records RNA QC, host/rRNA handling, reference choice, normalization, and an activity-oriented output.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Metatranscriptomics: Profiling the Active Microbiome

## Introduction

While metagenomics tells us what genes are *present* in a microbiome, **metatranscriptomics** tells us what genes are actually being *expressed* (the active transcripts). This distinction is critical because many microbes in an environment may be dead, dormant, or simply not transcribing specific metabolic pathways at a given moment.

Metatranscriptomics provides a functional snapshot of the microbiome under specific environmental or clinical conditions.

---

## 1. Challenges in Metatranscriptomics

Analyzing metatranscriptomic data is significantly more complex than metagenomics due to:

1.  **Host Contamination:** If sampling a human or animal, the vast majority of RNA will be host RNA.
2.  **rRNA Abundance:** Over 90% of a bacterium's RNA is ribosomal RNA (rRNA). Even with laboratory rRNA depletion kits, a massive computational filtering step is required to isolate the mRNA (messenger RNA) that encodes for functional proteins.
3.  **Lack of Reference Genomes:** Mapping transcripts to highly diverse, uncultured microbial communities is computationally intensive.

---

## 2. Standard Workflow and New Tools

The modern metatranscriptomic pipeline involves QC, host/rRNA removal, taxonomic profiling, and functional annotation.

### Step 1: rRNA and Host Filtering (SortMeRNA / Bowtie2)

Before analyzing functions, you must remove non-mRNA reads. **SortMeRNA** is the industry standard for rapidly filtering ribosomal RNA from metatranscriptomic data.

```bash
# Filter rRNA using SortMeRNA
sortmerna --ref smr_v4.3_default_db.fasta \
          --reads sample_raw.fastq \
          --aligned sample_rRNA.fastq \
          --other sample_mRNA.fastq \
          --fastx
```
*The resulting `sample_mRNA.fastq` will be used for downstream analysis.*

Next, map the remaining reads against the host genome (e.g., Human GRCh38) using `bowtie2` and discard mapped reads.

### Step 2: Taxonomic and Functional Profiling (HUMAnN 3)

The **HUMAnN 3** (HMP Unified Metabolic Analysis Network) pipeline is a premier tool for determining "what is the community doing?" It performs both taxonomic profiling (via MetaPhlAn) and functional profiling in a single workflow.

**How HUMAnN 3 works:**
1.  **Tier 1:** Maps reads to a database of functionally annotated pangenomes of the species detected in your sample.
2.  **Tier 2:** Any reads that fail to map are subjected to translated search (using Diamond) against a comprehensive protein database (UniRef90).

```bash
# Run HUMAnN 3 on your mRNA reads
humann --input sample_mRNA.fastq \
       --output humann_results/ \
       --threads 16
```

**Key Outputs:**
*   `_genefamilies.tsv`: Abundance of specific gene families (often mapped to UniRef).
*   `_pathabundance.tsv`: Abundance of entire metabolic pathways (e.g., glycolysis, short-chain fatty acid production).

### Step 3: SAMSA2 Pipeline

An alternative to HUMAnN 3 is **SAMSA2**, a highly scalable pipeline designed specifically for metatranscriptomics on HPC clusters.

SAMSA2 excels at handling massive datasets by parallelizing the annotation steps using Diamond to map reads directly against the NCBI RefSeq database or the SEED database.

```bash
# Example SAMSA2 Diamond annotation step
diamond blastx -d refseq_db \
               -q sample_mRNA.fastq \
               -a samsa_output \
               -t /dev/shm \
               -k 1
```

## Summary

Metatranscriptomics unlocks the functional reality of microbiomes. By combining rigorous depletion methods like SortMeRNA with highly optimized functional profiling tools like HUMAnN 3 or SAMSA2, researchers can transition from knowing *who* is in an environment to understanding *what* they are actively doing.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why can metatranscriptomic abundance not be interpreted in the same way as metagenomic DNA abundance?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">For a supplied sample, list the preprocessing steps needed before functional or taxonomic expression analysis and justify each step. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If an apparent pathway change is driven by one library with low depth or high rRNA carryover, what normalization and QC checks are needed?</p>
    </div>
  </div>
</div>
