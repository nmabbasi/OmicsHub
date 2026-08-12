---
title: "Command Line Mastery: A Detailed Guide for Bioinformatics Beginners - Part 3"
date: "2025-08-14"
author: "Shell2R Team"
category: "Shell Commands"
excerpt: "Part 3 of the Command Line Mastery: A Detailed Guide for Bioinformatics Beginners series."
image: "images/command-line-terminal.png"
---

## Advanced Text Processing with `awk`

`awk` is a powerful programming language built into Unix systems:

### Basic `awk` Patterns

```bash
awk '{print $1}' file.txt        # Print first column
awk '{print $1, $3}' file.txt    # Print columns 1 and 3
awk '{print NF}' file.txt        # Print number of fields
awk '{print NR, $0}' file.txt    # Print line numbers
```

### Conditional Processing

```bash
awk '$3 > 50' data.txt           # Print lines where column 3 > 50
awk '$1 == "gene"' data.txt      # Print lines where column 1 equals "gene"
awk 'length($0) > 80' file.txt   # Print lines longer than 80 characters
```

### Mathematical Operations

```bash
awk '{sum += $2} END {print sum}' numbers.txt    # Sum column 2
awk '{print $1, $2*2}' data.txt                 # Multiply column 2 by 2
awk '{avg = ($2+$3)/2; print $1, avg}' data.txt # Calculate average
```

## Pipes and Redirection: Connecting the Pieces

### Pipes (`|`)

Pipes connect the output of one command to the input of another:

```bash
cat sequences.fasta | grep ">" | wc -l          # Count sequences
ls -l | grep "\.fastq" | wc -l                  # Count FASTQ files
sort data.txt | uniq -c | sort -nr              # Sort, count, sort by count
```

### Redirection

#### Output redirection (`>` and `>>`)
```bash
ls > file_list.txt               # Write output to file (overwrite)
ls >> file_list.txt              # Append output to file
grep "error" log.txt > errors.txt # Save errors to file
```

#### Input redirection (`<`)
```bash
sort < unsorted.txt              # Use file as input
wc -l < sequences.fasta          # Count lines from file
```

### Combining Commands

```bash
# Complex bioinformatics pipeline
cat *.fastq | \
grep -A 1 "^@" | \
grep -v "^@" | \
grep -v "^--" | \
awk 'length($0) > 50' | \
wc -l
```

## File Permissions and Ownership

### Understanding Permissions

When you run `ls -l`, you see something like:
```
-rw-r--r-- 1 user group 1024 Jan 15 10:30 file.txt
```

This breaks down as:
- `-`: File type (- for file, d for directory)
- `rw-r--r--`: Permissions (owner, group, others)
- `1`: Number of links
- `user`: Owner
- `group`: Group
- `1024`: File size
- `Jan 15 10:30`: Last modified
- `file.txt`: Filename

### Permission Types

- `r` (read): Can view file contents
- `w` (write): Can modify file
- `x` (execute): Can run file as program

### Changing Permissions (`chmod`)

```bash
chmod +x script.sh               # Make script executable
chmod 755 script.sh              # rwxr-xr-x
chmod 644 data.txt               # rw-r--r--
chmod -R 755 directory/          # Apply to directory recursively
```

## Process Management

### Viewing Running Processes

```bash
ps                               # Show your processes
ps aux                           # Show all processes
top                              # Interactive process viewer
htop                             # Better interactive viewer (if installed)
```

### Background Processes

```bash
long_command &                   # Run in background
nohup long_command &             # Run in background, ignore hangup
jobs                             # Show background jobs
fg %1                            # Bring job 1 to foreground
bg %1                            # Send job 1 to background
```

### Killing Processes

```bash
kill PID                         # Kill process by ID
kill -9 PID                      # Force kill process
killall process_name             # Kill all processes by name
```

## Working with Compressed Files

### Compression and Decompression

```bash
gzip file.txt                    # Compress file
gunzip file.txt.gz               # Decompress file
tar -czf archive.tar.gz files/   # Create compressed archive
tar -xzf archive.tar.gz          # Extract compressed archive
```

### Working with Compressed Files Directly

```bash
zcat file.txt.gz | head          # View compressed file
zgrep "pattern" file.txt.gz      # Search in compressed file
zless file.txt.gz                # View compressed file interactively
```

## Environment Variables and PATH

### Viewing Environment Variables

```bash
echo $HOME                       # Show home directory
echo $PATH                       # Show executable search path
env                              # Show all environment variables
```

### Setting Environment Variables

```bash
export MYVAR="value"             # Set variable for session
echo 'export MYVAR="value"' >> ~/.bashrc  # Set permanently
```

## Command History and Shortcuts

### History Commands

```bash
history                          # Show command history
!123                             # Run command 123 from history
!!                               # Run last command
!grep                            # Run last command starting with grep
```

### Keyboard Shortcuts

- `Ctrl+C`: Cancel current command
- `Ctrl+Z`: Suspend current command
- `Ctrl+A`: Go to beginning of line
- `Ctrl+E`: Go to end of line
- `Ctrl+U`: Clear line before cursor
- `Ctrl+K`: Clear line after cursor
- `Tab`: Auto-complete
- `↑/↓`: Navigate command history

## Best Practices for Bioinformatics

### 1. **Organize Your Files**
```bash
project/
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
├── results/
└── docs/
```

### 2. **Use Descriptive Filenames**
```bash
# Good
sample_01_quality_filtered.fastq
alignment_results_2024_01_15.sam

# Bad
file1.txt
output.txt
```

### 3. **Document Your Commands**
```bash
# Keep a log of important commands
echo "$(date): Started quality control" >> analysis.log
fastqc *.fastq >> analysis.log 2>&1
```

### 4. **Test Commands on Small Datasets**
```bash
# Test on first 1000 lines
head -n 1000 large_file.fastq | your_command
```

### 5. **Use Version Control**
```bash
git init                         # Initialize repository
git add script.sh                # Add file to staging
git commit -m "Added QC script"  # Commit changes
```

## Troubleshooting Common Issues

### Command Not Found
```bash
which command_name               # Check if command exists
echo $PATH                       # Check search path
```

### Permission Denied
```bash
ls -l file.txt                   # Check permissions
chmod +x script.sh               # Make executable
```

### File Not Found
```bash
ls -la                           # Check if file exists
pwd                              # Verify current directory
```

### Out of Disk Space
```bash
df -h                            # Check disk usage
du -sh *                         # Check directory sizes
```

## Building Your First Bioinformatics Pipeline

Let's put it all together with a simple quality control pipeline:

```bash
#!/bin/bash

# Quality control pipeline for FASTQ files
# Usage: ./qc_pipeline.sh input_directory output_directory

INPUT_DIR=$1
OUTPUT_DIR=$2

# Create output directory
mkdir -p $OUTPUT_DIR

# Process each FASTQ file
for file in $INPUT_DIR/*.fastq; do
    filename=$(basename "$file" .fastq)
    
    # Count reads
    read_count=$(wc -l < "$file" | awk '{print $1/4}')
    echo "$filename: $read_count reads"
    
    # Check for adapters
    adapter_count=$(grep -c "AGATCGGAAGAG" "$file")
    echo "$filename: $adapter_count potential adapter sequences"
    
    # Calculate average read length
    avg_length=$(awk 'NR%4==2{sum+=length($0); count++} END{print sum/count}' "$file")
    echo "$filename: Average read length = $avg_length"
    
    # Save summary
    echo -e "$filename\t$read_count\t$adapter_count\t$avg_length" >> $OUTPUT_DIR/summary.txt
done

echo "Quality control complete. Results in $OUTPUT_DIR/summary.txt"
```

## Advanced Topics to Explore Next

Once you're comfortable with these basics, consider learning:

- **Regular expressions**: Pattern matching on steroids
- **Shell scripting**: Automating complex workflows
- **SSH and remote computing**: Working on clusters
- **Package managers**: Installing bioinformatics software
- **Workflow managers**: Snakemake, Nextflow, CWL

## Conclusion

Mastering the command line is like learning a new language — it takes practice, but once you're fluent, it opens up a world of possibilities. The commands and concepts covered in this tutorial form the foundation of computational biology work.

Remember:
- **Practice regularly** — Use the command line for daily tasks
- **Start simple** — Master basic commands before moving to complex pipelines
- **Read the manual** — Use `man command_name` to learn more about any command
- **Don't be afraid to experiment** — The best way to learn is by doing

The command line is your gateway to powerful bioinformatics analysis. With these skills, you're ready to tackle real biological datasets and start uncovering the secrets hidden in genomic data.

## Next Steps

Ready to level up your bioinformatics skills? Check out our other tutorials:

1. **[Package Management with Conda](conda-mamba-installation-guide.md)** — Learn to install and manage bioinformatics software
2. **[Single-cell RNA-seq Analysis](single-cell-rnaseq-introduction.md)** — Apply your command line skills to cutting-edge analysis
3. **[Introduction to Bioinformatics](introduction-to-bioinformatics.md)** — Understand the bigger picture

---

*Questions about command line usage? Need help with a specific bioinformatics task? [Contact us](contact.html) — we're here to help you master computational biology!*

