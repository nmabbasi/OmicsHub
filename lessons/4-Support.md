---
title: "Managing Resources"
date: "2025-08-23"
author: "Nasir Mahmood Abbasi, PhD"
category: "High-Performance Computing (HPC)"
excerpt: "Learn how to diagnose common errors on HPC systems, use man pages and help flags effectively, read error logs, and know when and how to contact cluster support."
image: "images/support.png"
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
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



# Linux/Unix Commands and Scripting

## Linux

### Linux/Unix commands and scripting

**Text based tutorials**

[Software Carpentry tutorial on the Unix Shell.](https://swcarpentry.github.io/shell-novice/) This tutorial explains the basics of the Unix shell (Linux is a _Unix-like_ operating system), including the difference between graphical user interface (GUI) and command line interface, using the prompt, navigating the file system, basic Unix/Linux commands, and the use of a text editor.

**Video tutorial**

[LinkedIn Learning video tutorial on Linux.](https://www.linkedin.com/learning/learning-linux-command-line-2) Going through the full Linux tutorial on LinkedIn Learning is well worth the time and consists of less than 2.5 hours total of video instruction and setup. 

See the video [Essential Linux Commands - Fluency Drill](https://www.youtube.com/watch?v=SYOANUvIg_A) for practice using the basic set of commands. It also explains file and directory permissions, and how to change them.

# Command Line Text Editors

### Command line text editors

**Vi/Vim**:

See the [full LinkedIn Learning video tutorial on Vim](https://www.linkedin.com/learning/learning-vim) or a [short section on Vim](https://www.linkedin.com/learning/learning-linux-command-line-2) from LinkedIn Learning Linux tutorial (skip the sudo apt install part).

**nano**:

See the [full LinkedIn Learning video tutorial on nano](https://www.linkedin.com/learning/learning-nano) or a [short section on nano](https://www.linkedin.com/learning/learning-linux-command-line-2) from LinkedIn Learning Linux tutorial.

# HPC Questions / Requests

If you have any questions or requests regarding the HPC cluster, please send an email to `nmabbasi@gmail.com`.



---


## References

1. Official tool documentation and package vignettes.
2. Stuart, T., et al. (2019). Comprehensive Integration of Single-Cell Data. *Cell*, 177(7), 1888-1902.e21. (For Seurat-based workflows)
3. Orchestrating Single-Cell Analysis with Bioconductor (OSCA) - A comprehensive guide to single-cell data analysis.
4. [Bioconductor](https://bioconductor.org/) and [CRAN](https://cran.r-project.org/) package manuals.

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
