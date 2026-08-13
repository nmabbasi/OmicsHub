---
title: "Advanced scRNA-seq Analysis: Metabolic Vulnerabilities and CLIC1"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Real Work Examples"
excerpt: "Learn how to use single-cell transcriptomics to identify metabolic dependencies in tumor subclones, with a specific focus on the role of CLIC1 in maintaining pH and redox balance in malignant T cells."
---

## Uncovering Metabolic Vulnerabilities in Single Cells

A major frontier in cancer biology is identifying the specific metabolic dependencies of malignant cells. Unlike normal cells, tumors often rewire their metabolism (e.g., the Warburg effect) to support rapid proliferation. Single-cell RNA-sequencing (scRNA-seq) allows us to identify these metabolic shifts at the subclonal level, revealing potential therapeutic targets that spare healthy tissue.

In this tutorial, we will focus on **CLIC1 (Chloride Intracellular Channel 1)**, a protein increasingly recognized for its role in pH regulation and redox balance in highly metabolic subclones of Cutaneous T-Cell Lymphoma (CTCL) and Sézary Syndrome.

---

## 1. Setting Up and Loading Data

We will use Scanpy to isolate malignant cells and evaluate their metabolic transcriptional networks.

```python
import scanpy as sc
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load our annotated dataset
adata = sc.read_h5ad('./data/ss_patient_annotated.h5ad')

# Isolate the malignant T-cell compartment for focused analysis
# Assuming 'cell_type' contains the annotation 'Malignant T'
tumor_cells = adata[adata.obs['cell_type'] == 'Malignant T'].copy()
```

---

## 2. Investigating CLIC1 Expression

CLIC1 expression is highly heterogeneous. Some subclones rely heavily on it to export chloride ions, which is coupled with proton export to prevent fatal intracellular acidification caused by high glycolytic rates.

```python
# Visualize CLIC1 expression across the malignant clusters (subclones)
sc.pl.violin(tumor_cells, 'CLIC1', groupby='leiden', 
             stripplot=False, inner='box')

# Map CLIC1 expression onto the UMAP
sc.pl.umap(tumor_cells, color=['leiden', 'CLIC1'], wspace=0.3)
```

If CLIC1 is highly expressed in a specific cluster (e.g., Cluster 2), this suggests that Cluster 2 represents a metabolically hyperactive subclone.

---

## 3. Creating a "Glycolytic / Redox" Module Score

To confirm that CLIC1 expression is actually tied to metabolic hyperactivity, we shouldn't look at CLIC1 in isolation. We need to evaluate whether the entire glycolytic and redox-management machinery is co-upregulated.

```python
# Define a metabolic gene signature
metabolic_signature = [
    'CLIC1',    # pH/redox balance
    'LDHA',     # Glycolysis (Lactate Dehydrogenase)
    'ENO1',     # Glycolysis (Enolase)
    'GAPDH',    # Glycolysis
    'SLC2A1',   # Glucose transporter (GLUT1)
    'SLC16A1',  # Lactate transporter (MCT1)
    'HIF1A'     # Hypoxia-inducible factor
]

# Ensure genes are in the dataset
valid_metabolic = [g for g in metabolic_signature if g in tumor_cells.var_names]

# Score the cells for this metabolic phenotype
sc.tl.score_genes(tumor_cells, gene_list=valid_metabolic, score_name='glycolytic_redox_score')

# Visualize the correlation between CLIC1 and the overall metabolic score
sc.pl.scatter(tumor_cells, x='CLIC1', y='glycolytic_redox_score', 
              color='leiden', title='CLIC1 vs. Metabolic Activity')
```

A strong positive correlation here provides computational evidence that CLIC1 is functioning as a critical release valve for highly metabolic, glycolytic subclones.

---

## 4. Differential Expression: Identifying Co-Dependencies

If we want to target the CLIC1-high subclone therapeutically, what other vulnerabilities does it have? We can perform differential expression (DE) comparing the CLIC1-high cells to the CLIC1-low cells.

```python
# Categorize cells into CLIC1-High and CLIC1-Low
# We use the 75th percentile as a cutoff for "High"
clic1_threshold = np.percentile(tumor_cells[:, 'CLIC1'].X.toarray(), 75)

tumor_cells.obs['CLIC1_status'] = 'Low'
tumor_cells.obs.loc[tumor_cells[:, 'CLIC1'].X.toarray().flatten() > clic1_threshold, 'CLIC1_status'] = 'High'

# Run DE analysis
sc.tl.rank_genes_groups(tumor_cells, groupby='CLIC1_status', 
                        groups=['High'], reference='Low', method='wilcoxon')

# Extract top upregulated genes in the CLIC1-High population
de_results = pd.DataFrame(tumor_cells.uns['rank_genes_groups']['names'])
top_genes_clic1_high = de_results['High'].head(20).tolist()

print("Top co-expressed genes with CLIC1:")
print(top_genes_clic1_high)
```

### Gene Set Enrichment Analysis (GSEA)

To understand the biological pathways driving these DE genes, we export the results for pathway analysis using `gseapy`.

```python
import gseapy as gp

# Extract the ranked list of genes (log fold changes)
ranked_genes = sc.get.rank_genes_groups_df(tumor_cells, group='High')
ranked_genes = ranked_genes[['names', 'logfoldchanges']].sort_values('logfoldchanges', ascending=False)

# Run GSEA against the KEGG pathways database
gsea_results = gp.prerank(rnk=ranked_genes, gene_sets='KEGG_2021_Human',
                          permutation_num=1000, outdir=None)

# Plot the top enriched pathways
terms = gsea_results.res2d.sort_values('NES', ascending=False).head(5)
gp.plot.barplot(terms, column="NES", title="Pathways Enriched in CLIC1-High Cells")
```

---

## Conclusion

By isolating specific sub-populations based on marker expression (`CLIC1`) and defining biological module scores, scRNA-seq allows us to reconstruct the metabolic landscape of a tumor. 

In the context of Sézary Syndrome, demonstrating that CLIC1-high cells exhibit distinct metabolic and redox dependencies provides the preclinical rationale for targeting CLIC1 to selectively induce apoptosis in the most aggressive tumor subclones, while sparing conventional, metabolically quiescent T cells.
