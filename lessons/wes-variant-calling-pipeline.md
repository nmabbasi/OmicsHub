---
title: "Whole Exome Sequencing (WES): Variant Calling & VAF"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Genomics & Whole Exome Sequencing"
excerpt: "A comprehensive guide to Whole Exome Sequencing (WES) analysis, covering read alignment, variant calling, LiftOver, and Variant Allele Frequency (VAF) calculations."
image: "images/bioinformatics-intro.png"
---

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Whole Exome Sequencing (WES) Pipeline

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


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
