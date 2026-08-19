---
title: "The Omics Hub: Bioinformatics & Command Line Cheat Sheet"
author: "The Omics Hub"
date: "2026"
geometry: margin=1in
---

# Command Line Basics

## Navigation
- \`pwd\`: Print working directory (where am I?)
- \`ls -lh\`: List files with human-readable sizes
- \`cd /path/to/dir\`: Change directory
- \`cd ..\`: Move up one directory
- \`cd ~\`: Move to home directory

## File Operations
- \`cp file1 file2\`: Copy file1 to file2
- \`mv old_name new_name\`: Move or rename a file
- \`rm file.txt\`: Remove/delete a file (CAUTION: irreversible)
- \`mkdir my_analysis\`: Create a new directory
- \`rm -r my_analysis\`: Remove a directory and its contents

## Examining Data
- \`head -n 10 data.fastq\`: View first 10 lines
- \`tail -n 10 data.fastq\`: View last 10 lines
- \`less data.fastq\`: View a file page-by-page (press \`q\` to exit)
- \`wc -l file.txt\`: Count the number of lines in a file

## Searching & Filtering (The Bioinformatics Swiss Army Knife)
- \`grep "pattern" file.txt\`: Find lines containing "pattern"
- \`grep -c "pattern" file.txt\`: Count occurrences of "pattern"
- \`grep -v "pattern" file.txt\`: Find lines that DO NOT contain "pattern"
- \`awk '{print $1, $3}' file.txt\`: Print 1st and 3rd columns
- \`sort -k 2,2n file.bed\`: Sort a BED file numerically by the second column

# High-Performance Computing (HPC) / Slurm

## Job Management
- \`squeue -u username\`: Check status of your jobs
- \`scancel 123456\`: Cancel job ID 123456
- \`sbatch my_script.sh\`: Submit a batch job

## Example Slurm Script Header
\`\`\`bash
#!/bin/bash
#SBATCH --job-name=my_analysis
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=my_analysis_%j.log
\`\`\`

# Conda / Mamba Environment Management
- \`conda create -n rna_seq_env python=3.9\`: Create a new environment
- \`conda activate rna_seq_env\`: Activate environment
- \`conda install -c bioconda fastqc\`: Install a tool from bioconda channel
- \`conda env list\`: List all environments
- \`conda list\`: List installed packages in current environment

# Key Bioinformatics File Formats
1. **FASTA (.fa, .fasta)**: Reference genomes, transcriptomes. Alternating headers (\`>seq1\`) and sequences.
2. **FASTQ (.fq, .fastq)**: Raw sequencing reads with quality scores.
3. **BAM/SAM (.bam, .sam)**: Aligned reads. SAM is plain text; BAM is compressed binary.
4. **VCF (.vcf)**: Variant Call Format. Contains SNPs and Indels.
5. **GTF/GFF (.gtf, .gff)**: Gene annotations (coordinates of exons, genes, CDS).

# Quick Tips
- **Piping (\`|\`)**: Pass the output of one command to another. Example: \`ls -l | wc -l\`
- **Redirection (\`>\`)**: Save output to a file. Example: \`echo "Hello" > file.txt\`
- **Appending (\`>>\`)**: Add output to the end of a file. Example: \`echo "World" >> file.txt\`
- Use \`tab\` for auto-completion to avoid typos!

# Important Single-Cell / Biomarker Genes

Below is a quick reference for common biomarkers used in immunology and cancer research, specifically relating to T-cell malignancies like Sézary Syndrome:

- **CD4**: Helper T-cell marker.
- **FOXP3**: Master regulator for Regulatory T cells (Tregs). In Sézary syndrome, differentiating CD25+ and CD25- phenotypes is critical.
- **CLIC1**: Chloride Intracellular Channel 1. A key marker associated with metabolic vulnerabilities in malignant cells.
- **CD25 (IL2RA)**: Alpha chain of the IL-2 receptor, typically expressed on Tregs and activated T cells.
- **CCR4 / CCR7**: Chemokine receptors important for T-cell skin homing and lymph node migration.
