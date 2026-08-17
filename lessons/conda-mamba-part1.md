---
title: "Conda, Mamba, and Micromamba"
date: "2025-08-13"
author: "Nasir Mahmood Abbasi, PhD"
category: "Package Management"
excerpt: "A complete guide to installing Conda and Mamba, creating isolated environments, and managing bioinformatics software to ensure fully reproducible analyses."
image: "images/conda-mamba-part1.png"
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
    <li><strong>Prerequisites:</strong> Complete Basic Navigation and have a terminal with permission to install software in your home directory.</li>
    <li><strong>Objective:</strong> Create, activate, export, clone, and troubleshoot isolated Conda or Mamba environments for bioinformatics software.</li>
    <li><strong>Expected Output:</strong> An environment YAML file that recreates a named environment containing one specified bioinformatics tool.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Why Package Management Matters in Bioinformatics

If you've ever spent hours trying to install a bioinformatics tool only to run into dependency conflicts, version mismatches, or the dreaded "it works on my machine" problem: you're not alone. Package management is one of the biggest pain points for researchers entering computational biology.

That's where Conda and Mamba come in. Think of them as your personal assistants for managing software installations: they handle all the messy details of dependencies, versions, and compatibility so you can focus on your research instead of wrestling with installation issues.

## What Are Conda and Mamba?

### Conda: The Foundation

**Conda** is a package manager and environment management system that was originally created for Python but has evolved to support packages from any language. It's like having a smart librarian who not only knows where every book is but also ensures that when you check out a book, all the related materials you need are available and compatible.

Key features of Conda:
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Language-agnostic**: Manages Python, R, C++, Java, and more
- **Environment isolation**: Keeps different projects separate
- **Dependency resolution**: Automatically handles complex dependencies

### Mamba: The Speed Demon

**Mamba** is a reimplementation of Conda that's significantly faster: we're talking about going from minutes to seconds for complex installations. It's essentially Conda with a turbo engine, using the same commands and configuration files but with dramatically improved performance.

Why Mamba is faster:
- **Parallel processing**: Downloads and installs packages simultaneously
- **Better algorithms**: More efficient dependency resolution
- **Optimized codebase**: Written in C++ instead of Python

## Installation Guide

### Option 1: Miniconda (Recommended)

Miniconda is a minimal installer that includes only Conda and Python. It's perfect for bioinformatics work because you can install exactly what you need.

#### Linux Installation
```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make it executable
chmod +x Miniconda3-latest-Linux-x86_64.sh

# Run the installer
bash Miniconda3-latest-Linux-x86_64.sh

# Follow the prompts and restart your terminal
```

#### macOS Installation
```bash
# Download Miniconda
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# Run the installer
bash Miniconda3-latest-MacOSX-x86_64.sh

# For Apple Silicon Macs, use:
# curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
```

#### Windows Installation
1. Download the Windows installer from [conda.io](https://conda.io/miniconda.html)
2. Run the `.exe` file and follow the installation wizard
3. Use Anaconda Prompt for all conda commands

### Option 2: Anaconda (Full Distribution)

Anaconda includes Conda plus 250+ pre-installed packages. It's convenient but takes up more space (3GB vs 400MB for Miniconda).

Download from [anaconda.com](https://www.anaconda.com/products/distribution) and follow the installation instructions.

### Verifying Installation

After installation, verify that Conda is working:

```bash
conda --version
# Should output something like: conda 23.7.4

conda info
# Shows detailed information about your Conda installation
```

## Installing Mamba

Once you have Conda installed, adding Mamba is straightforward:

```bash
# Install Mamba from conda-forge
conda install -c conda-forge mamba

# Verify installation
mamba --version
```

From now on, you can use `mamba` instead of `conda` for most commands: it's faster and uses the same syntax!

## Understanding Environments

### Why Use Environments?

Imagine you're working on three different projects:
1. **Project A**: Requires Python 3.8 and pandas 1.2
2. **Project B**: Requires Python 3.9 and pandas 1.5
3. **Project C**: Requires R 4.1 and Bioconductor 3.14

Without environments, these requirements would conflict. Environments solve this by creating isolated spaces where each project can have its own dependencies.

### Creating Your First Environment

```bash
# Create environment for single-cell analysis
mamba create -n single-cell python=3.9

# Create environment with specific packages
mamba create -n rnaseq python=3.9 pandas numpy matplotlib

# Create environment from a file (more on this later)
mamba env create -f environment.yml
```

### Activating and Deactivating Environments

```bash
# Activate environment
conda activate single-cell

# Your prompt should change to show the active environment:
# (single-cell) username@computer:~$

# Deactivate environment
conda deactivate

# List all environments
conda env list
```

**Pro tip**: Always activate the appropriate environment before starting work on a project!

## Installing Bioinformatics Software

### Essential Channels

Channels are repositories where packages are stored. For most modern bioinformatics environments, use **conda-forge** and **bioconda** with strict priority. The current Bioconda guidance no longer includes `defaults` in the recommended configuration.

```bash
# conda config --add works from lower to higher priority.
# Run these once to give conda-forge the highest priority.
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict

# Check the resulting configuration
conda config --show channels
conda config --show channel_priority
```

For one command without changing `~/.condarc`, place command-line channels in decreasing priority:

```bash
mamba create -n bioinfo -c conda-forge -c bioconda samtools bwa
```

See the [Bioconda usage guidance](https://bioconda.github.io/) when a solver conflict appears or when maintaining an older environment.

### Installing Common Bioinformatics Tools

#### Sequence Analysis Tools
```bash
# Activate your environment
conda activate bioinformatics

# Install BLAST
mamba install blast

# Install BWA and Bowtie2 for alignment
mamba install bwa bowtie2

# Install SAMtools for BAM file manipulation
mamba install samtools

# Install FastQC for quality control
mamba install fastqc
```

#### R and Bioconductor
```bash
# Install R
mamba install r-base

# Install essential R packages
mamba install r-ggplot2 r-dplyr r-tidyr r-readr

# Install Seurat for single-cell analysis
mamba install r-seurat

# Install DESeq2 for differential expression
mamba install bioconductor-deseq2
```

#### Python Packages for Bioinformatics
```bash
# Install scientific computing stack
mamba install numpy pandas scipy matplotlib seaborn

# Install Jupyter for interactive analysis
mamba install jupyter

# Install Biopython
mamba install biopython

# Install scanpy for single-cell analysis
mamba install scanpy
```

### Installing from Different Channels

Sometimes you need to specify the channel explicitly:

```bash
# Install from specific channel
mamba install -c bioconda gatk4

# Install from multiple channels
mamba install -c conda-forge -c bioconda snakemake

# Search for packages
mamba search blast
mamba search -c bioconda "*blast*"
```

## Environment Management Best Practices

### 1. One Environment Per Project

Create separate environments for different projects to avoid conflicts:

```bash
# Project-specific environments
mamba create -n cancer-genomics python=3.9 pandas numpy
mamba create -n microbiome-analysis python=3.8 qiime2
mamba create -n phylogenetics python=3.9 biopython dendropy
```

### 2. Document Your Environments

Export your environment specifications so others can reproduce your setup:

```bash
# Export environment to file
conda env export > environment.yml

# Create environment from file
mamba env create -f environment.yml
```

Example `environment.yml` file:
```yaml
name: single-cell-analysis
channels:
  - conda-forge
  - bioconda
dependencies:
  - python=3.9
  - pandas=1.5.3
  - numpy=1.24.3
  - matplotlib=3.7.1
  - seaborn=0.12.2
  - r-base=4.3.1
  - r-seurat=4.3.0
  - r-ggplot2=3.4.2
  - jupyter=1.0.0
  - pip
  - pip:
    - scanpy==1.9.3
    - anndata==0.9.2
```

### 3. Pin Important Versions

For reproducible research, pin versions of critical packages:

```bash
# Pin specific versions
mamba install python=3.9.16 pandas=1.5.3 numpy=1.24.3

# Allow patch updates but lock major.minor versions
mamba install "python>=3.9,<3.10" "pandas>=1.5,<1.6"
```

### 4. Regular Environment Maintenance

Keep your environments clean and up-to-date:

```bash
# Update all packages in current environment
mamba update --all

# Update specific package
mamba update pandas

# Remove unused packages
mamba clean --all

# Remove entire environment
conda env remove -n old-project
```

## Advanced Usage Patterns

### Creating Environments for Specific Workflows

#### Single-cell RNA-seq Environment
```bash
mamba create -n scrna-seq python=3.9 \
  pandas numpy matplotlib seaborn \
  r-base r-seurat r-ggplot2 r-dplyr \
  jupyter scanpy anndata \
  -c conda-forge -c bioconda
```

#### Genomics Pipeline Environment
```bash
mamba create -n genomics python=3.9 \
  bwa bowtie2 samtools bcftools \
  gatk4 picard fastqc multiqc \
  snakemake -c conda-forge -c bioconda
```

#### Phylogenetics Environment
```bash
mamba create -n phylo python=3.8 \
  biopython dendropy ete3 \
  muscle mafft iqtree raxml \
  -c conda-forge -c bioconda
```

### Using Conda with Jupyter Notebooks

Make your environments available in Jupyter:

```bash
# Install ipykernel in your environment
conda activate single-cell
mamba install ipykernel

# Register environment as Jupyter kernel
python -m ipykernel install --user --name single-cell --display-name "Single Cell Analysis"

# Start Jupyter and select your kernel
jupyter notebook
```

### Environment Variables and Configuration

Set environment-specific variables:

```bash
# Set variables when activating environment
conda activate myenv
conda env config vars set CUDA_VISIBLE_DEVICES=0
conda env config vars set OMP_NUM_THREADS=8

# Reactivate to apply changes
conda deactivate
conda activate myenv
```

## Troubleshooting Common Issues

### Slow Package Resolution

If Conda is taking forever to resolve dependencies:

```bash
# Use Mamba instead (much faster)
mamba install package-name

# Use libmamba solver (Conda 22.11+)
conda install --solver=libmamba package-name

# Set libmamba as default solver
conda config --set solver libmamba
```

### Conflicting Dependencies

When packages conflict:

```bash
# Try installing from different channels
mamba install -c conda-forge package-name

# Create a fresh environment
mamba create -n fresh-env package-name

# Use pip as fallback (in conda environment)
conda activate myenv
pip install package-name
```

### Environment Activation Issues

If `conda activate` doesn't work:

```bash
# Initialize conda for your shell
conda init bash  # or zsh, fish, etc.

# Restart your terminal or source your profile
source ~/.bashrc

# Alternative activation method
source activate myenv
```

### Disk Space Issues

Conda can use lots of disk space:

```bash
# Clean package cache
conda clean --all

# Remove unused packages
conda clean --packages

# Check disk usage
du -sh ~/miniconda3/
```

## Integration with Other Tools

### Using Conda with Docker

Create reproducible containers:

```dockerfile
FROM continuumio/miniconda3

COPY environment.yml .
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]
RUN echo "Environment is ready!"
```

### Using Conda with Snakemake

Snakemake can automatically manage Conda environments:

```python
# Snakefile
rule quality_control:
    input: "data/sample.fastq"
    output: "results/sample_fastqc.html"
    conda: "envs/qc.yml"
    shell: "fastqc {input} -o results/"
```

### Using Conda with Singularity

Build containers with Conda environments:

```bash
# Build Singularity container with Conda
singularity build mycontainer.sif docker://continuumio/miniconda3
```

## Best Practices Summary

### Do's ✅

1. **Use separate environments for different projects**
2. **Document environments with `environment.yml` files**
3. **Use Mamba for faster installations**
4. **Pin versions for reproducible research**
5. **Regularly clean up unused packages and environments**
6. **Use conda-forge and bioconda channels**
7. **Activate environments before starting work**

### Don'ts ❌

1. **Don't install everything in the base environment**
2. **Don't mix conda and pip carelessly**
3. **Don't ignore version conflicts**
4. **Don't forget to document your environments**
5. **Don't use `sudo` with conda commands**

## Real-World Example: Setting Up a Single-Cell Analysis Environment

Let's walk through setting up a complete environment for single-cell RNA-seq analysis:

```bash
# Step 1: Create the environment
mamba create -n single-cell-analysis python=3.9

# Step 2: Activate the environment
conda activate single-cell-analysis

# Step 3: Install R and essential packages
mamba install -c conda-forge r-base=4.3.1

# Step 4: Install Seurat and dependencies
mamba install -c conda-forge r-seurat r-ggplot2 r-dplyr r-tidyr

# Step 5: Install Python packages
mamba install -c conda-forge pandas numpy matplotlib seaborn jupyter

# Step 6: Install scanpy for Python-based analysis
mamba install -c conda-forge scanpy

# Step 7: Install additional tools
mamba install -c bioconda samtools bcftools

# Step 8: Export environment for reproducibility
conda env export > single-cell-environment.yml

# Step 9: Test the installation
python -c "import scanpy; print('scanpy version:', scanpy.__version__)"
R --slave -e "library(Seurat); cat('Seurat version:', as.character(packageVersion('Seurat')), '\n')"
```

## Conclusion

Conda and Mamba are game-changers for bioinformatics research. They eliminate the frustration of dependency management and make it easy to create reproducible computational environments. With the skills covered in this tutorial, you can:

- Install complex bioinformatics software with confidence
- Create isolated environments for different projects
- Share your computational setup with collaborators
- Reproduce analyses months or years later

Remember, good package management isn't just about convenience: it's about reproducible science. When you document your environments and pin your package versions, you're contributing to the reproducibility crisis solution in computational biology.

## Next Steps

Now that you've mastered package management, you're ready to tackle more advanced bioinformatics topics:

1. **[Command Line Fundamentals](command-line-part1.html)**: Master the terminal for bioinformatics
2. **[Single-cell RNA-seq Analysis](scrna-seq-basics.html)**: Apply your new environment to cutting-edge analysis
3. **[Introduction to Bioinformatics](introduction-to-bioinformatics.html)**: Understand the broader context

With proper package management under your belt, you'll never have to worry about "dependency hell" again. Welcome to the world of reproducible bioinformatics!

---

*Having trouble with package installations? Need help setting up a specific environment? [Contact us](contact.html): we're here to help you get your computational environment running smoothly!*



<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is an isolated environment safer than installing packages into a system Python or shared default environment?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Create an environment, install a named command-line tool, export the YAML, then recreate the environment from that file. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If dependency solving fails, how will you inspect channels, version pins, channel priority, and conflicting packages before deleting the environment?</p>
    </div>
  </div>
</div>
