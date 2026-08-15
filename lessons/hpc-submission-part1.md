---
title: "Writing Job Scripts"
date: "2025-08-23"
author: "Nasir Mahmood Abbasi, PhD"
category: "High-Performance Computing (HPC)"
excerpt: "Learn how to write and submit Slurm batch scripts on HPC clusters, allocate compute resources efficiently, and run parallel jobs at scale."
image: "images/sc.png"
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



## A basic script

All options actually have short versions (e.g., `--job-name` can be replaced by `-J`). The long names are used here for clarity. Not all options in this script are mandatory, but they represent the minimum recommended for clarity.

I use a generic `program` in all scripts. Replace it with your actual executable. For testing, you can simply use `hostname` or `ls`.

I use `ibrain` as the argument for `--partition`. You may not have access to it. Replace it with a partition available in the output of `sinfo`.

```bash
#!/bin/sh
#SBATCH --job-name example_script

#SBATCH --ntasks 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 2G

#SBATCH --partition ibrain
#SBATCH --output %x-%j.out
#SBATCH --error %x-%j.out
#SBATCH --hint=nomultithread


module purge
module load gcc/7.3.1

srun program
```

A few notes on the options:

*   The value given to `--job-name` is used to identify the job when calling `squeue`.
*   A standard Linux console output consists of the output stream and the error stream. When you use `sbatch`, neither will appear on the console. Instead, they will be redirected to the file(s) specified by the `--output` and `--error` options.
*   Scripts have internal variables. Here `%x` will be replaced by the job name, and `%j` will be replaced by the job ID. The job ID is automatically assigned when calling `sbatch` and appears when calling `squeue`.
*   The `--hint=nomultithread` option is discussed further in the [Hyperthreading](#hyperthreading) section. If you don’t care about or understand hyperthreading, just leave it there.

Most long versions of options have an associated variable obtained by:

*   Capitalizing every letter.
*   Replacing the leading `--` by `SLURM_`.
*   Replacing the dashes by underscores.

So, in the example above, the variables `$SLURM_JOB_NAME`, `$SLURM_NTASKS`, `$SLURM_CPUS_PER_TASK` (and more) will be defined right after their corresponding option line.

## Decomposing the script

A submission script is composed of the following parts:

*   A shebang.
*   Options.
*   Comments.
*   Shell commands.
*   Run commands.

### Shebang

The shebang is always the first line of the script. It specifies which shell interpreter to use for shell commands. Replace `sh` with whatever shell you want in the following line.

```bash
#!/bin/sh
```

### Options

Options are lines that start with:

```bash
#SBATCH
```

They have two purposes:

*   The first is to specify resource allocation. In the example script, the combination of `--ntasks` and `--cpus-per-task` asks to allocate a single CPU, and the `--mem` option asks to allocate 2G.

    **Note:** Allocating a lot of resources does not mean that all of them will be used. If you call a single program that does not run in parallel, a single CPU will be used whether you allocate 1 or more CPUs. Be mindful that if you allocate more resources than necessary, those unused resources will not be available to other users. Estimating the number of CPUs is usually not a problem as programs that run in parallel usually have an option specifying the number we want to use. It’s a bit harder to estimate memory. The best approach is to do some testing: either start with low memory and increase it until it runs, or start with high memory and monitor your program by SSHing to the node being used (`squeue` will tell you that) and executing `top`.

    **Other note:** In the current configuration, asking for 1 CPU will actually allocate 2, because Slurm allocates by the core, and cores are hyperthreaded. More details in the [Hyperthreading](#hyperthreading) section.

*   The second purpose is to be passed to the `srun` command. Unless overwritten when calling `srun`, all options given with `#SBATCH` are assumed.

There are many more options:

```bash
man sbatch
```

Any line starting with `#` but not followed by `SBATCH` is a comment. If you want to comment an option, use more than one `#`:

```bash
##SBATCH
```

To avoid confusion between comment and option when using a single `#`, the comment in my example script uses two `#`, even though only one is required.

### Shell commands

Shell commands are used to set up Linux environment variables. They should **not** be preceded by `srun`.

### Run commands

Run commands are your actual computations. They should be preceded by `srun`. The reason is that, as mentioned above, the options given with `#SBATCH` apply to `srun`. In truth, when only one task is given with the `--ntasks` option, omitting `srun` will not change anything. Put it there anyway, for consistency.

## Hyperthreading

Hyperthreading is activated on the nodes, meaning each core has two CPUs. However, this does not double computational power, as using two CPUs of the same core is less efficient than using two CPUs of different cores. With that in mind, here is how Slurm acts (with the number of CPUs you ask for being the product of `--ntasks` and `--cpus-per-task`):

*   Without the `--hint=nomultithread` option, asking for an odd number `N` of CPUs or asking for `N+1` CPUs is the same: Slurm allocates the `N+1` CPUs of `(N+1)/2` cores.
*   With the `--hint=nomultithread` option, asking for `N` CPUs will allocate the `2N` CPUs of `N` cores.

Note that if you like to use the `--mem-per-cpu` option instead of the `--mem` option, the total allocated memory will be based on the number of CPUs actually allocated, not the number of CPUs you asked for. Examples:

*   Without the `--hint=nomultithread` option, the combination of `--ntasks 1 --cpus-per-task 1 --mem-per-cpu 1G` will allocate 2G.
*   The combination of `--ntasks 1 --cpus-per-task 2 --mem-per-cpu 1G --hint=nomultithread` will allocate 4G.

There is really only one valid use of hyperthreading: when you want to ask for **all** the CPUs of a single node. In that case, remove the `--hint=nomultithread` option and allocate everything.

The rest of this documentation assumes we don’t use hyperthreading.

## Running things in parallel

### Calling the same program multiple times in parallel

```bash
#!/bin/sh
#SBATCH --job-name example_script

#SBATCH --ntasks 3
#SBATCH --cpus-per-task 1
#SBATCH --mem 6G

#SBATCH --partition ibrain
#SBATCH --output %x-%j.out
#SBATCH --error %x-%j.out
#SBATCH --hint=nomultithread


module purge
module load gcc/7.3.1

srun program
```

Recall that the options given with `#SBATCH` are passed to `srun`. In this case, a single call to `srun program` would be equivalent to `srun --ntasks 3 program`, which would call `program` three times.

### Several steps in parallel

Here is the full script.

```bash
#!/bin/sh
#SBATCH --job-name example_script

#SBATCH --ntasks 3
#SBATCH --cpus-per-task 1
#SBATCH --mem 6G

#SBATCH --partition ibrain
#SBATCH --output %x-%j.out
#SBATCH --error %x-%j.out
#SBATCH --hint=nomultithread


module purge
module load gcc/7.3.1

srun --ntasks=1 program0 &
srun --ntasks=1 program1 &
srun --ntasks=1 program2
```

Do not forget the `--ntasks 1` on the `srun` lines. If you do, `program0` will be called three times, and because three tasks are being run and you only allocated three, `program1` and `program2` will not be executed at the same time, and will have to wait for the previous tasks to end.

### Arrays

This is useful when you want to use the same programs multiple times with various arguments. The requirement is that the arguments differ only by an integer number. Here is the script.

```bash
#!/bin/sh
#SBATCH --job-name example_script

#SBATCH --array=0-2

#SBATCH --ntasks 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 2G

#SBATCH --partition ibrain
#SBATCH --output %x-%A-%a.out
#SBATCH --error %x-%A-%a.out
#SBATCH --hint=nomultithread


module purge
module load gcc/7.3.1

srun program --arg=$SLURM_ARRAY_TASK_ID
```

Here, the variable `$SLURM_ARRAY_TASK_ID` will take values from 0 to 2. The job ID will be `$SLURM_JOB_ID`, and the array job ID will be `$SLURM_ARRAY_JOB_ID`. The array task ID will be `$SLURM_ARRAY_TASK_ID`.

## Running an interactive session

```bash
srun --pty --job-name interactive --partition ibrain --mem 2G --cpus-per-task 1 bash
```

This will give you a shell on a compute node. The options are the same as for `sbatch`. The `--pty` option is needed to get a pseudo-terminal. The `bash` at the end specifies the shell to run. You can replace it with `sview` to get a graphical interface.

## Running a GUI

```bash
srun --pty --job-name gui --partition ibrain --mem 2G --cpus-per-task 1 --x11 bash
```

This will give you a shell on a compute node with X11 forwarding enabled. The `--x11` option is needed for X11 forwarding. You can then run graphical applications from this shell.

## Custom Module

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

## Conda on a Cluster

### Installing Conda

To install Conda on the cluster, you can download the Miniconda installer and run it. Choose a location in your home directory where you have write permissions.

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

Follow the prompts during installation. When asked about initializing Conda, you can choose `no` if you prefer to activate it manually.

### Using Conda Environments

After installation, you can create and manage Conda environments. This allows you to isolate different projects and their dependencies.

**Create an environment:**

```bash
conda create --name myenv python=3.8
```

**Activate an environment:**

```bash
conda activate myenv
```

**Install packages:**

```bash
conda install numpy pandas
```

**Deactivate an environment:**

```bash
conda deactivate
```

### Conda in Submission Scripts

To use Conda environments in your Slurm submission scripts, you need to activate the environment before running your program. Make sure to load the Conda module if necessary, or ensure Conda is in your PATH.

```bash
#!/bin/sh
#SBATCH --job-name conda_job
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 1
#SBATCH --mem 4G
#SBATCH --partition ibrain
#SBATCH --output %x-%j.out
#SBATCH --error %x-%j.out

# Load Conda if not in PATH
# module load conda

# Activate your Conda environment
source /path/to/your/miniconda3/bin/activate myenv

# Run your Python script or program
srun python my_script.py

# Deactivate environment (optional, but good practice)
conda deactivate
```

## Compression of files

This document will help you to compress your files on HPC as we see we have less space on cluster its better to compress our fastq files and other result files.

### Using `gzip`

`gzip` is a common compression utility. It replaces the original file with a compressed version (`.gz` extension).

**Compress a file:**

```bash
gzip my_file.txt
```

This will create `my_file.txt.gz` and remove `my_file.txt`.

**Decompress a file:**

```bash
gunzip my_file.txt.gz
```

This will restore `my_file.txt` and remove `my_file.txt.gz`.

### Using `tar` with `gzip` (for directories)

To compress entire directories, you typically use `tar` to archive the directory first, and then `gzip` to compress the archive. The `tar` command has options to do both simultaneously.

**Compress a directory:**

```bash
tar -czvf my_directory.tar.gz my_directory/
```

*   `-c`: Create a new archive.
*   `-z`: Compress the archive with `gzip`.
*   `-v`: Verbose output (show progress).
*   `-f`: Specify the archive filename.

**Decompress a directory:**

```bash
tar -xzvf my_directory.tar.gz
```

*   `-x`: Extract files from an archive.
*   `-z`: Decompress with `gzip`.
*   `-v`: Verbose output.
*   `-f`: Specify the archive filename.

### Using `bzip2`

`bzip2` often provides better compression ratios than `gzip`, but is slower.

**Compress a file:**

```bash
bzip2 my_file.txt
```

This creates `my_file.txt.bz2`.

**Decompress a file:**

```bash
bunzip2 my_file.txt.bz2
```

### Using `xz`

`xz` provides even better compression than `bzip2` but is the slowest.

**Compress a file:**

```bash
xz my_file.txt
```

This creates `my_file.txt.xz`.

**Decompress a file:**

```bash
unxz my_file.txt.xz
```

Choose the compression method based on your needs for compression ratio versus speed. For large files like fastq, `gzip` is a common balance. For maximum compression, `xz` is preferred if time is not critical.



<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
