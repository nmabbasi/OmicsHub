---
title: "Cell-Cell Communication"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Advanced Single-Cell Analysis"
excerpt: "Learn how to infer cell-to-cell signaling networks from scRNA-seq data using state-of-the-art tools like LIANA and CellChat."
image: "images/cell-cell-communication.png"
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
    <li><strong>Prerequisites:</strong> Complete scRNA-seq Basics, cell-type annotation, and sample-aware differential-expression concepts.</li>
    <li><strong>Objective:</strong> Infer candidate ligand-receptor communication programs and separate computational scores from experimentally established cell signaling.</li>
    <li><strong>Expected Output:</strong> A ranked interaction table with sender/receiver labels, database version, sample context, and validation hypothesis.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Cell-Cell Communication Analysis

## Introduction

In multi-cellular organisms, cells do not exist in isolation. They constantly communicate through secreted ligands and membrane-bound receptors. Single-cell RNA-seq allows us to infer these communication networks by looking at the simultaneous expression of a ligand in one cell type and its cognate receptor in another cell type.

Two of the most powerful tools in R for inferring these networks are **LIANA** and **CellChat**.

---

## 1. LIANA (Ligand-Receptor Analysis Framework)

LIANA is incredibly powerful because it is not just one method—it is a wrapper that runs *multiple* cell-cell communication methods (like CellPhoneDB, NATMI, Connectome, and SingleCellSignalR) simultaneously and aggregates the results, giving you a consensus ranking of the most likely interactions.

### Running LIANA

```r
library(liana)
library(SCpubr)

# Run the LIANA wrapper on your Seurat or SingleCellExperiment object
liana_output <- liana_wrap(seurat_obj)

# Aggregate the results across all methods to get consensus rankings
liana_aggregate <- liana_aggregate(liana_output)

# Save the results
write.csv(liana_aggregate, "liana_aggregate_results.csv", row.names = FALSE)
```

### Visualizing LIANA Results

The `SCpubr` package works seamlessly with LIANA to create publication-ready plots.

```r
# Create a DotPlot of the top Ligand-Receptor interactions
p1 <- SCpubr::do_LigandReceptorPlot(liana_output = liana_output,
                                    top_interactions = 15)
p1
```

---

## 2. CellChat

While LIANA is great for getting a consensus list of interactions, **CellChat** shines at pathway-level analysis and visualizing the structural topology of the communication networks (e.g., Circle plots and Hierarchy plots).

### Running CellChat

```r
library(CellChat)

# 1. Create the CellChat object from Seurat
cellchat <- createCellChat(object = seurat_obj, group.by = "cell_type")

# 2. Set the database (e.g., Human or Mouse)
CellChatDB <- CellChatDB.human
cellchat@DB <- CellChatDB

# 3. Preprocess and infer communications
cellchat <- subsetData(cellchat)
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)
cellchat <- computeCommunProb(cellchat)
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)
```

### Visualizing CellChat Networks

```r
# Visualize the communication network as a Circle Plot
netVisual_circle(cellchat@net$count, vertex.weight = groupSize, weight.scale = T,
                 label.edge= F, title.name = "Number of interactions")
```

## Summary

*   Use **LIANA** when you want a highly robust, consensus-driven list of specific Ligand-Receptor pairs.
*   Use **CellChat** when you want to visualize pathway-level communication networks and create beautiful network topologies.

---

## 3. Interpretation, Limitations & Validation

### Interpretation Pitfalls
When interpreting LIANA or CellChat results, remember that these tools infer *potential* communication based on mRNA co-expression, **not** actual physical interaction.
*   **High probability != guaranteed interaction:** The ligand and receptor might be transcribed, but the proteins could be degraded, trapped in the Golgi, or blocked by competitive inhibitors.
*   **Spatial context is missing:** In standard scRNA-seq, a macrophage and a T-cell might show high communication probability, but in the actual tissue, they might be millimeters apart and unable to interact.

### Validation Strategies
Because scRNA-seq only provides a hypothesis, you **must** validate key findings experimentally:
1.  **Spatial Transcriptomics (e.g., Visium, Xenium):** Verify that the sender and receiver cells are physically co-localized in the tissue.
2.  **Multiplexed Immunofluorescence (mIF):** Use antibodies to confirm the presence of both the ligand and receptor proteins at the tissue level.
3.  **In Vitro Co-culture Assays:** Isolate the sender and receiver cells, co-culture them, and block the receptor using an antagonist to observe phenotypic changes.

### Software Requirements
*   **LIANA:** Tested on R 4.3.2. Requires Seurat v5 and `liana` (v0.1.12).
*   **CellChat:** Tested on R 4.3.2. Requires `CellChat` (v2.1.2) and `ComplexHeatmap`.

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why does coexpression of a ligand and receptor suggest a hypothesis rather than prove physical communication?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run or inspect one ligand-receptor analysis and report the sender, receiver, interaction database, score, and a proposed validation experiment. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a strong interaction appears only in one sample or broad cell type, how will you inspect cell abundance, expression thresholds, replicates, and spatial context?</p>
    </div>
  </div>
</div>
