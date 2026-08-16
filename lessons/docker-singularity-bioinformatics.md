---
title: "Docker & Singularity"
date: "2026-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Workflow & Containerization"
excerpt: "Understand how containerization solves the dependency hell of bioinformatics, focusing on Docker for local use and Singularity for HPC clusters."
image: "images/command-line-terminal.png"
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
    <li><strong>Prerequisites:</strong> Complete Conda/Mamba Environments and basic HPC concepts; use only containers authorized by your institution.</li>
    <li><strong>Objective:</strong> Explain container images, bind mounts, reproducible tool execution, and the distinction between Docker and Singularity/Apptainer contexts.</li>
    <li><strong>Expected Output:</strong> A documented container command that reads a test input through an explicit bind mount and writes a result to a project directory.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>



## Containerization in Bioinformatics

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


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why do containers improve reproducibility without eliminating the need to record image versions, inputs, and parameters?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run an approved containerized command on a small test input and record the image reference, bind mount, command, and output path. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If files are invisible inside a container, how will you inspect bind mounts, working directory, permissions, and image entrypoint behavior?</p>
    </div>
  </div>
</div>
