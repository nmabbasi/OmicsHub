---
title: "Command Line for Bioinformatics: Text Processing and Data Manipulation"
date: "2025-08-14"
author: "OmicsHub Team"
category: "Shell Commands"
excerpt: "Master grep, sed, cut, and sort to filter, extract, and reshape biological data files directly from the command line."
image: "images/command-line-terminal.png"
---

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
