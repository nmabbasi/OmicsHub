---
title: "Phylogenomics with OrthoFinder"
date: "2026-08-14"
author: "OmicsHub Team"
category: "Evolutionary Bioinformatics Analysis"
excerpt: "Scale up from single-gene phylogeny to whole-genome phylogenomics by identifying orthogroups and constructing species trees using OrthoFinder."
image: "images/bioinformatics-intro.png"
---

# Phylogenomics and Orthology Analysis

## Introduction

Traditional phylogenetic analysis relies on aligning a single highly conserved gene (like 16S rRNA or Cytochrome C) to determine the evolutionary relationship between species. However, single genes can be misleading due to horizontal gene transfer or differing mutation rates.

**Phylogenomics** solves this by using *entire genomes*. Instead of one gene, we look at thousands of genes simultaneously. The absolute industry standard tool for identifying which genes are comparable across different genomes is **OrthoFinder**.

---

## 1. The Concept of Orthology

To compare genomes, you must first find the matching genes across them. 
*   **Orthologs** are genes in different species that evolved from a common ancestral gene via speciation. These are the genes you *want* to use to build a species tree.
*   **Paralogs** are genes related via duplication events within a genome. Comparing paralogs across species will give you an incorrect evolutionary tree.

OrthoFinder automatically sorts the proteomes (all protein sequences) of your species into **Orthogroups**, strictly separating orthologs from paralogs.

---

## 2. Running OrthoFinder

OrthoFinder is incredibly easy to run. You simply provide it a directory containing the `.faa` (Protein FASTA) files of the species you want to compare.

*(Note: You can easily generate these `.faa` files by running PROKKA on your assembled genomes).*

```bash
# Assuming you have a folder named 'proteomes' containing fasta files:
# speciesA.faa, speciesB.faa, speciesC.faa

# Run OrthoFinder using 16 threads
orthofinder -f proteomes/ -t 16 -a 16
```

Under the hood, OrthoFinder runs an all-versus-all DIAMOND blast search, calculates sequence similarities, clusters the genes into orthogroups using MCL, and infers unrooted gene trees.

---

## 3. Key Outputs from OrthoFinder

OrthoFinder creates a highly structured `Results/` directory. The most critical outputs are:

### `Orthogroups.tsv`
This is a matrix where each row is an orthogroup, and columns are your species. It shows exactly which genes belong to which orthogroup.

### `Single_Copy_Orthologue_Sequences/`
This directory contains the absolute gold-mine for phylogenomics. A "Single-Copy Ortholog" is a gene that exists exactly once in every single species you analyzed. These are the perfect genes for building a highly robust phylogenetic tree, as there is zero ambiguity about paralogs.

### `Species_Tree/SpeciesTree_rooted.txt`
OrthoFinder automatically concatenates the alignments of those single-copy orthologs and uses STAG and STRIDE algorithms to infer a highly accurate, rooted **Species Tree** in Newick format.

You can instantly visualize this file using tools like **iTOL** (Interactive Tree Of Life) or FigTree.

## Conclusion

OrthoFinder represents a massive leap forward from single-gene phylogeny. By leveraging the entire proteome to accurately identify orthogroups and automatically inferring a rooted species tree, you can resolve deep evolutionary relationships with unprecedented statistical confidence.
