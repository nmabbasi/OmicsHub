#!/usr/bin/env python3
"""Small educational count-matrix workflow: deterministic QC, optional CPM, human review.

Offline planning is a deterministic role simulation, not AI. Optional OpenAI-compatible
planning supplies an allowlisted JSON plan only; it never generates or executes code.
This is not a security sandbox or production/clinical analysis pipeline.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
from pathlib import Path

TOOLS = {"qc", "cpm"}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
GROUP_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
MAX_BYTES, MAX_GENES, MAX_SAMPLES = 2 * 1024 * 1024, 10000, 100

class WorkflowError(ValueError):
    pass

def event(path, role, status, message):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "status": status, "message": message}, sort_keys=True) + "\n")

def input_snapshot(path):
    """Read a bounded snapshot once; use these same bytes for parsing and hashing."""
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise WorkflowError(f"Input exceeds {MAX_BYTES} byte training-data limit: {path.name}")
    return data

def load_inputs(counts_path, metadata_path, snapshots=None):
    try:
        counts_data, metadata_data = snapshots if snapshots is not None else (
            input_snapshot(counts_path), input_snapshot(metadata_path))
        rows = list(csv.reader(io.StringIO(counts_data.decode("utf-8-sig"), newline=""), strict=True))
        meta = list(csv.reader(io.StringIO(metadata_data.decode("utf-8-sig"), newline=""), strict=True))
    except (OSError, UnicodeError, csv.Error) as e:
        raise WorkflowError(f"Could not read valid UTF-8 CSV input: {type(e).__name__}") from None
    if not rows or len(rows[0]) < 3 or rows[0][0] != "gene_id":
        raise WorkflowError("Counts header must be gene_id followed by at least two sample IDs")
    samples = rows[0][1:]
    if len(samples) > MAX_SAMPLES or any(not ID_RE.fullmatch(s) for s in samples) or len(set(samples)) != len(samples):
        raise WorkflowError("Sample IDs must be unique simple IDs (letters, digits, _, ., -); maximum 100")
    if len(rows) < 2 or len(rows) - 1 > MAX_GENES:
        raise WorkflowError("Counts require 1..10000 gene rows")
    genes, gene_order, values = set(), [], []
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(samples) + 1:
            raise WorkflowError(f"Ragged counts row at line {line}")
        gene = row[0]
        if not ID_RE.fullmatch(gene) or gene in genes:
            raise WorkflowError(f"Gene IDs must be unique simple IDs (line {line})")
        genes.add(gene)
        gene_order.append(gene)
        vals = []
        for token in row[1:]:
            if not re.fullmatch(r"[0-9]{1,12}", token, flags=re.ASCII):
                raise WorkflowError(f"Counts must be ASCII nonnegative integer values of at most 12 digits (line {line})")
            vals.append(int(token))
        values.append(vals)
    if not meta or meta[0] != ["sample_id", "group"]:
        raise WorkflowError("Metadata header must be exactly sample_id,group")
    groups = {}
    for line, row in enumerate(meta[1:], 2):
        if len(row) != 2 or not ID_RE.fullmatch(row[0]) or not GROUP_RE.fullmatch(row[1]) or row[0] in groups:
            raise WorkflowError(f"Metadata rows need unique simple sample IDs and simple group labels (line {line})")
        groups[row[0]] = row[1]
    if set(groups) != set(samples):
        raise WorkflowError("Metadata sample IDs must exactly match counts columns (order may differ)")
    return samples, gene_order, values, groups

def strict_json_loads(text):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise WorkflowError("JSON object contains duplicate keys")
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=reject_duplicates)

def validate_plan(obj, task):
    if not isinstance(obj, dict) or set(obj) != {"steps"} or not isinstance(obj["steps"], list):
        raise WorkflowError("Plan schema must contain only {steps: [...]} ")
    steps = obj["steps"]
    if any(not isinstance(x, str) or x not in TOOLS for x in steps) or not 1 <= len(steps) <= 2:
        raise WorkflowError("Plan steps must be one or two allowlisted tools: qc, cpm")
    if len(set(steps)) != len(steps) or steps[0] != "qc" or (len(steps) == 2 and steps[1] != "cpm"):
        raise WorkflowError("Plan steps must be unique and ordered qc before cpm")
    if task == "qc" and steps != ["qc"]:
        raise WorkflowError("qc task requires exactly the qc step")
    if task == "normalize" and steps != ["qc", "cpm"]:
        raise WorkflowError("normalize task requires qc followed by cpm")
    return {"steps": steps}

def openai_plan(task, n_genes, n_samples, model):
    try:
        from openai import OpenAI
    except ImportError:
        raise WorkflowError("Optional planner requires the openai package; install with: python -m pip install openai") from None
    if not os.environ.get("OPENAI_API_KEY"):
        raise WorkflowError("OPENAI_API_KEY is required for --planner openai (value is never displayed)")
    base = os.environ.get("OPENAI_BASE_URL")
    try:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=base, timeout=30.0, max_retries=0) if base else OpenAI(timeout=30.0, max_retries=0)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Return an allowlisted workflow plan only; never provide code."},
                      {"role": "user", "content": json.dumps({"task": task, "dimensions": {"n_genes": n_genes, "n_samples": n_samples}})}],
            response_format={"type": "json_schema", "json_schema": {"name": "workflow_plan", "strict": True, "schema": {"type": "object", "properties": {"steps": {"type": "array", "items": {"type": "string", "enum": ["qc", "cpm"]}, "minItems": 1, "maxItems": 2}}, "required": ["steps"], "additionalProperties": False}}},
        )
        choice = response.choices[0]
        if getattr(choice, "finish_reason", "stop") != "stop":
            raise WorkflowError("Planner did not return a complete plan; no analysis was run")
        message = choice.message
        if getattr(message, "refusal", None):
            raise WorkflowError("Planner refused the request; no analysis was run")
        content = getattr(message, "content", None)
        if not isinstance(content, str):
            raise WorkflowError("Planner returned no plan; no analysis was run")
        return strict_json_loads(content)
    except WorkflowError:
        raise
    except Exception as e:
        # Avoid exception text: compatible SDK/provider exceptions can include credentials or request data.
        raise WorkflowError(f"Planner request failed ({type(e).__name__}); no analysis was run") from None

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()

def demo(path):
    if path.exists(): raise WorkflowError("Demo directory already exists; refusing to overwrite")
    path.mkdir()
    (path / "counts.csv").write_text("gene_id,S1,S2,S3\nGENE1,10,20,0\nGENE2,0,5,0\nGENE3,90,75,0\nGENE4,0,0,0\n", encoding="utf-8")
    (path / "counts_positive.csv").write_text("gene_id,S1,S2,S3\nGENE1,10,20,5\nGENE2,0,5,0\nGENE3,90,75,45\nGENE4,0,0,0\n", encoding="utf-8")
    (path / "metadata.csv").write_text("sample_id,group\nS1,control\nS2,case\nS3,case\n", encoding="utf-8")

def review_outputs(out, samples, genes, matrix, groups, totals, min_library_size, expect_cpm):
    """Independently recompute and verify the written deliverables."""
    expected_header = ["sample_id", "group", "library_size", "detected_genes", "low_library_warning"]
    try:
        with (out / "sample_qc.csv").open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f, strict=True)
            header = next(reader, [])
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as e:
        raise WorkflowError(f"QC review could not read output ({type(e).__name__})") from None
    if header != expected_header or len(rows) != len(samples):
        raise WorkflowError("QC review failed: unexpected header or sample count")
    for j, (row, sample) in enumerate(zip(rows, samples)):
        total = sum(values[j] for values in matrix)
        detected = sum(1 for values in matrix if values[j] > 0)
        expected = [sample, groups[sample], str(total), str(detected), "yes" if total < min_library_size else "no"]
        if row != expected:
            raise WorkflowError(f"QC review failed for sample {sample}")
    cpm_status = "not requested"
    if expect_cpm:
        try:
            with (out / "cpm.csv").open(newline="", encoding="utf-8") as f:
                reader = csv.reader(f, strict=True)
                header = next(reader, [])
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as e:
            raise WorkflowError(f"CPM review could not read output ({type(e).__name__})") from None
        if header != ["gene_id", *samples] or len(rows) != len(genes):
            raise WorkflowError("CPM review failed: unexpected header or gene count")
        columns = [[] for _ in samples]
        # Column-oriented traversal is intentionally distinct from executor writing.
        for gene, input_row, output_row in zip(genes, matrix, rows):
            if len(output_row) != len(samples) + 1 or output_row[0] != gene:
                raise WorkflowError("CPM review failed: gene IDs or row shape differ")
            for j, (token, count) in enumerate(zip(output_row[1:], input_row)):
                try:
                    value = float(token)
                except (ValueError, TypeError):
                    raise WorkflowError("CPM review failed: nonnumeric value") from None
                if not math.isfinite(value) or value < 0 or not math.isclose(value, count / totals[j] * 1_000_000, rel_tol=1e-8, abs_tol=1e-6):
                    raise WorkflowError("CPM review failed: value does not match validated counts")
                columns[j].append(value)
        if any(not math.isclose(sum(column), 1_000_000, rel_tol=0, abs_tol=0.01) for column in columns):
            raise WorkflowError("CPM review failed: column sum differs from one million")
        cpm_status = "passed (finite, nonnegative; each column sums to approximately 1,000,000)"
    warning_samples = [f"{samples[j]} ({totals[j]} counts)" for j in range(len(samples)) if totals[j] < min_library_size]
    warning_text = ", ".join(warning_samples) if warning_samples else "None"
    table_rows = "\n".join(
        f"| {samples[j]} | {groups[samples[j]]} | {totals[j]} | {sum(1 for row in matrix if row[j] > 0)} | {'yes' if totals[j] < min_library_size else 'no'} |"
        for j in range(len(samples)))
    report = ("# Educational count workflow\n\nStatus: **NEEDS_HUMAN_REVIEW**\n\n"
              "| Sample | Group | Count-column total | Detected genes | Low-library warning |\n|---|---|---:|---:|---|\n" + table_rows +
              f"\n\nWarnings (threshold: {min_library_size} counts): {warning_text}. Warnings flag observations for investigation; samples are not removed.\n\n"
              f"CPM review: {cpm_status}.\n\n"
              "This workflow reports the supplied count matrix. Included demo fixtures are synthetic; arbitrary user inputs are not presumed synthetic. This is descriptive QC/CPM only: no differential expression or biological validation is performed. A human must verify identities, units, data suitability, and conclusions.\n")
    (out / "report.md").write_text(report, encoding="utf-8")
    event(out / "events.jsonl", "reviewer", "needs_human_review", "Numerical output checks passed; human review still required")

def run(args):
    counts, metadata, out = map(lambda s: Path(s).resolve(), (args.counts, args.metadata, args.out))
    if not counts.is_file() or not metadata.is_file(): raise WorkflowError("Counts and metadata inputs must both exist as files")
    if out.exists(): raise WorkflowError("Output directory already exists; refusing overwrite")
    if not out.parent.is_dir(): raise WorkflowError("Output parent directory must already exist")
    snapshots = (input_snapshot(counts), input_snapshot(metadata))
    samples, genes, matrix, groups = load_inputs(counts, metadata, snapshots)  # validate before any planner call
    if args.planner == "openai" and not args.model: raise WorkflowError("--model is required with --planner openai")
    out.mkdir()
    log = out / "events.jsonl"
    try:
        event(log, "validator", "ok", "Inputs validated; metadata joined by sample_id")
        totals = [sum(row[j] for row in matrix) for j in range(len(samples))]
        if args.plan:
            if args.plan.stat().st_size > 16 * 1024:
                raise WorkflowError("Plan file exceeds 16384 byte limit")
            plan_obj = strict_json_loads(args.plan.read_text(encoding="utf-8"))
        else:
            plan_obj = (openai_plan(args.task, len(genes), len(samples), args.model) if args.planner == "openai" else
                        {"steps": ["qc", "cpm"] if args.task == "normalize" else ["qc"]})
        plan_obj = validate_plan(plan_obj, args.task)
        (out / "plan.json").write_text(json.dumps(plan_obj, indent=2) + "\n", encoding="utf-8")
        event(log, "planner", "ok", "Validated allowlisted plan" if args.plan or args.planner == "openai" else "Deterministic offline role simulation; not AI")
        origin = None
        if args.planner == "openai" and os.environ.get("OPENAI_BASE_URL"):
            from urllib.parse import urlsplit
            u = urlsplit(os.environ["OPENAI_BASE_URL"]); host = u.hostname or ""
            if u.port is not None: host += f":{u.port}"
            origin = f"{u.scheme}://{host}"
        manifest = {"counts_sha256": hashlib.sha256(snapshots[0]).hexdigest(), "metadata_sha256": hashlib.sha256(snapshots[1]).hexdigest(), "script_sha256": digest(Path(__file__).resolve()),
                    "python": sys.version, "task": args.task, "parameters": {"min_library_size": args.min_library_size},
                    "planner_mode": "plan_file" if args.plan else args.planner, "model": args.model if args.planner == "openai" and not args.plan else None,
                    "provider_endpoint_origin": origin}
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        if args.dry_run:
            event(log, "executor", "plan_only", "Dry run: stopped before executing tools")
            (out / "README.md").write_text("# Workflow plan\n\nStatus: `plan_only`. Inputs were validated and the plan was recorded; no QC or CPM analysis ran.\n", encoding="utf-8")
            return
        event(log, "executor", "started", "Executing allowlisted workflow steps")
        if "qc" in plan_obj["steps"]:
            with (out / "sample_qc.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["sample_id", "group", "library_size", "detected_genes", "low_library_warning"])
                for j, sample in enumerate(samples):
                    detected = sum(1 for row in matrix if row[j] > 0)
                    w.writerow([sample, groups[sample], totals[j], detected, "yes" if totals[j] < args.min_library_size else "no"])
        if "cpm" in plan_obj["steps"]:
            if any(total == 0 for total in totals):
                event(log, "executor", "failed", "CPM cannot run: one or more library totals are zero; QC retained")
                raise WorkflowError("CPM unavailable because at least one sample has zero library size; QC output retained")
            with (out / "cpm.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["gene_id", *samples])
                for gene, row in zip(genes, matrix): w.writerow([gene, *[format(v / totals[j] * 1_000_000, ".10g") for j, v in enumerate(row)]])
        review_outputs(out, samples, genes, matrix, groups, totals, args.min_library_size, "cpm" in plan_obj["steps"])
        event(log, "executor", "completed", "Tools completed")
    except Exception as e:
        # Preserve a failure event whenever output has been created; never claim success.
        try: event(log, "workflow", "failed", str(e) if isinstance(e, WorkflowError) else f"Failure ({type(e).__name__})")
        except OSError: pass
        raise

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--make-demo", metavar="DIR")
    p.add_argument("--counts"); p.add_argument("--metadata"); p.add_argument("--out")
    p.add_argument("--task", choices=["qc", "normalize"], default="qc")
    p.add_argument("--planner", choices=["offline", "openai"], default="offline")
    p.add_argument("--model"); p.add_argument("--plan", type=Path); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--min-library-size", type=int, default=50)
    a = p.parse_args(argv)
    try:
        if a.make_demo:
            if any((a.counts, a.metadata, a.out, a.plan)) or a.planner != "offline": raise WorkflowError("--make-demo cannot be combined with workflow options")
            demo(Path(a.make_demo)); print(f"Created demo inputs in {a.make_demo}"); return 0
        if not (a.counts and a.metadata and a.out): raise WorkflowError("--counts, --metadata, and --out are required")
        if a.plan and a.planner != "offline": raise WorkflowError("--plan is exclusive with --planner openai")
        if a.model and a.planner != "openai": raise WorkflowError("--model is only valid with --planner openai")
        if a.min_library_size < 0: raise WorkflowError("--min-library-size must be nonnegative")
        run(a); print(f"Workflow outputs written to {a.out}"); return 0
    except (WorkflowError, OSError, json.JSONDecodeError, UnicodeError) as e:
        print(f"Error: {e}", file=sys.stderr); return 2

if __name__ == "__main__":
    sys.exit(main())
