---
title: "Conda for Bioinformatics: Installation, Environments, and Channel Configuration"
date: "2026-08-13"
author: "Bioinformatics Workflow Hub"
category: "Conda"
excerpt: "A focused guide to Conda: installing Miniconda, configuring bioconda and conda-forge channels correctly, and creating reproducible project environments. Covers the libmamba solver upgrade that makes modern Conda as fast as Mamba."
---

## What is Conda and Why Does It Matter?

**Conda** is a cross-platform package and environment manager created by Anaconda, Inc. For bioinformatics, it is the primary solution for installing and isolating software that spans multiple languages (Python, R, C++, Java) with complex dependency graphs.

The core problem Conda solves: bioinformatics tools have rigid version requirements. GATK4 may require Java 17. Seurat may pin to an exact R version. Installing these in your system Python or system R environment is a path to dependency conflicts and broken analyses months later.

> **2024 Update:** As of Conda 23.9+, the default solver has been upgraded to `libmamba`, meaning modern Conda is now nearly as fast as Mamba. If you have an older Conda version, upgrade or switch to Mamba (covered in the Mamba tutorial).

---

## Installation: Miniconda vs. Anaconda

### Miniconda (Recommended for Research)

Miniconda installs only the minimal base: Conda, Python, and a handful of packages. You build environments from scratch, which gives you full control.

```bash
# Linux (x86_64) - HPC default
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3

# macOS Intel
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh -b -p $HOME/miniconda3

# macOS Apple Silicon (M1/M2/M3)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh -b -p $HOME/miniconda3

# Initialize for your shell (do once)
$HOME/miniconda3/bin/conda init bash   # or zsh, fish
source ~/.bashrc
```

### Anaconda (Not Recommended for HPC)

Anaconda includes 250+ pre-installed packages (3 GB). Avoid it on shared HPC systems where disk quotas are tight.

### Verify Installation

```bash
conda --version     # e.g. conda 24.1.2
conda info          # Shows platform, active env, channel URLs
```

---

## Critical First Step: Channel Configuration

**This is the most commonly misconfigured part of Conda.** Channel priority determines which package version wins when a package exists in multiple channels. The correct setup for bioinformatics is:

```bash
# Add channels in this exact order (last added = highest priority)
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge

# CRITICAL: enable strict priority
conda config --set channel_priority strict

# Verify
conda config --show channels
# Should show:
# channels:
#   - conda-forge  (highest priority)
#   - bioconda
#   - defaults
```

> **Why `strict` priority?** Without it, Conda may silently mix incompatible package builds from different channels, causing subtle runtime errors that are extremely difficult to debug.

### Enable the libmamba Solver (Conda 22.11+)

```bash
# Check current solver
conda config --show solver

# Enable libmamba if not already set
conda config --set solver libmamba

# Verify
conda config --show solver
# solver: libmamba
```

---

## Creating and Managing Environments

### The Golden Rule: One Environment Per Project

```bash
# Create a named environment with a specific Python version
conda create -n myproject python=3.11

# Create with initial packages
conda create -n rna-analysis python=3.10 numpy pandas matplotlib

# Create an R-based environment
conda create -n deseq2-env r-base=4.3 bioconductor-deseq2 r-ggplot2 -c conda-forge -c bioconda

# Activate / deactivate
conda activate myproject
conda deactivate

# List all environments
conda env list
```

### Creating from an environment.yml File

The `environment.yml` file is the standard way to share and reproduce environments. Always commit this file to version control.

```yaml
# environment.yml - commit this file to your repository
name: scrna-analysis
channels:
  - conda-forge
  - bioconda
  - defaults
dependencies:
  - python=3.10
  - scanpy=1.9.8
  - anndata=0.10.3
  - pandas=2.0.3
  - numpy=1.25.2
  - matplotlib=3.8.0
  - seaborn=0.13.0
  - leidenalg=0.10.1
  - python-igraph=0.11.3
  - scrublet=0.2.3           # doublet detection
  - pip
  - pip:
    - scvi-tools==1.1.0
    - celltypist==1.6.2
```

```bash
# Create environment from file
conda env create -f environment.yml

# Update environment after editing the yml
conda env update -f environment.yml --prune

# Export your current environment exactly
conda env export > environment-locked.yml
```

---

## Installing Bioinformatics Software

### Sequence Analysis Tools

```bash
conda activate biotools

# Quality control
conda install -c bioconda fastqc multiqc

# Alignment
conda install -c bioconda bwa-mem2 bowtie2 star

# Post-alignment
conda install -c bioconda samtools picard

# Variant calling
conda install -c bioconda gatk4 bcftools

# Cell Ranger (10x Genomics) - install from 10x directly, not conda
```

### R Bioconductor Packages

```bash
conda create -n bioconductor r-base=4.3 -c conda-forge
conda activate bioconductor

# Install Bioconductor packages via bioconda channel
conda install -c conda-forge -c bioconda \
  bioconductor-deseq2 \
  bioconductor-edger \
  bioconductor-limma \
  bioconductor-scran \
  r-seurat \
  r-ggplot2 \
  r-dplyr
```

### Python Scientific Stack

```bash
conda install -c conda-forge \
  scanpy \
  anndata \
  scvi-tools \
  harmonypy \
  leidenalg \
  python-igraph \
  jupyter
```

---

## Reproducibility Best Practices

### Pin Critical Versions

```bash
# Install with explicit version pinning
conda install "python=3.10.12" "pandas=2.0.3" "numpy=1.25.2"

# Pin a package to prevent future updates from breaking it
echo "pandas=2.0.3" >> $CONDA_PREFIX/conda-meta/pinned
```

### The Correct Order When Mixing conda and pip

```bash
# Rule: install everything you can with conda first, pip last
conda activate myenv
conda install numpy pandas matplotlib scipy  # conda first
pip install some-package-not-on-conda        # pip last, inside activated env
```

> **Warning:** Running `pip install` before conda installs can cause conda to be unable to track or update packages. Always conda first.

### Cleaning Up Disk Space

Conda caches downloaded packages. Over time this can consume tens of gigabytes.

```bash
# See cache size
du -sh ~/.conda/pkgs/
du -sh ~/miniconda3/pkgs/

# Remove package cache (keeps installed environments intact)
conda clean --packages --tarballs

# Remove ALL unused packages and cache
conda clean --all

# Remove an entire environment
conda env remove -n old-project
```

---

## Common Errors and Fixes

### "Solving environment: failed"

```bash
# First, try using mamba (faster solver, better error messages)
mamba install package-name

# Or try a fresh environment
conda create -n test-env package-name

# Check for channel conflicts
conda config --show channels
# Ensure conda-forge is ABOVE bioconda in the list
```

### "conda activate does not work"

```bash
# Re-initialize conda for your shell
conda init bash
source ~/.bashrc

# Or manually source
source ~/miniconda3/etc/profile.d/conda.sh
```

### "PackageNotFoundError" for a bioinformatics tool

```bash
# Search across channels
conda search -c bioconda -c conda-forge tool-name

# If not found in conda, check bioconda.github.io recipes
# Many tools are only in bioconda
conda install -c bioconda tool-name
```

---

## Summary

Conda is the backbone of reproducible bioinformatics. With channel priority configured correctly and the libmamba solver enabled, it is now fast and reliable for even complex environments.

**Next steps:**
- Read the [Mamba tutorial](mamba-micromamba-guide.md) for speed comparison and micromamba for HPC/Docker
- See [Real-world Example: scRNA-seq Pipeline Setup](real-world-scrna-seq-scanpy.md) for a complete practical workflow
