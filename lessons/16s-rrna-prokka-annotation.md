---
title: "16S rRNA and PROKKA"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metagenomics"
excerpt: "Learn the fundamentals of 16S rRNA amplicon sequencing techniques and how to perform rapid prokaryotic genome annotation using PROKKA."
image: "images/bioinformatics-intro.png"
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
    <li><strong>Prerequisites:</strong> Complete Biological Data Formats and basic command-line navigation; understand the distinction between amplicon data and assembled genomes.</li>
    <li><strong>Objective:</strong> Differentiate 16S rRNA profiling from prokaryotic genome annotation and select appropriate inputs, outputs, and validation checks for each.</li>
    <li><strong>Expected Output:</strong> A documented analysis plan that names the correct input type, reference/database choice, and expected output for 16S or PROKKA work.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Academy Pathway</a> to review any prerequisite stage before continuing.</p>
</div>



## 16S rRNA Profiling and PROKKA Annotation

## 1. 16S rRNA Amplicon Sequencing

While shotgun metagenomics sequences all DNA in a sample, **16S rRNA sequencing** is an amplicon-based method that targets a specific, highly conserved gene (the 16S ribosomal RNA gene) found in all bacteria and archaea.

Because the 16S gene contains both highly conserved regions (used for primer binding) and hypervariable regions (V1-V9, used for species identification), it serves as a "molecular barcode" to profile "who is there" in a microbiome.

### Key Tools and Techniques

The standard workflow for 16S analysis involves moving from raw FASTQ reads to an Operational Taxonomic Unit (OTU) or Amplicon Sequence Variant (ASV) table.

#### QIIME 2 (Quantitative Insights Into Microbial Ecology)
QIIME 2 is the gold standard platform for microbiome analysis.

```bash
# Example QIIME 2 workflow for DADA2 denoising
qiime dada2 denoise-paired \
  --i-demultiplexed-seqs demux.qza \
  --p-trunc-len-f 250 \
  --p-trunc-len-r 250 \
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats denoising-stats.qza
```

#### DADA2
DADA2 replaces traditional OTU clustering (grouping sequences by 97% similarity) with ASVs, which provide single-nucleotide resolution by modeling Illumina sequencing errors.

#### Taxonomy Assignment
Once ASVs are identified, they are assigned to a taxonomy using databases like **SILVA**, **Greengenes**, or **RDP**.

---

## 2. Genome Annotation with PROKKA

Once you have identified a bacteria of interest (via 16S) and assembled its genome (using tools like SPAdes), you have a long FASTA file of DNA bases. However, this DNA sequence is meaningless without knowing where the genes are and what they do.

**PROKKA** is a software tool designed to rapidly annotate bacterial, archaeal, and viral genomes. It coordinates a suite of existing software tools to identify features like:
*   Coding sequences (CDS)
*   rRNA and tRNA
*   Non-coding RNA

### Installing PROKKA

```bash
# PROKKA is easily installed via Conda
mamba create -n prokka_env prokka
conda activate prokka_env
```

### Running PROKKA

PROKKA is designed to be incredibly simple and fast, typically annotating a standard bacterial genome in under 10 minutes on a standard laptop.

```bash
# Run PROKKA on an assembled contig file
prokka --outdir my_annotation --prefix Ecoli_K12 assembled_contigs.fasta
```

### Understanding PROKKA Outputs

PROKKA generates multiple output files in the `my_annotation` directory:

*   **`.gff`**: The master annotation file in GFF3 format, containing both sequences and annotations. This is the primary file loaded into genome viewers like IGV.
*   **`.faa`**: Protein FASTA file of the translated coding genes.
*   **`.ffn`**: Nucleotide FASTA file of all the transcript genes.
*   **`.txt`**: A statistical summary of the features annotated.

### Advanced Usage

You can customize PROKKA by providing a trusted set of proteins. PROKKA will use these to annotate your genome before relying on its default databases.

```bash
# Force PROKKA to prioritize a specific reference database
prokka --proteins trusted_reference.faa --outdir custom_annotation assembled_contigs.fasta
```

By combining 16S profiling for community structure and PROKKA for functional genome annotation, researchers can build a comprehensive understanding of microbial ecology.


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why should 16S amplicon profiling and PROKKA annotation not be treated as interchangeable analyses?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Inspect one 16S feature table and one bacterial assembly, then identify which downstream task is appropriate for each and why. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If taxonomic labels or annotations look implausible, how will you check database version, contamination, input quality, and the limits of marker-based assignment?</p>
    </div>
  </div>
</div>
