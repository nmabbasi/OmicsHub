#!/usr/bin/env python3
"""Retrieve an advertised AlphaFold DB model, then report CA B-factor confidence.

No third-party packages. Fetching is explicit; offline PDB analysis is supported.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://alphafold.ebi.ac.uk/api/prediction/{}"
USER_AGENT = "Mozilla/5.0 (compatible; OmicsHubTeachingClient/1.0; +https://theomicshub.com)"
MAX_BYTES = 10 * 1024 * 1024
ACCESSION = re.compile(r"^[A-Z0-9]{6,10}$")


def parse_ca(text):
    """Return one CA observation per chain/residue key, preferring blank/A altloc."""
    chosen = {}
    seen_altlocs = set()
    model_records = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.startswith("MODEL "):
            model_records += 1
            if model_records > 1:
                raise ValueError("multiple MODEL records are unsupported; this reader accepts one model")
        if not line.startswith("ATOM  "):
            continue
        if line[12:16].strip() != "CA":
            continue
        if len(line) < 66:
            raise ValueError(f"line {line_no}: CA ATOM record is too short")
        alt = line[16:17]
        chain = line[21:22].strip() or "_"
        resid = line[22:26].strip()
        icode = line[26:27].strip()
        if not resid or not re.fullmatch(r"[+-]?\d+", resid):
            raise ValueError(f"line {line_no}: CA residue number must be a valid integer")
        row_key = (chain, resid, icode, alt)
        if row_key in seen_altlocs:
            raise ValueError(f"line {line_no}: duplicate CA record for chain/residue/insertion/altloc")
        seen_altlocs.add(row_key)
        if alt not in (" ", "A"):
            continue
        try:
            value = float(line[60:66])
        except ValueError as exc:
            raise ValueError(f"line {line_no}: invalid CA B-factor") from exc
        if not math.isfinite(value) or not 0.0 <= value <= 100.0:
            raise ValueError(f"line {line_no}: CA B-factor must be finite and in [0,100]")
        key = (chain, resid, icode)
        # Distinct alternate conformers are legitimate; repeated same-alt rows are not.
        # If both blank and A alternate conformers occur, blank is preferred.
        priority = 0 if alt == " " else 1
        if key not in chosen:
            chosen[key] = (priority, value, {alt})
        else:
            chosen[key][2].add(alt)
            if priority < chosen[key][0]:
                chosen[key] = (priority, value, chosen[key][2])
    if not chosen:
        raise ValueError("no alpha-carbon ATOM records with usable B-factors found")
    ordered = sorted(chosen.items(), key=lambda item: (item[0][0], int(item[0][1]), item[0][2]))
    return [{"chain": k[0], "residue_id": k[1], "insertion_code": k[2], "bfactor": v[1]}
            for k, v in ordered]


def summarize(rows, alphafold_verified=False):
    vals = [r["bfactor"] for r in rows]
    return {"ca_residue_count": len(rows), "chains": sorted({r["chain"] for r in rows}),
            "mean_ca_bfactor": round(sum(vals) / len(vals), 3),
            "min_ca_bfactor": min(vals), "max_ca_bfactor": max(vals),
            "interpretation": (("Only for a verified AlphaFold-predicted file, B-factor is pLDDT (0-100); higher indicates greater local model confidence. "
                                "Experimental B-factors are not pLDDT. " if alphafold_verified else
                                "B-factors are reported as provided; this input's provenance was not verified, and experimental B-factors are not pLDDT. ")
                               + "This summary is not evidence of function, binding, stability, or experimental accuracy.")}


def safe_read(response, limit=MAX_BYTES):
    data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"download exceeds {limit} byte limit")
    return data


def write_new(path, data):
    # exclusive create prevents silently replacing prior user results
    with open(path, "xb") as f:
        f.write(data)


def fetch(accession, outdir):
    if not ACCESSION.fullmatch(accession):
        raise ValueError("accession must be 6-10 uppercase alphanumeric characters")
    outdir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(API.format(accession), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        api_bytes = safe_read(response)
    payload = json.loads(api_bytes)
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"AlphaFold DB returned no model for {accession}")
    if any(not isinstance(m, dict) for m in payload):
        raise ValueError("AlphaFold DB returned invalid JSON entries (expected objects)")
    matches = [m for m in payload if m.get("uniprotAccession") == accession and isinstance(m.get("pdbUrl"), str)]
    if not matches:
        raise ValueError("API response has no matching entry with an advertised PDB URL")
    if len(matches) > 1:
        raise ValueError("AlphaFold DB returned multiple matching model/fragment entries; select a specific entry via the official DB, or use offline analyze on the desired PDB")
    model = matches[0]
    from urllib.parse import urlparse
    parsed = urlparse(model["pdbUrl"])
    if parsed.scheme != "https" or parsed.hostname not in {"alphafold.ebi.ac.uk", "www.alphafold.ebi.ac.uk"}:
        raise ValueError("refusing PDB URL outside the official HTTPS AlphaFold DB host")
    with urllib.request.urlopen(urllib.request.Request(model["pdbUrl"], headers={"User-Agent": USER_AGENT}), timeout=30) as response:
        pdb = safe_read(response)
    text = pdb.decode("ascii", errors="strict")
    rows = parse_ca(text)
    stem = f"{accession}_alphafold"
    write_new(outdir / f"{stem}_api.json", json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n")
    write_new(outdir / f"{stem}.pdb", pdb)
    result = {"accession": accession, "description": model.get("uniprotDescription"),
              "model_id": model.get("entryId"), "model_version": model.get("latestVersion"),
              "pdb_url": model["pdbUrl"], "pdb_sha256": hashlib.sha256(pdb).hexdigest(), **summarize(rows, alphafold_verified=True),
              "residues": rows}
    write_new(outdir / f"{stem}_qc.json", (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({k: v for k, v in result.items() if k != "residues"}, indent=2))


def analyze(pdb_path, output):
    with pdb_path.open("rb") as f:
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"input exceeds {MAX_BYTES} byte limit")
    rows = parse_ca(data.decode("ascii", errors="strict"))
    result = {"input": pdb_path.name, "sha256": hashlib.sha256(data).hexdigest(), **summarize(rows), "residues": rows}
    encoded = (json.dumps(result, indent=2) + "\n").encode()
    if output:
        write_new(output, encoded)
    else:
        sys.stdout.write(encoded.decode())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch", help="explicitly query public AFDB API and download its advertised PDB")
    f.add_argument("accession"); f.add_argument("--outdir", type=Path, required=True)
    a = sub.add_parser("analyze", help="offline parse existing PDB; output is stdout unless --out")
    a.add_argument("pdb", type=Path); a.add_argument("--out", type=Path)
    args = p.parse_args()
    try:
        fetch(args.accession, args.outdir) if args.command == "fetch" else analyze(args.pdb, args.out)
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        p.exit(2, f"error: {exc}\n")

if __name__ == "__main__":
    main()
