---
title: "Docker & Singularity"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Workflow & Containerization"
excerpt: "Understand how containerization solves the dependency hell of bioinformatics, focusing on Docker for local use and Singularity for HPC clusters."
image: "images/command-line-terminal.png"
---

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Containerization in Bioinformatics

## The Dependency Hell

In bioinformatics, "Dependency Hell" is the situation where Software A requires Python 3.8 and package X version 1.2, but Software B requires Python 3.10 and package X version 2.0. Even with Conda, complex environments can break over time.

Worse, if you publish a paper today, a researcher trying to run your script in 5 years might find that the underlying packages are no longer available. 

The ultimate solution is **Containerization**. 

---

## 1. What is a Container?

A container is a standalone, executable package of software that includes **everything** needed to run an application: the code, runtime, system tools, system libraries, and settings. 

When you run a bioinformatics pipeline inside a container, you are guaranteed that it will execute identically on your laptop, on an HPC cluster, or in the cloud.

---

## 2. Docker: The Industry Standard

**Docker** is the most famous container platform. It requires root (administrator) privileges to run, making it ideal for your local laptop or cloud instances (AWS/GCP).

### Finding Containers
You rarely need to build your own containers from scratch. The **Biocontainers** project automatically builds Docker images for almost every bioinformatics tool in existence.

### Running a Docker Container

Instead of installing `bwa` locally, you can pull the official Biocontainer for it:

```bash
# Pull the container image
docker pull quay.io/biocontainers/bwa:0.7.17--hed695b0_7

# Run BWA completely isolated from your host system
docker run -v /my/local/data:/data quay.io/biocontainers/bwa:0.7.17--hed695b0_7 bwa mem /data/ref.fa /data/reads.fq
```
*Note: The `-v` flag mounts your local data folder into the container so the software can see your files.*

---

## 3. Singularity (Apptainer): The HPC Solution

**The Problem with Docker on HPC:** Docker requires root access. System administrators of High-Performance Computing (HPC) clusters will *never* give users root access, as it is a massive security risk.

**The Solution:** **Singularity** (now rebranded as **Apptainer**) was built specifically for scientific computing. It allows you to run containers securely *without* root privileges.

### Converting Docker to Singularity
The beauty of Singularity is that it can seamlessly convert and run Docker images!

```bash
# Pull a Docker image and convert it into a Singularity Image Format (.sif) file
apptainer pull bwa_container.sif docker://quay.io/biocontainers/bwa:0.7.17--hed695b0_7
```

### Running Singularity on Slurm

Singularity works perfectly alongside HPC schedulers like Slurm.

```bash
#!/bin/bash
#SBATCH --job-name=bwa_map
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G

# Execute the containerized software
apptainer exec bwa_container.sif bwa mem -t 8 reference.fa reads.fq > output.sam
```

## Summary

If you combine **Nextflow** (to handle the logic) with **Singularity** (to handle the software environments), you achieve the holy grail of modern computational biology: 100% reproducible, instantly scalable research.


---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
