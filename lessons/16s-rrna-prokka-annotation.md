---
title: "16S rRNA and PROKKA"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Metagenomics"
excerpt: "Learn the fundamentals of 16S rRNA amplicon sequencing techniques and how to perform rapid prokaryotic genome annotation using PROKKA."
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



# 16S rRNA Profiling and PROKKA Annotation

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


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
