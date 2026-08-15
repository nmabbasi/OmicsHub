---
title: "Basic Slurm Commands"
date: "2025-08-23"
author: "Nasir Mahmood Abbasi, PhD"
category: "High-Performance Computing (HPC)"
excerpt: "Learn to load software modules, inspect cluster partitions and nodes, monitor running jobs with squeue, and submit your first tasks on an HPC system."
image: "images/hpc.png"
---

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>



## Modules

Some programs on the HPC cluster are only accessible by loading specific modules. For example, to compile MPI programs with `mpic++`, you would load the appropriate module:

```bash
module load mpi/openmpi-x86_64
```

For more options and commands, you can always consult the manual:


```bash
man module
```

Here are some of the most important `module` commands:

*   `module avail`: Lists all available modules.
*   `module list`: Lists all currently loaded modules.
*   `module load X`: Loads module `X`.
*   `module unload X`: Unloads module `X`.
*   `module purge`: Unloads all currently loaded modules.

**Important**: Remember to load the appropriate modules inside your job submission scripts (see [Writing a submission script]()). These in-script module loads are usually preceded by `module purge` to ensure a clean environment.

## Listing partitions and nodes

To view information about the cluster partitions and nodes, use the `sinfo` command:

```bash
sinfo
```

The `STATE` column indicates the status of the nodes listed in the `NODELIST` column. Common states include:

*   `idle`: No resources are allocated.
*   `mix`: Some resources are allocated, but not all.
*   `alloc`: At least one resource (CPU or memory) is fully allocated.
*   `drain`: The node will finish current jobs but will not accept new ones.
*   `down`: The node is shut down.

![partition](images/partitions.png)


For a comprehensive list of states and options, consult the manual:

```bash
man sinfo
```

To display the characteristics of each node, use:

```bash
sinfo --long --Node
```

The `--long` option provides detailed information. The important columns in the output are `CPUS` (maximum allocatable CPUs) and `Memory` (maximum available memory in Megabytes). You can restrict the output to a single partition using the `-p` option.

## Listing submitted jobs

To view all submitted jobs, use:

```bash
squeue
```

To see only your own jobs, use:

```bash
squeue -u `whoami`
```

The `ST` column shows the job status, typically `R` for running or `PD` for pending.

## Partitions, nodes and jobs in a GUI

If X forwarding is activated (see section [Running a GUI]()), you can run a graphical interface to monitor the cluster:

```bash
sview&
```

## Running tasks

There are two primary ways to execute tasks on the cluster nodes:

1.  **Submit a job** (section [Submitting a job]()).
2.  **Start an interactive session** (section [Running an interactive session]()).

Interactive sessions should generally be reserved for specific cases:

*   When you need to run a Graphical User Interface (GUI).
*   When you are debugging your program.

For all other scenarios, it is highly recommended to submit a job script. The reason is that interactive sessions require allocated resources, and there is often downtime (e.g., modifying scripts, waiting for tasks, or idle time if you forget the task has completed). During this downtime, resources remain allocated but unused, which is inefficient. Job scripts ensure resources are utilized effectively.

# Custom Module

### Creating a custom module

If you have a program that you want to make available to others, you can create a custom module for it. This involves creating a module file that defines the environment variables and paths needed to run your program.

**Example module file (`myprogram/1.0.lua`):**

```lua
help([[This module loads MyProgram version 1.0]])

prepend_path("PATH", "/path/to/myprogram/bin")
prepend_path("LD_LIBRARY_PATH", "/path/to/myprogram/lib")
```

Place this file in a directory that is part of the `MODULEPATH` environment variable. You can check your `MODULEPATH` with `module use`.

### Using a custom module

Once your custom module is created and placed in the correct location, you can load it like any other module:

```bash
module load myprogram/1.0
```


















---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
