---
title: "Advanced scRNA-seq Analysis: Transcriptional Heterogeneity and Plasticity"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Single-cell RNA-seq"
excerpt: "Learn how to investigate cellular heterogeneity and plasticity using single-cell RNA-seq, focusing on defining complex cell states via module scoring and inferring transitions with RNA Velocity."
---

## Understanding Transcriptional Plasticity

In traditional biology, cell populations are often viewed as consisting of discrete, static cell types. However, single-cell transcriptomics (scRNA-seq) has revealed profound **transcriptional heterogeneity** and **plasticity** within seemingly uniform populations. Cells frequently transition between various functional states in response to their microenvironment.

In this tutorial, we will explore advanced scRNA-seq techniques used to dissect this heterogeneity. We will define complex cellular states using signature scoring and track how cells move between these states.

---

## 1. Setting Up the Analysis Environment

We assume you have already performed standard QC, normalization, and clustering (as covered in our introductory scRNA-seq guides).

```python
import scanpy as sc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load pre-processed data (e.g., a complex tissue sample)
adata = sc.read_h5ad('./data/complex_tissue_clustered.h5ad')
```

---

## 2. Defining Transcriptional States via Module Scoring

Rather than relying on single marker genes, which are subject to technical dropout in scRNA-seq, we can identify complex cell states by calculating **module scores** (or signature scores) using known biological pathways.

Consider a population that can exist in several distinct phenotypic states:
1. **Proliferative/Stem-like**: Actively dividing or maintaining progenitor status.
2. **Inflammatory**: Responding to local cytokine signaling.
3. **Exhausted/Regulatory**: Exhibiting regulatory markers due to chronic stimulation.

```python
# Define generic gene signatures for different functional states
signatures = {
    'proliferative': ['MKI67', 'TOP2A', 'PCNA', 'CDK1'],
    'inflammatory': ['ISG15', 'IFIT1', 'STAT1', 'CXCL10'],
    'regulatory': ['IL2RA', 'CTLA4', 'TIGIT', 'PDCD1', 'LAG3']
}

# Calculate a score for each signature
for state, genes in signatures.items():
    # Only use genes present in our dataset
    valid_genes = [g for g in genes if g in adata.var_names]
    
    # Calculate score (adds a new column to adata.obs)
    sc.tl.score_genes(adata, gene_list=valid_genes, score_name=f'{state}_score')

# Visualize the distribution of these states across the UMAP
sc.pl.umap(adata, color=['proliferative_score', 'inflammatory_score', 'regulatory_score'], 
           cmap='viridis', vmin=0, vmax='p99')
```

---

## 3. Boolean Gating for Specific Phenotypes

Sometimes we need to ask binary questions about our data. For instance, in immunology, the co-expression of specific surface receptors often defines a unique functional phenotype. We can use boolean logic on the expression matrices to isolate these cells.

```python
# Ensure we are looking at the normalized/log-transformed data
adata.X = adata.raw.X if adata.raw is not None else adata.X

# Create boolean masks for expression of two hypothetical markers (Marker A and Marker B)
# We define "expressed" as having a log-normalized count > 0
marker_a_expr = adata[:, 'MARKERA'].X > 0
marker_b_expr = adata[:, 'MARKERB'].X > 0

# Convert sparse matrix outputs to dense 1D arrays if necessary
if not isinstance(marker_a_expr, np.ndarray):
    marker_a_expr = marker_a_expr.toarray().flatten()
    marker_b_expr = marker_b_expr.toarray().flatten()

# Annotate cells based on their combinatorial phenotype
conditions = [
    (marker_a_expr & marker_b_expr),              # Double positive
    (marker_a_expr & ~marker_b_expr),             # Marker A single positive
    (~marker_a_expr & marker_b_expr),             # Marker B single positive
    (~marker_a_expr & ~marker_b_expr)             # Double negative
]
choices = ['Double+', 'MarkerA_Only', 'MarkerB_Only', 'Double-']

adata.obs['phenotype_gate'] = np.select(conditions, choices, default='Unknown')

# Visualize where these specific phenotypes fall on the UMAP
sc.pl.umap(adata, color='phenotype_gate')
```

Once isolated, you can perform standard differential expression testing (`sc.tl.rank_genes_groups`) specifically between the `Double+` and `MarkerA_Only` populations to uncover the functional consequences of acquiring Marker B.

---

## 4. Modeling Transcriptional Plasticity (RNA Velocity)

If a population is highly plastic, cells should be actively transitioning between these states. We can infer these transitions using **RNA Velocity** (via `scVelo`), which estimates future cell states by comparing the ratio of spliced (mature) to unspliced (nascent) mRNA transcripts.

```python
import scvelo as scv

# Requires BAM files processed through velocyto or kallisto/bustools 
# Assuming adata already contains 'spliced' and 'unspliced' layers
scv.pp.filter_and_normalize(adata, min_shared_counts=20, n_top_genes=2000)
scv.pp.moments(adata, n_pcs=30, n_neighbors=30)

# Estimate velocity
scv.tl.velocity(adata)
scv.tl.velocity_graph(adata)

# Project velocity streams over our module scores
scv.pl.velocity_embedding_stream(adata, basis='umap', color='proliferative_score')
```

If the velocity arrows flow consistently from the `proliferative` state toward the `regulatory` state, it provides strong computational evidence for dynamic plasticity and cellular differentiation within the microenvironment, moving beyond the concept of static clusters.

## Conclusion

By leveraging module scoring and boolean gating in single-cell data, we can test complex biological hypotheses regarding phenotypic states. Combining these static snapshots with dynamic trajectory mapping (like RNA Velocity) allows researchers to reconstruct a continuous map of cellular heterogeneity and plasticity.
