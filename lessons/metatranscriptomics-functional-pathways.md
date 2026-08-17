---
title: "Functional Pathway Analysis with HUMAnN 3"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metatranscriptomics"
excerpt: "Dive deep into metatranscriptomics by mapping active RNA transcripts to complete metabolic pathways using HUMAnN 3 and the MetaCyc database."
image: "images/metatranscriptomics-functional-pathways.png"
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
    <li><strong>Prerequisites:</strong> Complete Metatranscriptomics Basics and be comfortable interpreting gene-family and pathway abundance tables.</li>
    <li><strong>Objective:</strong> Map microbial transcripts to functional gene families and pathways while separating observed activity from unsupported causal claims.</li>
    <li><strong>Expected Output:</strong> A pathway-level table with normalized abundance, database version, sample comparison, and stated uncertainty.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Functional Pathway Analysis in Metatranscriptomics

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


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why does a detected transcript support potential activity but not necessarily measured pathway flux or phenotype?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Interpret a HUMAnN-style pathway output and report one up- or down-shift with the normalization method and biological caveat. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a pathway disappears after filtering, how will you inspect read depth, reference coverage, normalization, and the gene-family evidence behind it?</p>
    </div>
  </div>
</div>
