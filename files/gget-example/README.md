# An observed ACE2 retrieval with gget

This directory records a real execution of `gget info ENSG00000130234` and `gget seq --translate ENSG00000130234` on 23 October 2026 UTC. Both returned exit status zero in the compatible environment below. This is a retrieval example, not a new biological analysis.

## Reproduce in a new environment

Download `run_retrieval.py` and `requirements-direct.txt`, then use Python 3.12 in a new folder:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-direct.txt
python run_retrieval.py --output retrieval-results
```

The direct pins exercised were gget 0.28.6, NumPy 1.26.4 and pandas 2.2.3 on Linux / Python 3.12.3. `observed/requirements.txt` records the full installed distributions for this run; it is an environment snapshot, not a cross-platform lockfile or a guarantee that upstream services will return the same content.

The runner requires a fresh output directory, caps each external command at 120 seconds, saves raw stdout/stderr and SHA256 fingerprints, and records start/end timestamps, exact arguments and exit status in `manifest.json`. It returns nonzero for a failed/empty/malformed retrieval. Do not interpret an empty file or an exit-zero result alone as verified biological evidence.

## What actually came back

- `observed/ACE2_info.json`: the queried stable identifier maps to `ENSG00000130234.15`, species `homo_sapiens`, gene name `ACE2`, assembly `GRCh38`, sequence region `X`, strand `-1`, and canonical transcript field `ENST00000252519.8` in the returned record.
- `observed/ACE2_protein.fasta`: the returned header names transcript `ENST00000252519`, UniProt `Q9BYF1`, and sequence length 805; the saved sequence contains 805 amino-acid letters.
- `observed/manifest.json`: successful command statuses, UTC times and hashes of the raw files.

A gene, transcript and protein accession are different identifiers. The FASTA header links this returned sequence to a transcript and UniProt record; the header alone is not a general rule for which isoform gget will select on a future query. Coordinates are meaningful only with the returned assembly and coordinate convention. The gene response does not supply an explicit annotation release field, so this example does not invent one. Missing PDB/NCBI fields in this response are not proof that no corresponding records exist.

## A failure caught during preparation

Installing gget 0.28.6 with unconstrained current dependencies selected NumPy 2.5.4 and pandas 3.1.0. Both CLI commands failed with an `np.NaN` compatibility error. The successful run used the explicit NumPy/pandas pins above. This is why the lesson now supplies tested constraints instead of pinning only gget. The original failure was not relabeled as a successful result, and the successful raw responses were not hand-authored.

For changing APIs and documentation, consult the [official gget project](https://github.com/scverse/gget), [Ensembl](https://www.ensembl.org/) and [UniProt Q9BYF1](https://www.uniprot.org/uniprotkb/Q9BYF1/entry). gget's translated sequence source is UniProt. This saved snapshot does not freeze the remote databases or establish functional/clinical validity.
