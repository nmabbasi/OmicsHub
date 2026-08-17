---
title: "Biological Data Formats"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/biological-data-formats-workstation.webp"
excerpt: "Read FASTA, FASTQ, SAM/BAM, VCF, GTF/GFF, and count matrices with confidence before running analysis pipelines."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Bioinformatics tools exchange information through standardized files. A learner who can inspect a file, identify its assumptions, and validate its contents is much less likely to run the right command on the wrong input.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Recognize the purpose and basic structure of FASTA, FASTQ, BAM, VCF, GTF/GFF, and count matrices.
- Use shell commands to inspect headers, record counts, and delimiters.
- Distinguish reference sequences, reads, alignments, variants, annotations, and expression matrices.
- Identify metadata that must remain linked to samples.

**Prerequisites:**

- Complete [Computer and Data Fundamentals](computer-data-fundamentals.html).
- Know basic `pwd`, `ls`, `head`, `grep`, and pipe syntax.


### Expected Output

By the end of this lesson, you should have: **A small, validated set of FASTA, FASTQ, BAM/CRAM, VCF, GTF/GFF, and tabular-file examples with their purpose, structure, and safe inspection command recorded.**

## 1. Sequence and read files

FASTA stores named sequences as a header beginning with `>` followed by sequence lines. FASTQ stores a read name, sequence, a plus line, and one quality string for every record. A FASTQ record therefore has four lines, although wrapped sequence files require more careful parsing.

```bash
head -n 8 sample.fastq
grep -c "^@" sample.fastq
grep -c "^>" reference.fasta
```

## 2. Alignments and variants

SAM is text; BAM is its compressed binary equivalent. A BAM requires an index for many random-access operations. VCF stores variant records with a header, reference/alternate alleles, quality, filters, and sample genotype fields. Never interpret a VCF without checking the reference genome build.

```bash
samtools view -H aligned.bam | head
samtools quickcheck aligned.bam
bcftools view -h variants.vcf.gz | head
```

## 3. Annotation and expression tables

GTF/GFF files describe genomic features such as genes and transcripts. Count matrices usually have genes in rows, samples or cells in columns, and an identifier column. Confirm whether values are raw counts, normalized values, or transformed values before choosing a statistical method.

```bash
head -n 3 annotation.gtf
head -n 5 counts.tsv | cut -f1-5
```

## 4. Metadata is part of the experiment

A sample sheet should link every file to sample ID, donor, condition, batch, library type, and other pre-specified variables. Do not infer experimental groups from filenames alone.

```text
sample_id,fastq_r1,condition,batch,donor
S01,S01_R1.fastq.gz,control,1,D01
```

## Practical Exercise

Inspect one small FASTA, FASTQ, GTF, or count table. Record its format, number of records or rows, identifier field, compression state, and the metadata required to interpret it.

**Pass criteria:** You can identify the file type from its structure, report one validation command, and explain which reference build or sample metadata is required.

## Troubleshooting

If a count table appears shifted, inspect delimiters and quoted fields. If a BAM fails `samtools quickcheck`, re-download or regenerate it rather than continuing with corrupted data.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** You can identify the file type from its structure, report one validation command, and explain which reference build or sample metadata is required.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Quality Control Fundamentals](quality-control-fundamentals.html) and [Reference Genomes and Annotation Databases](reference-genomes-annotation.html). Record the software versions, dataset or example inputs, and any decisions you made.
