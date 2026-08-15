---
title: "Reference Genomes and Annotation Databases"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/reference-genomes-annotation.png"
excerpt: "Choose genome builds, transcript versions, identifiers, and reproducible annotation sources for analysis."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>A reference genome is not a neutral backdrop: its build, annotation release, transcript model, and identifiers directly affect alignment, quantification, variant calls, and biological interpretation. Record the exact references used.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Distinguish genome assemblies, annotation releases, transcript versions, and gene identifiers.
- Download reference files from stable authoritative sources.
- Verify checksums and record versions.
- Explain why mixing builds or annotations can invalidate results.

**Prerequisites:**

- Understand FASTA and GTF/GFF from [Biological Data Formats](biological-data-formats.html).
- Have `curl`, `wget`, and `sha256sum` available.

## 1. Build and annotation are different

GRCh38 is an assembly; a GENCODE release is an annotation set for that assembly. A transcript identifier may change between releases. Keep the FASTA and GTF compatible.

```text
assembly: GRCh38
annotation: GENCODE v46
source: https://www.gencodegenes.org/human/
downloaded: 2026-08-15
```

## 2. Download reproducibly

Prefer NCBI, Ensembl, GENCODE, or UCSC pages that document release versions. Save URLs, checksums, and commands in the project.

```bash
curl -L -o reference.fa.gz "https://ftp.ncbi.nlm.nih.gov/genomes/"
sha256sum reference.fa.gz > reference.fa.gz.sha256
```

## 3. Validate compatibility

Check chromosome names, feature IDs, coordinate conventions, and whether the annotation includes the feature type your tool expects. Do not mix `chr1` with `1` without a documented conversion.

```bash
cut -f1 reference.fa.fai | head
awk "$3=="gene" {print \$1}" annotation.gtf | sort -u | head
```

## 4. Identifier mapping

Gene symbols are human-friendly but unstable. Use stable Ensembl or NCBI identifiers in computational tables and retain the mapping table used to label figures.

```text
keep: stable_id, versioned_id, symbol, source_release
```

## Practical Exercise

Write a reference manifest listing assembly, annotation release, URLs, download date, checksum path, chromosome naming convention, and identifier type.

**Pass criteria:** A second learner could identify and re-download the exact compatible references from the manifest.

## Troubleshooting

If a tool reports missing contigs or features, compare assembly names, chromosome prefixes, and annotation release before editing files.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** A second learner could identify and re-download the exact compatible references from the manifest.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Data Visualization Fundamentals](data-visualization-fundamentals.html) and [Whole Exome Sequencing](wes-variant-calling-pipeline.html). Record the software versions, dataset or example inputs, and any decisions you made.
