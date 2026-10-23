# Invented text-processing inputs

These five tiny inputs were created solely for the Command-line Text Processing lesson. They are not research data, patient data, observed read counts or a biological benchmark.

- `data.tsv` and `genes_of_interest.txt` reproduce the lesson's four-row table and matching-ID list.
- `sequences.fasta` has three records and 25 bases in total. `gene_B_wrapped` deliberately splits the forward-strand `ATGCG` motif across two lines.
- `reads.fastq` has two four-line records, each with eight bases and eight quality characters.
- `malformed.fastq` deliberately has four bases but only three quality characters. A record-aware conversion must reject this input; a plausible-looking AWK output is the counterexample, not evidence of valid input.

The lesson displays the complete creation commands and links the same bytes for download. The tests run those displayed commands and compare their generated inputs against these files.

Verified locally under Ubuntu Linux x86_64 with Bash 5.2.21, mawk 1.3.4 (20240123), GNU grep 3.11, GNU Coreutils 9.4, and SeqKit 2.14.0. The bounded checks cover table filtering, ID matching, the wrapped motif, conversion of the valid fixture, rejection of the malformed fixture and temporary-output cleanup. Other operating systems, biological data and large-file performance were not tested.

Primary command reference: https://bioinf.shenwei.me/seqkit/usage/
