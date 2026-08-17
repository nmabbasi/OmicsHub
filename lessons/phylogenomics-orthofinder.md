---
title: "Phylogenomics with OrthoFinder"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Evolutionary Bioinformatics Analysis"
excerpt: "Scale up from single-gene phylogeny to whole-genome phylogenomics by identifying orthogroups and constructing species trees using OrthoFinder."
image: "images/phylogenomics-orthofinder.png"
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
    <li><strong>Prerequisites:</strong> Complete Evolutionary Phylogeny and have predicted protein sets with consistent species and gene naming.</li>
    <li><strong>Objective:</strong> Use orthogroups and comparative genomics outputs to distinguish orthology, paralogy, gene-family change, and species-tree inference.</li>
    <li><strong>Expected Output:</strong> An annotated orthogroup summary that records input proteomes, software version, species set, and one cautiously interpreted result.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Phylogenomics and Orthology Analysis

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



### Matched Python and R OrthoFinder species-tree workflow

The species tree is an OrthoFinder output. Inspect its topology and branch lengths after checking the orthogroup and single-copy-orthologue settings used to infer it.

```python
from Bio import Phylo

species_tree = Phylo.read("Results_Example/Species_Tree/SpeciesTree_rooted.txt", "newick")
print(species_tree.get_terminals())
Phylo.draw(species_tree)
```
```r
library(ape)

species_tree <- read.tree("Results_Example/Species_Tree/SpeciesTree_rooted.txt")
print(species_tree$tip.label)
plot(species_tree, cex = 0.7)
```

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is an orthogroup not automatically a one-to-one ortholog set?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run or inspect an OrthoFinder output and identify an orthogroup, a potential duplication event, and the evidence used for interpretation. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a gene family appears expanded, how will you check assembly completeness, annotation consistency, gene models, and sampling before claiming adaptation?</p>
    </div>
  </div>
</div>
