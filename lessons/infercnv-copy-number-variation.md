---
title: "Inferring Copy Number Variation (inferCNV)"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to use inferCNV to detect large-scale chromosomal copy number alterations in single-cell RNA-seq data, essential for identifying malignant tumor cells."
image: "images/infercnv-copy-number-variation.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics and cell-type annotation; use matched reference cells and non-clinical training data where appropriate.</li>
    <li><strong>Objective:</strong> Infer broad copy-number patterns from expression while understanding reference selection, smoothing, and the need for orthogonal validation.</li>
    <li><strong>Expected Output:</strong> A CNV inference figure with reference-cell rationale, genomic patterns, sample context, and an explicit non-diagnostic interpretation.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Inferring Copy Number Variation with inferCNV

## Introduction

In oncology and cancer single-cell RNA-seq, distinguishing malignant tumor cells from normal, healthy cells in the microenvironment is the most critical first step. Because cancer is fundamentally driven by genomic instability, malignant cells often have massive chromosomal amplifications or deletions.

**inferCNV** is a powerful R package that uses single-cell RNA expression as a proxy for DNA copy number variation (CNV). By comparing the expression of genes across the genome in a suspect cell against a known "normal" reference cell, it can identify these large-scale chromosomal alterations.

---

## 1. Preparing Data for inferCNV

You need three inputs for inferCNV:
1. A raw count matrix.
2. A metadata file mapping each cell to its annotation (e.g., "Tumor", "Normal_T_cell", "Normal_B_cell").
3. A gene ordering file mapping each gene to its physical position on the chromosome.

```r
library(infercnv)

# Assuming you have extracted counts from your Seurat object
raw_counts <- GetAssayData(seurat_obj, slot = "counts")

# Create the inferCNV object
infercnv_obj <- CreateInfercnvObject(
  raw_counts_matrix = raw_counts,
  annotations_file = "cell_annotations.txt",
  delim = "\t",
  gene_order_file = "gene_ordering_hg38.txt",
  ref_group_names = c("Normal_T_cell", "Normal_B_cell") # Define the healthy reference!
)
```

---

## 2. Running the inferCNV Pipeline

inferCNV applies a series of smoothing steps, moving averages, and hidden Markov models (HMM) to denoise the RNA data and uncover the true DNA copy number signal.

```r
# Run the core inferCNV algorithm
infercnv_obj <- infercnv::run(
  infercnv_obj,
  cutoff = 0.1, # 0.1 for 10x Genomics, 1 for Smart-seq2
  out_dir = "infercnv_output/",
  cluster_by_groups = TRUE,
  denoise = TRUE,
  HMM = TRUE,
  num_threads = 8
)
```

### Key Considerations
*   **Cutoff:** Use `0.1` for sparse data like 10x Genomics, and `1.0` for full-length methods like Smart-seq2.
*   **Denoising:** Always use `denoise = TRUE` to remove background noise using the residual distributions.
*   **HMM:** The Hidden Markov Model predicts the actual integer copy number (e.g., 2 copies, 3 copies, or complete deletion).

---

## 3. Interpreting the Output

inferCNV automatically generates a heatmap in your output directory (`infercnv_output/infercnv.png`).

*   **Rows** are individual cells.
*   **Columns** are genes, ordered strictly by their physical location from Chromosome 1 to Chromosome X/Y.
*   **Colors:** Red indicates chromosomal amplification (e.g., Trisomy). Blue indicates chromosomal deletion.

If a cluster of cells shows massive, coordinated blocks of red and blue across entire chromosome arms, those cells are undoubtedly malignant. The reference cells (which you provided) will show a flat, neutral color, confirming they have a standard diploid genome.

This technique is the absolute gold standard for computationally validating malignant clusters before performing downstream differential expression.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is expression-derived CNV inference not a substitute for validated DNA-based copy-number measurement?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run or inspect an inferCNV output, identify the reference population, and report one broad pattern with its limitations. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a broad CNV signal appears in many cell types, how will you investigate reference quality, normalization, cell-cycle effects, and technical artifacts?</p>
    </div>
  </div>
</div>
