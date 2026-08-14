---
title: "Part 1: Metatranscriptomics Basics"
date: "2026-08-14"
author: "OmicsHub Team"
category: "Metatranscriptomics"
excerpt: "A guide to analyzing metatranscriptomic data, distinguishing active from dormant microbes, and using modern tools like HUMAnN3 and SAMSA2."
image: "images/bioinformatics-intro.png"
---

# Metatranscriptomics: Profiling the Active Microbiome

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
