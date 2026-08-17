---
title: "Quality Control Fundamentals"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/quality-control-fundamentals-workstation.webp"
excerpt: "Understand read quality, mapping, duplication, contamination, missing data, and QC decisions across omics workflows."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Quality control is not a decorative report added at the end of an analysis. It is the evidence used to decide whether data can support the biological question. This lesson introduces common QC measurements and how to act on them without applying arbitrary thresholds.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Explain read quality, mapping rate, duplication, coverage, contamination, and missingness.
- Separate technical failure from a genuine biological signal.
- Choose QC plots and thresholds appropriate to the assay.
- Document exclusions and retain the original data.

**Prerequisites:**

- Complete [Biological Data Formats](biological-data-formats.html).
- Understand that thresholds depend on protocol, organism, platform, and study design.


### Expected Output

By the end of this lesson, you should have: **A QC summary that records the tool and version, key quality metrics, a pass-or-review decision, and the next action for the data.**

## 1. Read-level QC

For short reads, inspect per-base quality, adapter content, sequence length, GC distribution, overrepresented sequences, and duplication. A low-quality tail may be trimmed, but trimming should be justified and recorded.

```bash
fastqc sample_R1.fastq.gz sample_R2.fastq.gz
multiqc .
```

## 2. Alignment and coverage QC

Mapping rate, properly paired reads, insert size, coverage depth, duplicate fraction, and target enrichment describe different failure modes. A high mapping rate does not guarantee correct alignment if the reference is wrong or contamination is present.

```bash
samtools flagstat aligned.bam
samtools idxstats aligned.bam | head
samtools depth -a aligned.bam | awk "{sum+=\$3} END {print sum/NR}"
```

## 3. Single-cell QC

For scRNA-seq, inspect genes per cell, counts per cell, mitochondrial proportion, ribosomal content, doublets, and cell-cycle or stress signals. Thresholds should be explored by tissue and protocol, not copied blindly from another dataset.

<div class="code-tabs" data-code-tabs>
  <div class="code-tab-list" role="tablist" aria-label="Single-cell QC code examples">
    <button id="qc-python-tab" class="code-tab-button is-active" type="button" role="tab" aria-selected="true" aria-controls="qc-python-panel">Python · Scanpy</button>
    <button id="qc-r-tab" class="code-tab-button" type="button" role="tab" aria-selected="false" aria-controls="qc-r-panel" tabindex="-1">R · Seurat</button>
  </div>

  <div id="qc-python-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="qc-python-tab">
    <pre><code class="language-python"># Inspect the distribution of core QC metrics
qc_columns = ["n_genes_by_counts", "total_counts", "pct_counts_mt"]
print(adata.obs[qc_columns].describe())

# Visualize distributions and metric relationships before choosing thresholds
sc.pl.violin(adata, ["n_genes_by_counts", "total_counts", "pct_counts_mt"], jitter=0.25, multi_panel=True)
sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt")
</code></pre>
    <p class="code-tab-note">Use the metric names created by your own preprocessing workflow. In Scanpy, mitochondrial percentage is commonly stored as <code>pct_counts_mt</code>.</p>
  </div>

  <div id="qc-r-panel" class="code-tab-panel" role="tabpanel" aria-labelledby="qc-r-tab" hidden>
    <pre><code class="language-r">library(Seurat)

# Add QC percentages; use ^mt- for many mouse annotations
seurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = "^MT-")
seurat_obj[["percent.rb"]] <- PercentageFeatureSet(seurat_obj, pattern = "^RP[SL]")

# Inspect distributions before defining any filtering rule
VlnPlot(seurat_obj,
        features = c("nFeature_RNA", "nCount_RNA", "percent.mt", "percent.rb"),
        ncol = 4, pt.size = 0.1)
FeatureScatter(seurat_obj, feature1 = "nCount_RNA", feature2 = "percent.mt")
</code></pre>
    <p class="code-tab-note">Match the gene-pattern regular expression to the organism and annotation used in your dataset; QC variables should be inspected before setting thresholds.</p>
  </div>
</div>

<figure class="lesson-figure">
  <img src="images/tutorial-figures/qc-metrics-distribution.webp" alt="Four high-resolution single-cell QC distribution panels showing detected genes, RNA counts, mitochondrial percentage, and ribosomal percentage." loading="lazy" width="1920" height="930">
  <figcaption>
    <strong>Figure: Read QC distributions before choosing thresholds.</strong> This illustrative multi-batch panel shows detected genes, RNA counts, mitochondrial fraction, and ribosomal fraction. Look for unusually low-complexity groups, long high-count tails that can indicate doublets, and shifts that may reflect biology, chemistry, or library quality. The figure supports exploration; it does not justify one universal cutoff.
    <span class="figure-source">Author-provided, non-clinical teaching figure. Original source-group identifiers have been removed; the panel is used solely to illustrate QC-metric interpretation.</span>
  </figcaption>
</figure>

## 4. Record decisions

Create a QC report that states the metric, threshold, number removed, reason, and whether the decision was made before examining the biological outcome.

```text
metric,threshold,removed,reason
pct_counts_mt,<20,143,high mitochondrial content
```

## Practical Exercise

Choose one assay and create a one-page QC decision table with metric, plot, threshold rationale, records removed, and possible biological bias.

**Pass criteria:** You can explain at least four QC metrics, state why each matters, and document an exclusion without claiming that one universal threshold is correct.

## Troubleshooting

If a sample fails every metric, do not rescue it by repeatedly changing cutoffs. Check sample identity, library preparation, contamination, sequencing depth, and batch before deciding.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** You can explain at least four QC metrics, state why each matters, and document an exclusion without claiming that one universal threshold is correct.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Statistics for Bioinformatics](statistics-for-bioinformatics.html) and [scRNA-seq Basics](scrna-seq-basics.html). Record the software versions, dataset or example inputs, and any decisions you made.
