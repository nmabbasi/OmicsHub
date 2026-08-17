---
title: "Whole Exome Sequencing (WES): Variant Calling & VAF"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Genomics & Whole Exome Sequencing"
excerpt: "A comprehensive guide to Whole Exome Sequencing (WES) analysis, covering read alignment, variant calling, LiftOver, and Variant Allele Frequency (VAF) calculations."
image: "images/wes-variant-calling.png"
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
    <li><strong>Prerequisites:</strong> Complete Biological Data Formats, Reference Genomes, and basic command-line concepts; use controlled, non-clinical training data.</li>
    <li><strong>Objective:</strong> Trace a whole-exome variant-calling workflow from aligned reads to filtered variants while interpreting depth, genotype quality, and VAF responsibly.</li>
    <li><strong>Expected Output:</strong> A documented VCF review with reference build, filters, depth, genotype quality, VAF, and explicit non-clinical interpretation limits.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Whole Exome Sequencing (WES) Pipeline

## Introduction

While RNA sequencing (RNA-seq) tells us what genes are actively expressed, **Whole Exome Sequencing (WES)** reveals the underlying DNA mutations. WES specifically targets the protein-coding regions of the genome, making it a highly cost-effective method for identifying disease-causing variants in cancer and rare genetic disorders.

This tutorial covers the standard bioinformatics pipeline for processing raw WES data, calculating Variant Allele Frequency (VAF), and managing genome assembly liftovers.

---

## 1. Raw Data Processing & Alignment

The first step in any DNA-seq pipeline is aligning the raw FASTQ reads to a reference genome (e.g., GRCh38/hg38) and marking PCR duplicates.

### BWA-MEM Alignment
`BWA-MEM` is the gold standard for aligning DNA reads to a reference genome.

```bash
# Index the reference genome (only needed once)
bwa index Homo_sapiens_assembly38.fasta

# Align paired-end reads to the reference
bwa mem -t 8 Homo_sapiens_assembly38.fasta sample_R1.fastq.gz sample_R2.fastq.gz > aligned_reads.sam
```

### Sorting and Marking Duplicates (GATK / Picard)
We use `samtools` to convert to BAM, and `Picard` to remove PCR duplicates that arise during exome capture library preparation.

```bash
# Convert SAM to BAM and sort by coordinate
samtools sort -@ 8 -o sorted_reads.bam aligned_reads.sam

# Mark Duplicates
java -jar picard.jar MarkDuplicates \
      I=sorted_reads.bam \
      O=dedup_reads.bam \
      M=marked_dup_metrics.txt
```

---

## 2. Variant Calling (GATK HaplotypeCaller)

Once the reads are aligned and deduplicated, we use the Broad Institute's **GATK (Genome Analysis Toolkit)** to identify SNPs (Single Nucleotide Polymorphisms) and Indels.

```bash
# Call variants using HaplotypeCaller
gatk HaplotypeCaller \
     -R Homo_sapiens_assembly38.fasta \
     -I dedup_reads.bam \
     -O raw_variants.vcf.gz
```

---

## 3. Variant Allele Frequency (VAF) Analysis

**Variant Allele Frequency (VAF)** is the percentage of sequencing reads matching a specific DNA variant divided by the total coverage at that locus. In cancer genomics, VAF is critical for determining whether a mutation is clonal (present in all tumor cells) or subclonal.

### Calculating VAF in R

If you extract the allelic depths (AD) and total depth (DP) from your VCF into a data frame, you can analyze VAF in R:

```r
library(ggplot2)
library(dplyr)

# Example: Read extracted VCF data
variant_data <- read.csv("extracted_variants.csv")

# Calculate VAF: Alternate Allele Depth (AD_alt) / Total Depth (DP)
variant_data <- variant_data %>%
  mutate(VAF = AD_alt / DP)

# Visualize the VAF distribution to look for clonal peaks
ggplot(variant_data, aes(x = VAF)) +
  geom_histogram(binwidth = 0.02, fill = "darkred", color = "black", alpha = 0.7) +
  theme_minimal() +
  labs(title = "Variant Allele Frequency (VAF) Distribution",
       x = "VAF",
       y = "Number of Mutations")
```
*A distinct peak around VAF = 0.5 typically represents heterozygous germline mutations, while lower peaks often represent subclonal somatic mutations.*

---

## 4. Genome LiftOver (e.g., hg19 to hg38)

Often, you may receive older variant data mapped to an outdated genome assembly (like `hg19`). You must "LiftOver" these coordinates to the modern `hg38` assembly before combining them with new data.

```r
library(rtracklayer)
library(GenomicRanges)

# Load the chain file downloaded from UCSC
chain <- import.chain("hg19ToHg38.over.chain")

# Create a GRanges object of your hg19 variants
hg19_variants <- GRanges(seqnames = Rle(c("chr1", "chr2")),
                         ranges = IRanges(start = c(10000, 20000), width = 1))

# Perform the LiftOver
hg38_variants <- liftOver(hg19_variants, chain)

print(hg38_variants)
```

## Conclusion

A robust WES pipeline requires careful alignment, stringent duplicate removal, accurate variant calling, and deep interpretation of metrics like VAF. By mastering these steps, you can confidently identify pathogenic mutations in complex cohorts.



### Matched Python and R VAF calculation

Check the VCF header and sample order before calculating variant allele fraction. The simplified examples below use allele-depth fields and should be extended for multi-allelic sites, quality filters, tumor purity, and copy-number context.

```python
import pandas as pd
from cyvcf2 import VCF

rows = []
for variant in VCF("sample.vcf.gz"):
    allele_depths = variant.format("AD")[0]
    if allele_depths is None or len(allele_depths) < 2:
        continue
    ref_depth, alt_depth = map(int, allele_depths[:2])
    total_depth = ref_depth + alt_depth
    rows.append({
        "chrom": variant.CHROM,
        "position": variant.POS,
        "vaf": alt_depth / total_depth if total_depth else float("nan"),
    })
vaf_table = pd.DataFrame(rows)
```
```r
library(VariantAnnotation)

vcf <- readVcf("sample.vcf.gz")
allele_depths <- geno(vcf)$AD
ref_depth <- allele_depths[1, 1, ]
alt_depth <- allele_depths[2, 1, ]
vaf <- alt_depth / (ref_depth + alt_depth)
vaf_table <- data.frame(position = start(rowRanges(vcf)), vaf = vaf)
```

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why are a variant call, a high VAF, and a clinically meaningful conclusion different levels of evidence?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Inspect a training VCF and report the reference build, one variant’s depth/quality/VAF, and the filters applied. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a variant is absent or low quality, how will you inspect coverage, alignment context, caller filters, and genome-build consistency?</p>
    </div>
  </div>
</div>
