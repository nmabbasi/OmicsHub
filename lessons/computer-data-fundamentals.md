---
title: "Computer and Data Fundamentals for Biologists"
category: "Foundations & Prerequisites"
date: "2026-08-15"
image: "images/computer-data-fundamentals.jpg"
excerpt: "Learn how computers store, process, and move biological data before using Linux, HPC, and omics workflows."
author: "Nasir Mahmood Abbasi, PhD"
---

<div class="mb-10 text-xl text-gray-600 leading-relaxed">
  <p>Before learning bioinformatics commands, it helps to understand what the computer is doing. This lesson builds a practical mental model of files, storage, memory, processors, paths, permissions, and compression so that later command-line errors are easier to diagnose.</p>
</div>

## Learning Objectives & Prerequisites

**By the end of this lesson, you should be able to:**

- Explain the difference between CPU, RAM, storage, and network bandwidth.
- Describe files, directories, paths, extensions, metadata, and file permissions.
- Estimate why sequencing data needs substantial storage and memory.
- Choose safe locations for raw data, intermediate files, and results.

**Prerequisites:**

- A web browser and a terminal such as macOS Terminal, Linux Terminal, or WSL.
- No programming experience is required.

## 1. The four resources every workflow uses

A CPU executes instructions, RAM holds actively used data, storage keeps files between sessions, and network bandwidth controls transfer speed. A workflow may be limited by any one of these resources. For example, a compressed FASTQ file can fit on disk but still require much more temporary space after decompression.

| Resource | What it controls | Typical failure |
|---|---|---|
| CPU | How quickly calculations run | Long runtime |
| RAM | How much data a process can hold | Out-of-memory error |
| Storage | Files and temporary output | Disk quota/full disk |
| Network | Download/upload speed | Slow or interrupted transfer |

## 2. Files, paths, and safe organization

A path identifies a location. Absolute paths begin at the filesystem root, while relative paths begin in the current directory. Keep raw data read-only and separate from derived results so that an analysis can be repeated.

```text
project/
├── data/raw/          # original downloads; never edit
├── data/processed/    # filtered or converted data
├── scripts/           # commands and programs
├── results/           # tables and figures
├── logs/              # execution logs
└── README.md          # provenance and instructions
```

## 3. Inspect a workspace safely

The following commands work on Linux, macOS, and WSL. Read the output before deleting or moving anything.

```bash
pwd
ls -lah
du -sh .
df -h .
mkdir -p project/{data/raw,data/processed,scripts,results,logs}
printf "# Project
" > project/README.md
```

## 4. Compression and file size

FASTQ and tabular files are often compressed with gzip. Compression saves storage and transfer time but some tools can read compressed input directly while others require decompression. Check the file before processing it.

```bash
file reads.fastq.gz
gzip -l reads.fastq.gz
zcat reads.fastq.gz | head -n 8
```

## Practical Exercise

Create the project tree above, place a small text file in `data/raw`, record its size with `du -h`, and write a README sentence describing where raw data and results belong.

**Pass criteria:** The project contains the six named directories, the raw file is unchanged, and the README explains the raw/processed/results distinction.

## Troubleshooting

If `mkdir` reports a permission error, work inside your home directory rather than a system directory. If `df -h` is nearly full, do not start a large download; ask the cluster administrator about quotas.

## Knowledge Check & Assessment

### 1. Concept Verification

Write short answers explaining the main concepts, the assumptions behind them, and one way a careless workflow could produce a misleading result.

### 2. Practical Execution

Complete the practical exercise above and save the command, script, table, or figure in the project structure. **Pass Criteria:** The project contains the six named directories, the raw file is unchanged, and the README explains the raw/processed/results distinction.

### 3. Troubleshooting

Explain what you would inspect first if the output were empty, malformed, unexpectedly large, or failed because of a missing file, package, permission, memory, or metadata problem.

## Next Steps

Continue with [Biological Data Formats](biological-data-formats.html) and [Reproducible Project Structure](reproducible-project-structure.html). Record the software versions, dataset or example inputs, and any decisions you made.
