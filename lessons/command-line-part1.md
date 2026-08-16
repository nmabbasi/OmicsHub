---
title: "Basic Navigation"
date: "2025-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Shell Command Basics"
excerpt: "Learn essential Unix/Linux commands for navigating the file system, managing directories, and handling files, which form the foundation of every bioinformatics workflow."
image: "images/shell-commands-part1.png"
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
    <li><strong>Prerequisites:</strong> A terminal on Linux, macOS, or Windows WSL; no prior shell experience is required.</li>
    <li><strong>Objective:</strong> Navigate directories, inspect files, create folders, and use paths safely in a command-line bioinformatics project.</li>
    <li><strong>Expected Output:</strong> A small project directory created from the terminal with documented paths and correctly named files.</li>
  </ul>
  <p class="text-sm text-blue-700"><strong>Suggested route:</strong> use the <a href="start-here.html" class="underline">Bioinformatics Academy Pathway</a> to review any prerequisite stage before continuing.</p>
</div>



## Why the Command Line Matters in Bioinformatics

The command line is like learning to drive a manual transmission car. Sure, automatic is easier to start with, but once you master manual, you have complete control over the machine. In bioinformatics, that control translates to unprecedented power and efficiency.

Here's why every bioinformatician needs command line skills:

- **Processing massive datasets** that would crash graphical programs
- **Automating repetitive tasks** that would take hours manually
- **Connecting tools together** in powerful workflows
- **Working on remote servers** where GUIs aren't available
- **Reproducing analyses** with precise, documented commands

Think of the command line as your Swiss Army knife for biological data: once you master it, you'll wonder how you ever lived without it.

## Getting Started: Your First Commands

### Opening the Terminal

**On macOS**: Press `Cmd + Space`, type "Terminal", and press Enter
**On Linux**: Press `Ctrl + Alt + T` or search for "Terminal"
**On Windows**: Use Windows Subsystem for Linux (WSL) or Git Bash

### Understanding the Prompt

When you open a terminal, you'll see something like:
```bash
username@computer:~$
```

This tells you:
- `username`: Your current user
- `computer`: The machine name
- `~`: Your current location (home directory)
- `$`: You're ready for a command

## Essential Navigation Commands

### Where Am I? (`pwd`)

The `pwd` command (print working directory) tells you exactly where you are in the file system:

```bash
pwd
# Output: /home/username
```

Think of it as your GPS for the file system: you should always know where you are before you start moving around.

### What's Here? (`ls`)

The `ls` command lists the contents of your current directory:

```bash
ls                    # Basic listing
ls -l                 # Long format with details
ls -la                # Include hidden files
ls -lh                # Human-readable file sizes
ls *.fasta            # List only FASTA files
```

**Pro tip**: The `-l` flag shows permissions, file sizes, and modification dates: incredibly useful for troubleshooting.

### Moving Around (`cd`)

The `cd` command (change directory) is your teleportation device:

```bash
cd /path/to/directory  # Go to specific path
cd ..                  # Go up one level
cd ~                   # Go to home directory
cd -                   # Go back to previous directory
cd                     # Also goes to home directory
```

**Navigation shortcuts**:
- `.` means "current directory"
- `..` means "parent directory"
- `~` means "home directory"
- `/` means "root directory"

## File and Directory Operations

### Creating Directories (`mkdir`)

```bash
mkdir project                    # Create single directory
mkdir -p project/data/raw       # Create nested directories
mkdir project_{1..5}            # Create multiple directories
```

The `-p` flag is a lifesaver: it creates parent directories if they don't exist.

### Creating Files (`touch`)

```bash
touch analysis.txt              # Create empty file
touch file1.txt file2.txt      # Create multiple files
touch data/sample_{1..10}.fastq # Create numbered files
```

### Copying Files and Directories (`cp`)

```bash
cp file1.txt file2.txt          # Copy file
cp file1.txt backup/            # Copy to directory
cp -r project/ project_backup/  # Copy directory recursively
cp *.fasta sequences/           # Copy all FASTA files
```

**Important**: Use `-r` (recursive) when copying directories!

### Moving and Renaming (`mv`)

```bash
mv old_name.txt new_name.txt    # Rename file
mv file.txt documents/          # Move file to directory
mv *.fastq raw_data/           # Move all FASTQ files
```

**Caution**: `mv` will overwrite existing files without warning!

### Removing Files and Directories (`rm`)

```bash
rm file.txt                     # Remove file
rm -r directory/                # Remove directory recursively
rm -f file.txt                  # Force removal (no confirmation)
rm *.tmp                        # Remove all temporary files
```

**⚠️ Warning**: There's no "trash" in the command line: deleted files are gone forever!


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-4">Knowledge Check & Assessment</h3>
  <div class="space-y-4">
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">1. Concept Verification</h4>
      <p class="text-gray-600 text-sm">What is the difference between an absolute path, a relative path, the current directory, and the home directory?</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">2. Practical Execution</h4>
      <p class="text-gray-600 text-sm">Create a project directory with raw-data, scripts, and results subdirectories; use pwd, ls, cd, and mkdir to verify it. <strong>Pass Criteria:</strong> Record the command or analysis choice, keep the output, and explain why it answers the stated task.</p>
    </div>
    <div class="bg-white p-4 rounded-lg border border-gray-100 shadow-sm">
      <h4 class="font-bold text-gray-800 mb-2">3. Troubleshooting</h4>
      <p class="text-gray-600 text-sm">If a command reports “No such file or directory,” how will you check the working directory, spelling, spaces, and permissions?</p>
    </div>
  </div>
</div>
