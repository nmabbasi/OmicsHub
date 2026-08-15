---
title: "Text Processing"
date: "2025-08-14"
author: "Nasir Mahmood Abbasi, PhD"
category: "Shell Command Basics"
excerpt: "Master grep, sed, cut, and sort to filter, extract, and reshape biological data files directly from the command line."
image: "images/shell-commands-part2.png"
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



## Text Processing: The Bioinformatician's Superpower

### Viewing File Contents

#### `cat` - Display entire file
```bash
cat sequences.fasta             # Show entire file
cat file1.txt file2.txt        # Concatenate files
```

#### `head` - Show beginning of file
```bash
head sequences.fasta            # First 10 lines
head -n 20 sequences.fasta      # First 20 lines
head -n 5 *.txt                # First 5 lines of all text files
```

#### `tail` - Show end of file
```bash
tail sequences.fasta            # Last 10 lines
tail -n 20 sequences.fasta      # Last 20 lines
tail -f logfile.txt            # Follow file as it grows
```

#### `less` - Interactive file viewer
```bash
less sequences.fasta            # View file interactively
```

**Navigation in `less`**:
- `Space`: Next page
- `b`: Previous page
- `/pattern`: Search forward
- `q`: Quit

### Searching and Filtering (`grep`)

`grep` is your text-searching superhero:

```bash
grep "ATCG" sequences.fasta      # Find lines containing ATCG
grep -c ">" sequences.fasta      # Count sequence headers
grep -v ">" sequences.fasta      # Show lines NOT containing >
grep -i "error" logfile.txt      # Case-insensitive search
grep -n "pattern" file.txt       # Show line numbers
grep -A 3 -B 3 "pattern" file    # Show 3 lines after and before
```

### Counting Things (`wc`)

```bash
wc file.txt                      # Lines, words, characters
wc -l file.txt                   # Count lines only
wc -w file.txt                   # Count words only
wc -c file.txt                   # Count characters only
```

### Sorting and Uniqueness

#### `sort` - Sort lines
```bash
sort file.txt                    # Sort alphabetically
sort -n numbers.txt              # Sort numerically
sort -r file.txt                 # Reverse sort
sort -k 2 data.txt              # Sort by second column
```

#### `uniq` - Remove duplicates
```bash
uniq file.txt                    # Remove adjacent duplicates
sort file.txt | uniq             # Remove all duplicates
uniq -c file.txt                 # Count occurrences
```

## Bioinformatics-Specific Examples

### Working with FASTA Files

#### Count sequences in a FASTA file
```bash
grep -c ">" sequences.fasta
```

#### Extract sequence headers
```bash
grep ">" sequences.fasta | head -10
```

#### Remove the ">" from headers
```bash
grep ">" sequences.fasta | sed 's/>//'
```

#### Find sequences with specific patterns
```bash
grep -A 1 ">" sequences.fasta | grep "ATGC"
```

### Working with FASTQ Files

#### Count reads in a FASTQ file
```bash
wc -l reads.fastq | awk '{print $1/4}'
```

#### Extract quality scores
```bash
awk 'NR%4==0' reads.fastq | head -10
```

#### Convert FASTQ to FASTA
```bash
awk 'NR%4==1{printf ">%s\n", substr($0,2)} NR%4==2{print}' reads.fastq > sequences.fasta
```

### Working with Tab-Delimited Files

#### View first few columns
```bash
cut -f 1,2,3 data.tsv | head
```

#### Sort by a specific column
```bash
sort -k 3 -n data.tsv           # Sort by 3rd column numerically
```

#### Filter rows based on column values
```bash
awk '$3 > 100' data.tsv         # Show rows where column 3 > 100
```


<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
