---
title: "Advanced scRNA-seq Analysis: Transcriptional Heterogeneity and the Four-State Model"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Single-cell RNA-seq"
excerpt: "Learn how to investigate intra-tumoral heterogeneity and plasticity using single-cell RNA-seq, focusing on regulatory T cell phenotypes (FOXP3) and the Four-State Model in Cutaneous T-Cell Lymphoma."
---

## Understanding Transcriptional Plasticity in Malignancies

Traditional paradigms often view tumors as homogeneous masses. However, single-cell transcriptomics (scRNA-seq) has revealed profound **transcriptional heterogeneity** and **plasticity** within malignant populations. 

In this tutorial, we will explore advanced scRNA-seq techniques used to dissect this heterogeneity, using **Sézary Syndrome (SS)**—a leukemic variant of Cutaneous T-Cell Lymphoma (CTCL)—as our biological framework.

---

## The Biological Context: Sézary Syndrome

Recent literature (e.g., Borcherding et al., 2019; Childs et al., 2026) has demonstrated that SS cells do not exist in a single static state. Instead, they exhibit significant transcriptional plasticity, which can be conceptualized using a **"Four-State" Model**:

1. **Stem-like state**: High expression of progenitor and renewal markers.
2. **Metabolic state**: Upregulation of metabolic enzymes and transporters (e.g., CLIC1).
3. **Interferon-stimulated state**: Inflammatory signaling response.
4. **Exhausted/Regulatory state**: Expression of markers like FOXP3 and PD-1.

A major point of debate in the field revolves around the regulatory state: Do FOXP3-expressing malignant cells possess true suppressive regulatory function? While Heid and Klemke et al. (2009) identified functional FOXP3+CD25- cells, Wada et al. (2013) showed that classic CD4+CD25+FOXP3+ tumor cells often lack suppressive activity.

We will use Scanpy to identify these distinct states and isolate the controversial FOXP3+ subsets for downstream analysis.

---

## 1. Setting Up the Analysis Environment

We assume you have already performed standard QC, normalization, and clustering (as covered in our [End-to-End scRNA-seq guide](real-world-scrna-seq-scanpy.md)).

```python
import scanpy as sc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load pre-processed data (e.g., a clustered SS patient sample)
adata = sc.read_h5ad('./data/ss_patient_clustered.h5ad')
```

---

## 2. Defining the Four-State Signatures

To identify the four states, we can calculate **module scores** (also known as signature scores) for each cell. This is more robust than relying on single genes.

```python
# Define gene signatures based on literature (Borcherding, Childs, etc.)
signatures = {
    'stem_like': ['TCF7', 'LEF1', 'SELL', 'IL7R'],
    'metabolic': ['CLIC1', 'LDHA', 'ENO1', 'GAPDH', 'SLC2A1'],
    'interferon': ['ISG15', 'IFIT1', 'IFIT3', 'STAT1', 'OAS1'],
    'regulatory': ['FOXP3', 'IL2RA', 'CTLA4', 'TIGIT', 'PDCD1'] # IL2RA is CD25
}

# Calculate a score for each signature
for state, genes in signatures.items():
    # Only use genes present in our dataset
    valid_genes = [g for g in genes if g in adata.var_names]
    
    # Calculate score (adds column to adata.obs)
    sc.tl.score_genes(adata, gene_list=valid_genes, score_name=f'{state}_score')

# Visualize the distribution of these states across the UMAP
sc.pl.umap(adata, color=['stem_like_score', 'metabolic_score', 
                         'interferon_score', 'regulatory_score'], 
           cmap='viridis', vmin=0, vmax='p99')
```

---

## 3. Isolating and Analyzing the FOXP3+ Subpopulation

Given the debate surrounding the functional relevance of FOXP3 in Sézary Syndrome, we need to specifically isolate the cells expressing both FOXP3 and CD25 (IL2RA).

```python
# Ensure we are looking at the normalized/log-transformed data
adata.X = adata.raw.X if adata.raw is not None else adata.X

# Create boolean masks for expression
# We define "expressed" as having a log-normalized count > 0
foxp3_expr = adata[:, 'FOXP3'].X > 0
cd25_expr = adata[:, 'IL2RA'].X > 0

# Convert sparse matrix outputs to dense 1D arrays if necessary
if not isinstance(foxp3_expr, np.ndarray):
    foxp3_expr = foxp3_expr.toarray().flatten()
    cd25_expr = cd25_expr.toarray().flatten()

# Annotate cells based on the Wada (2013) and Heid (2009) phenotypes
conditions = [
    (foxp3_expr & cd25_expr),              # Classic Treg phenotype (Wada)
    (foxp3_expr & ~cd25_expr),             # FOXP3+CD25- phenotype (Heid/Klemke)
    (~foxp3_expr & cd25_expr),             # Activated non-Treg
    (~foxp3_expr & ~cd25_expr)             # Double negative
]
choices = ['FOXP3+CD25+', 'FOXP3+CD25-', 'FOXP3-CD25+', 'FOXP3-CD25-']

adata.obs['treg_phenotype'] = np.select(conditions, choices, default='Unknown')

# Visualize where these specific phenotypes fall on the UMAP
sc.pl.umap(adata, color='treg_phenotype', 
           palette={'FOXP3+CD25+': 'red', 'FOXP3+CD25-': 'orange', 
                    'FOXP3-CD25+': 'blue', 'FOXP3-CD25-': 'lightgrey'})
```

### Differential Expression: FOXP3+ vs FOXP3-

To infer whether these FOXP3+ cells possess actual regulatory capacity (as debated in the literature), we can look for the co-expression of functional suppressive molecules (e.g., IL-10, TGFB1, ENTPD1/CD39).

```python
# Sub-cluster to compare only within the malignant T cell compartment
# Assuming cluster '0' and '1' represent the malignant clone
malignant_adata = adata[adata.obs['leiden'].isin(['0', '1'])].copy()

# Perform differential expression between FOXP3 phenotypes
sc.tl.rank_genes_groups(malignant_adata, groupby='treg_phenotype', 
                        groups=['FOXP3+CD25+', 'FOXP3+CD25-'], 
                        reference='FOXP3-CD25-', method='wilcoxon')

# Plot functional regulatory markers
functional_markers = ['IL10', 'TGFB1', 'ENTPD1', 'LAG3']
sc.pl.dotplot(malignant_adata, functional_markers, groupby='treg_phenotype')
```

---

## 4. Modeling Transcriptional Plasticity (RNA Velocity)

If the "Four-State" model represents plasticity rather than fixed sub-clones, cells should dynamically transition between these states. We can infer these transitions using **RNA Velocity** (via `scVelo`), which estimates future cell states by comparing spliced vs. unspliced mRNA transcripts.

```python
import scvelo as scv

# Requires BAM files processed through velocyto or kallisto/bustools to generate spliced/unspliced matrices
# Assuming adata already contains 'spliced' and 'unspliced' layers
scv.pp.filter_and_normalize(adata, min_shared_counts=20, n_top_genes=2000)
scv.pp.moments(adata, n_pcs=30, n_neighbors=30)

# Estimate velocity
scv.tl.velocity(adata)
scv.tl.velocity_graph(adata)

# Project velocity streams over our Four-State module scores
scv.pl.velocity_embedding_stream(adata, basis='umap', color='regulatory_score')
```

If the velocity arrows flow from the `stem_like` state toward the `regulatory` or `metabolic` states, it provides strong computational evidence for dynamic plasticity within the tumor microenvironment, supporting recent findings by Borcherding et al.

## Conclusion

By leveraging module scoring and boolean gating in single-cell data, we can test complex biological hypotheses—such as resolving the phenotypic debate around FOXP3+ Sézary cells. Understanding this transcriptional heterogeneity is the first step toward identifying metabolic vulnerabilities and targeting resistant subclones.
