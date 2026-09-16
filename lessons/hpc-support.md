---
title: "HPC Troubleshooting and Support"
date: "2026-09-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "High-Performance Computing (HPC)"
excerpt: "Learn how to diagnose common errors on HPC systems, use Slurm commands effectively, read error logs, and know when and how to contact cluster support."
image: "images/hpc-managing-resources.webp"
---

<div class="flex flex-wrap items-center gap-4 text-xs font-mono text-gray-500 bg-gray-50 p-3 rounded-lg border border-gray-200 mb-6">
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    <span><strong>Tested on:</strong> Slurm 23.02, Ubuntu 24.04</span>
  </div>
  <div class="flex items-center gap-1">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
    <span><strong>Last Review:</strong> 2026-09-14</span>
  </div>
</div>

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Complete the preceding HPC lessons and have access to your own job IDs and log files, where permitted.</li>
    <li><strong>Objective:</strong> Diagnose common cluster problems, collect useful evidence, and write an effective support request without exposing sensitive data.</li>
    <li><strong>Expected Output:</strong> A support-ready issue report containing the job ID, command, resource request, relevant log excerpt, and steps already attempted.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Learning Path</a> to review any prerequisite stage before continuing.</p>
</div>


## Diagnosing HPC Failures

When running large-scale bioinformatics pipelines on a High-Performance Computing (HPC) cluster, job failures are inevitable. Whether it is an Out-Of-Memory (OOM) error, a timeout, or a missing dependency, knowing how to independently diagnose the issue is a critical skill.

Before escalating an issue to your cluster's support team or system administrators, you should systematically investigate the failure using Slurm's built-in accounting and profiling tools.

---

## 1. Checking Job State and Exit Codes

When a job fails or disappears from the queue, your first step should be checking its final state and exit code using `sacct` (Slurm Accounting).

```bash
# Replace 1234567 with your actual job ID
sacct -j 1234567 --format=JobID,JobName,State,ExitCode,Elapsed,ReqMem,MaxRSS
```

### Common Slurm States:
*   `COMPLETED`: The job finished successfully (ExitCode 0:0).
*   `FAILED`: The job terminated with a non-zero exit code. Look at the `ExitCode` column.
*   `TIMEOUT`: The job exceeded its requested walltime (`--time`).
*   `OUT_OF_MEMORY` or `OOM`: The job used more memory than requested (`--mem`).
*   `CANCELLED`: The job was killed by the user or an administrator.

### Understanding Exit Codes
If your job state is `FAILED`, the exit code provides the first clue:
*   **Exit Code 1**: General error (e.g., syntax error in your script, file not found).
*   **Exit Code 127**: "Command not found". This usually means you forgot to load a module (e.g., `module load samtools`) or activate your Conda environment before running the tool.
*   **Exit Code 137**: Process killed (SIGKILL). In HPC environments, this is almost always an **Out-Of-Memory (OOM)** kill by the Linux kernel because your process exceeded the memory allocated to it by Slurm.

---

## 2. Investigating Out-Of-Memory (OOM) Errors

Memory limits are the most common cause of bioinformatics job failures. Tools like genome assemblers, aligners (STAR, BWA), and single-cell tools (Seurat, Scanpy) can consume massive amounts of RAM.

If you suspect an OOM error, compare the `ReqMem` (Requested Memory) with the `MaxRSS` (Maximum Resident Set Size, or peak memory usage) from your `sacct` output.

```bash
sacct -j 1234567 --format=JobID,ReqMem,MaxRSS,State
```

If `MaxRSS` is very close to or equals `ReqMem`, the job was killed for memory reasons. 

### Profiling with `seff`
Many clusters provide the `seff` (Slurm Efficiency) tool, which offers a highly readable summary of CPU and Memory utilization for a completed job.

```bash
seff 1234567
```

**Output Example:**
```text
Job ID: 1234567
Cluster: omicshub-cluster
User/Group: TheOmicsHub/research
State: OUT_OF_MEMORY (exit code 125)
Nodes: 1
Cores per node: 8
CPU Utilized: 02:15:30
CPU Efficiency: 85.20% of 02:39:04 core-walltime
Job Wall-clock time: 00:19:53
Memory Utilized: 64.00 GB
Memory Efficiency: 100.00% of 64.00 GB
```
In this example, the memory efficiency is 100%, confirming the job hit its limit. The solution is to resubmit the job with a higher `--mem` request (e.g., `--mem=128G`).

---

## 3. Reading the Error Logs

Slurm normally writes standard output to `slurm-<jobid>.out` and standard error to the same file, unless you explicitly split them using `--error=slurm-%j.err`.

Always check the last 50 lines of your log file for stack traces or error messages from the software itself:

```bash
tail -n 50 slurm-1234567.out
```

**Common log file errors:**
*   `FileNotFoundError: No such file or directory: 'data/reads.fastq'`: Your script is running from the wrong directory. Ensure your submission script uses `cd $SLURM_SUBMIT_DIR`.
*   `ModuleNotFoundError: No module named 'scanpy'`: Your Conda environment wasn't activated in the batch script.

---

## 4. How to Write an Effective Support Ticket

If you have checked the exit codes, analyzed the logs, and still cannot resolve the issue, it is time to contact HPC support.

System administrators handle hundreds of users and tickets. A vague message like *"My job failed, please help"* will significantly delay your resolution. Instead, provide a **Minimal Reproducible Example (MRE)**.

### Information to Include:
1.  **Job ID(s)** of the failed runs.
2.  **The exact command or submission script** you used (`sbatch run_pipeline.sh`).
3.  **The path to your working directory** so admins can inspect the files.
4.  **A specific excerpt of the error log** (do not attach a 50MB log file; paste the relevant 20 lines).
5.  **What you have already tried** (e.g., "I increased the memory to 128G but it still failed with Exit Code 137").

### Template for HPC Support:
> **Subject:** Job failing with Exit Code 137 on the highmem partition
>
> Hello HPC Support,
>
> My job (`ID: 1234567`) running `cellranger count` failed on the `highmem` partition.
> 
> *   **Working Directory:** `/scratch/users/TheOmicsHub/project_x`
> *   **Script:** `run_cellranger.sh`
> *   **Log File:** `slurm-1234567.out`
>
> The `sacct` output shows `State: FAILED` and `ExitCode: 137`. I initially requested 64GB of RAM and it failed, so I increased it to 128GB (`Job ID: 1234568`), but it still failed immediately. 
>
> The end of the log file shows: `error: memory allocation failed`. Is there a hard limit on memory per task on this partition, or could this be a node-specific hardware issue?
>
> Thank you.

---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">Why is a reproducible minimal example more useful to HPC support than a vague statement that “the cluster failed”?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Run the diagnostic commands (`sacct` and `seff`) in this lesson for one completed or test job and assemble a concise troubleshooting note. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a job fails with `Exit Code 127`, what is the most likely problem with your submission script?</p>
    </div>
  </div>
</div>
