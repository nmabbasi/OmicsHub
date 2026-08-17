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

```python
adata.obs["n_genes_by_counts"].describe()
adata.obs["pct_counts_mt"].describe()
```

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
