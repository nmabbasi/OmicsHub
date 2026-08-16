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
    <li><strong>Prerequisites:</strong> Complete the preceding HPC lessons and have access to your own job IDs and log files, where permitted.</li>
    <li><strong>Objective:</strong> Diagnose common cluster problems, collect useful evidence, and write an effective support request without exposing sensitive data.</li>
    <li><strong>Expected Output:</strong> A support-ready issue report containing the job ID, command, resource request, relevant log excerpt, and steps already attempted.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Academy Pathway</a> to review any prerequisite stage before continuing.</p>
</div>



## Linux/Unix Commands and Scripting

### Core command-line support resources

#### Linux/Unix commands and scripting

**Text based tutorials**

[Software Carpentry tutorial on the Unix Shell.](https://swcarpentry.github.io/shell-novice/) This tutorial explains the basics of the Unix shell (Linux is a _Unix-like_ operating system), including the difference between graphical user interface (GUI) and command line interface, using the prompt, navigating the file system, basic Unix/Linux commands, and the use of a text editor.

**Video tutorial**

[LinkedIn Learning video tutorial on Linux.](https://www.linkedin.com/learning/learning-linux-command-line-2) Going through the full Linux tutorial on LinkedIn Learning is well worth the time and consists of less than 2.5 hours total of video instruction and setup.

See the video [Essential Linux Commands - Fluency Drill](https://www.youtube.com/watch?v=SYOANUvIg_A) for practice using the basic set of commands. It also explains file and directory permissions, and how to change them.

### Command-line text editors

#### Command-line text editors

**Vi/Vim**:

See the [full LinkedIn Learning video tutorial on Vim](https://www.linkedin.com/learning/learning-vim) or a [short section on Vim](https://www.linkedin.com/learning/learning-linux-command-line-2) from LinkedIn Learning Linux tutorial (skip the sudo apt install part).

**nano**:

See the [full LinkedIn Learning video tutorial on nano](https://www.linkedin.com/learning/learning-nano) or a [short section on nano](https://www.linkedin.com/learning/learning-linux-command-line-2) from LinkedIn Learning Linux tutorial.

### Diagnose before escalating

Run these safe status checks before opening a support request. They help separate scheduler, resource, and application-level failures.

```bash
# Replace JOB_ID with a job you are allowed to inspect
squeue -j JOB_ID -o "%.18i %.9P %.12j %.8u %.2t %.10M %.6D %R"
sacct -j JOB_ID --format=JobID,State,ExitCode,Elapsed,ReqMem,MaxRSS
```

### HPC questions and requests

Include the job ID, exact command or script, requested resources, a short relevant log excerpt, and steps already attempted. Do not include passwords, private keys, participant identifiers, or restricted data. For general questions or requests, contact `nmabbasi@gmail.com`.



<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is a reproducible minimal example more useful to HPC support than a vague statement that “the cluster failed”?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run the diagnostic commands in this lesson for one completed or test job and assemble a concise troubleshooting note. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a job fails, how will you separate scheduler state, resource limits, environment problems, input-path mistakes, and application errors?</p>
    </div>
  </div>
</div>
