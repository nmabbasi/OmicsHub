---
title: "Evolutionary Phylogeny"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Evolutionary and Comparative Genomics"
excerpt: "A comprehensive guide to evolutionary analysis, covering multiple sequence alignment with Kalign, tree construction, and using MEGA via the command line."
image: "images/evolutionary-phylogeny.png"
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
    <li><strong>Prerequisites:</strong> Complete Biological Data Formats and understand sequences, multiple sequence alignment, and homologous characters.</li>
    <li><strong>Objective:</strong> Build and interpret a phylogenetic tree while distinguishing tree topology, support, rooting, and evolutionary inference.</li>
    <li><strong>Expected Output:</strong> A reproducible tree-analysis record containing aligned input, model or method, root choice, support values, and figure caption.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Evolutionary Bioinformatics Analysis

## Introduction to Evolutionary Bioinformatics

Evolutionary bioinformatics applies computational methods to understand the evolutionary relationships between biological sequences (DNA, RNA, or proteins). By analyzing these relationships, we can infer common ancestry, trace the history of gene families, and understand functional conservation.

Two of the most fundamental steps in evolutionary analysis are **Multiple Sequence Alignment (MSA)** and **Phylogeny (Tree Construction)**.

---

## 1. Multiple Sequence Alignment using Kalign

Before building an evolutionary tree, homologous sequences must be aligned to identify conserved regions and mutations. While tools like Clustal Omega and MAFFT are popular, **Kalign** is highly efficient for aligning massive datasets rapidly.

### Installing Kalign

Kalign is available via Conda/Mamba in the bioconda channel:

```bash
# Create a dedicated environment
mamba create -n phylogeny_env kalign
conda activate phylogeny_env
```

### Running Kalign

To perform a multiple sequence alignment on a FASTA file containing unaligned sequences:

```bash
# Basic alignment
kalign -i unaligned_sequences.fasta -o aligned_sequences.fasta

# Specify output format (e.g., Clustal format instead of FASTA)
kalign -i unaligned_sequences.fasta -f clu -o aligned_sequences.aln
```

Kalign uses the Wu-Manber string-matching algorithm, making it exceptionally fast for large-scale phylogenomics projects where thousands of sequences are involved.

---

## 2. Phylogenetic Tree Construction

Once sequences are aligned, the next step is calculating the evolutionary distance and constructing a phylogenetic tree. There are several methods for tree construction:
*   **Distance-based:** Neighbor-Joining (NJ), UPGMA
*   **Character-based:** Maximum Parsimony (MP), Maximum Likelihood (ML)
*   **Bayesian Inference:** (e.g., MrBayes)

### Using MEGA via Command Line (MEGA-CC)

**Molecular Evolutionary Genetics Analysis (MEGA)** is an industry standard for phylogeny. While famous for its graphical interface, MEGA also provides a command-line version called **MEGA-CC** (MEGA Computational Core), which is perfect for HPC environments or automated pipelines.

### Generating a Configuration (.mao) File

MEGA-CC requires an analysis options file (`.mao`). You may create it in the MEGA GUI, but do not treat a GUI selection as the complete record of an analysis. Save the exact `.mao` file beside the alignment, record the MEGA-CC version, and commit both settings and command to the project repository.

For an auditable exercise, create a project folder containing:

```text
phylogeny-project/
├── aligned_sequences.fasta
├── ML_Tree_Settings.mao
├── command.txt
└── results/
```

Write the exact `megacc` command into `command.txt`. If a learner cannot produce or inspect a `.mao` file, use the fully command-line IQ-TREE route below instead; it exposes model selection and bootstrap settings directly in the command.

### Running MEGA-CC

Once you have your alignment file and your `.mao` configuration file, you can run the analysis on the command line:

```bash
# Run MEGA-CC for Maximum Likelihood tree construction
megacc -a ML_Tree_Settings.mao -d aligned_sequences.fasta -o output_tree
```

This will output several files, including the tree in Newick format (`output_tree.nwk`), which can be visualized using tools like FigTree or iTOL (Interactive Tree Of Life).

---

## 3. Alternative Command Line Phylogeny Tools

While MEGA is excellent, other highly optimized command-line tools are heavily used in modern bioinformatics:

### IQ-TREE (Maximum Likelihood)

IQ-TREE is renowned for its speed and its "ModelFinder" feature, which automatically determines the best-fitting evolutionary model for your data before building the tree.

```bash
mamba install -c bioconda iqtree

# Run IQ-TREE with automatic model selection and 1000 ultrafast bootstraps
iqtree -s aligned_sequences.fasta -m MFP -B 1000
```

### FastTree (Approximate Maximum Likelihood)

For massive alignments (e.g., tens of thousands of sequences), FastTree is often the only feasible option.

```bash
mamba install -c bioconda fasttree

# Build a tree using the General Time Reversible (GTR) model
FastTree -gtr -nt < aligned_sequences.fasta > output.tree
```

---

## Summary Workflow

1.  **Gather Sequences:** Download homologous FASTA sequences.
2.  **Align:** Use `kalign` to generate a robust multiple sequence alignment.
3.  **Build Tree:** Use `megacc` or `iqtree` to compute evolutionary distances and infer the tree topology.
4.  **Visualize:** Upload the resulting `.nwk` file to iTOL for publication-ready visualization.



### Matched Python and R tree-inspection workflow

Use code to inspect and plot an already inferred Newick tree; it does not substitute for model selection, alignment review, or branch-support assessment during inference.

```python
from Bio import Phylo

species_tree = Phylo.read("species_tree.nwk", "newick")
print({"tips": species_tree.count_terminals(), "total_branch_length": species_tree.total_branch_length()})
Phylo.draw(species_tree)
```
```r
library(ape)

species_tree <- read.tree("species_tree.nwk")
print(list(tips = Ntip(species_tree), total_branch_length = sum(species_tree$edge.length)))
plot(species_tree, cex = 0.7)
```

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">What does a branch pattern represent, and what cannot be inferred from branch placement without an explicit root and support assessment?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Generate or inspect a tree from a provided alignment, identify sister groups and support values, and write a cautious interpretation. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a tree changes after alignment trimming or rooting, what methodological choices should be reported before making evolutionary claims?</p>
    </div>
  </div>
</div>
