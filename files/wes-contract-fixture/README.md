# Invented WES table-contract fixture

`filter_status_ad_dp.vcf` contains four invented records on `chrToy`. It is not NA12878 sequencing data, a real reference, a truth set or a clinical example. The WES tutorial reuses its example filenames only to test the displayed filtering and VAF commands.

The records distinguish PASS, an assigned failing filter, an unreviewed `.` filter, and a PASS multiallelic call. The biallelic PASS call deliberately has FORMAT/DP different from the sum of AD. Expected behavior is two PASS output rows, VAF `0.4` for the biallelic record, and `NA` for the multiallelic record.

Run the contract checks from the repository root:

```bash
python3 tests/test_priority_wes.py -v
```

The bcftools integration checks run when `bcftools` is on `PATH`; otherwise they report a skip. The Bash failure-path test uses named stubs, not real BWA or samtools. Neither the fixture nor those tests run GATK, call variants or validate a WES workflow scientifically. No human reference or reads are required.
