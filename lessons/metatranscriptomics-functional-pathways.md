---
title: "Functional Pathway Analysis with HUMAnN 3"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metatranscriptomics"
excerpt: "Dive deep into metatranscriptomics by mapping active RNA transcripts to complete metabolic pathways using HUMAnN 3 and the MetaCyc database."
image: "images/bioinformatics-intro.png"
---

# Functional Pathway Analysis in Metatranscriptomics

## Introduction

In our previous metatranscriptomics guide, we discussed the critical first step: filtering out the massive abundance of ribosomal RNA (rRNA) using SortMeRNA to isolate the functional messenger RNA (mRNA). 

Once you have your clean mRNA reads, the next goal is functional profiling: **What specific biochemical pathways are the microbes actively utilizing?** The absolute gold standard for this analysis is **HUMAnN 3**.

---

## 1. How HUMAnN 3 Works

HUMAnN 3 (The HMP Unified Metabolic Analysis Network) is highly sophisticated. It uses a tiered approach to maximize both speed and accuracy:

*   **Tier 1 (Nucleotide level):** It first runs `MetaPhlAn` to determine exactly which species are present in your sample. It then dynamically builds a custom database of the pangenomes for *only* those specific species. It maps your mRNA reads to this custom database using Bowtie2. This is extremely fast and accurate.
*   **Tier 2 (Translated search):** Any reads that fail to map to the known species' pangenomes (the "unclassified" reads) are translated into proteins and searched against the massive **UniRef90** protein database using DIAMOND. This is slower, but ensures you capture functional genes even from unknown or unculturable species.

---

## 2. Running the HUMAnN 3 Pipeline

```bash
# Assuming you have your rRNA-depleted mRNA reads
humann --input sample_mRNA.fastq.gz \
       --output humann_out/ \
       --threads 16 \
       --taxonomic-profile metaphlan_bugs_list.tsv # Optional: provide pre-computed taxonomy
```

### Understanding the MetaCyc Database

HUMAnN 3 maps the individual gene families it finds into complete metabolic pathways using the **MetaCyc** database. 

Why MetaCyc instead of KEGG? MetaCyc is heavily focused on experimentally elucidated pathways and is highly curated for microbial metabolism, whereas KEGG is broader and includes many eukaryotic-specific signaling pathways that are irrelevant to microbiome research.

---

## 3. Interpreting HUMAnN Outputs

HUMAnN 3 generates three primary output files:

1.  **`pathabundance.tsv`**: The abundance of complete metabolic pathways (e.g., *GLYCOLYSIS-E-D: superpathway of glycolysis*).
2.  **`pathcoverage.tsv`**: The coverage of the pathway. (Just because one gene in a 10-gene pathway is highly expressed doesn't mean the pathway is active. Coverage checks if the *entire* pathway is present).
3.  **`genefamilies.tsv`**: The abundance of individual UniRef90 gene families.

### Stratification by Species

The brilliance of HUMAnN 3 is that the outputs are **stratified**. 

If you look at `pathabundance.tsv`, you won't just see "Glycolysis = 5000". You will see:
*   `Glycolysis` = 5000
*   `Glycolysis|Escherichia_coli` = 4000
*   `Glycolysis|Bacteroides_fragilis` = 1000

This allows you to confidently state not just *what* the community is doing, but exactly *which species* is responsible for doing it!

---

## 4. Normalizing the Data

Raw counts in metatranscriptomics are highly influenced by sequencing depth. Before doing statistical comparisons between a Healthy patient and a Sick patient, you must normalize the abundances to Copies Per Million (CPM).

```bash
# Normalize the pathway abundances
humann_renorm_table --input humann_out/sample_pathabundance.tsv \
                    --output sample_pathabundance_cpm.tsv \
                    --units cpm
```

With CPM-normalized tables across all your samples, you are ready to perform differential expression testing (e.g., using DESeq2) to find which metabolic pathways are uniquely activated in your disease state.
