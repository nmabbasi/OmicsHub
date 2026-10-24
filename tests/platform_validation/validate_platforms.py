#!/usr/bin/env python3
"""Execute selected published beginner lesson code on the active native OS.

This harness uses only Python's standard library to extract HTML code blocks,
then runs the displayed Python and R code in temporary projects. Dependencies
are provisioned by the GitHub Actions workflow; no website outputs are written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from html.parser import HTMLParser
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen
import unittest

ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = ROOT / "tutorials"
VISUAL_FIXTURES = ROOT / "files/tutorial-examples/data-visualization-fundamentals"
PBMC3K_URL = "https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz"
PBMC3K_BYTES = 7_621_991
PBMC3K_SHA256 = "847d6ebd9a1ec9a768f2be7e40ca42cbfe75ebeb6d76a4c24167041699dc28b5"


class PreBlockParser(HTMLParser):
    """Collect complete rendered text in each PRE, retaining its optional id."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str | None, str]] = []
        self._parts: list[str] | None = None
        self._identifier: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "pre":
            self._parts = []
            self._identifier = dict(attrs).get("id")

    def handle_data(self, data: str) -> None:
        if self._parts is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "pre" and self._parts is not None:
            self.blocks.append((self._identifier, "".join(self._parts)))
            self._parts = None
            self._identifier = None


def html_blocks(relative: str) -> list[tuple[str | None, str]]:
    parser = PreBlockParser()
    parser.feed((ROOT / relative).read_text(encoding="utf-8"))
    return parser.blocks


def block(relative: str, *, index: int | None = None,
          identifier: str | None = None, needles: tuple[str, ...] = ()) -> str:
    blocks = html_blocks(relative)
    if index is not None:
        try:
            found = blocks[index][1]
        except IndexError as exc:
            raise AssertionError(f"{relative}: missing PRE block {index}") from exc
        if not all(needle in found for needle in needles):
            raise AssertionError(f"{relative}: PRE block {index} no longer matches {needles}")
        return found
    matches = [source for name, source in blocks
               if (identifier is None or name == identifier)
               and all(needle in source for needle in needles)]
    if len(matches) != 1:
        raise AssertionError(
            f"{relative}: expected one code block id={identifier!r} containing {needles}, got {len(matches)}"
        )
    return matches[0]


def heredoc(source: str, filename: str) -> str:
    """Extract a displayed cat > filename <<'EOF' teaching fixture."""
    pattern = rf"cat\s+>\s+{re.escape(filename)}\s+<<'EOF'\s*\n(.*?)\nEOF"
    match = re.search(pattern, source, re.S)
    if not match:
        raise AssertionError(f"Could not extract published {filename} heredoc")
    return match.group(1) + "\n"


def printf_fixture(source: str, filename: str) -> str:
    """Extract the simple printf "...\\n" > file fixture used by the lesson."""
    pattern = rf'printf\s+"((?:[^"\\]|\\.)*)"\s*>\s*{re.escape(filename)}'
    match = re.search(pattern, source)
    if not match:
        raise AssertionError(f"Could not extract published printf fixture {filename}")
    return match.group(1).replace("\\n", "\n")


def run_script(executable: str, source: str, name: str, cwd: Path,
               *arguments: str, env: dict[str, str] | None = None,
               timeout: int = 180) -> subprocess.CompletedProcess[str]:
    script = cwd / name
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(source, encoding="utf-8", newline="\n")
    return subprocess.run(
        [executable, str(script), *arguments], cwd=cwd, env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, check=False,
    )


def require_rscript() -> str:
    executable = shutil.which("Rscript")
    if not executable:
        raise AssertionError("Rscript is required; CI installs R release before running this harness")
    return executable


def r_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("TZ", "UTC")
    return env


def assert_png_white_900x600(path: Path) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise AssertionError("Pillow is installed by the cross-platform workflow") from exc
    with Image.open(path) as image:
        if image.format != "PNG" or image.size != (900, 600):
            raise AssertionError(f"Unexpected image format/size: {image.format} {image.size}")
        rgba = image.convert("RGBA")
        if rgba.getchannel("A").getextrema() != (255, 255):
            raise AssertionError("Tidyverse plot is not fully opaque")
        for point in ((0, 0), (899, 0), (0, 599), (899, 599)):
            if rgba.getpixel(point) != (255, 255, 255, 255):
                raise AssertionError(f"PNG corner {point} is not opaque white: {rgba.getpixel(point)}")


def write_tidyverse_project(parent: Path) -> Path:
    lesson = "tutorials/r-tidyverse-fundamentals.html"
    setup = block(lesson, identifier="tidyverse-fixture-setup")
    project = parent / "tidy-qc"
    for relative in ("data/raw", "data/metadata", "scripts", "results"):
        (project / relative).mkdir(parents=True, exist_ok=True)
    (project / ".here").write_text("", encoding="utf-8")
    (project / "data/raw/gene_counts.tsv").write_text(
        heredoc(setup, "data/raw/gene_counts.tsv"), encoding="utf-8", newline="\n")
    (project / "data/metadata/samples.tsv").write_text(
        heredoc(setup, "data/metadata/samples.tsv"), encoding="utf-8", newline="\n")
    workflow = block(lesson, identifier="tidyverse-workflow", needles=("here::i_am", "ggsave"))
    (project / "scripts/01-tidy-qc.R").write_text(workflow, encoding="utf-8", newline="\n")
    return project


def read_delimited(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def prepare_stats_project(directory: Path) -> tuple[str, str, str, str, str]:
    lesson = "tutorials/statistics-for-bioinformatics.html"
    setup = block(lesson, index=0, needles=("data/control.csv", "data/treated.csv"))
    control = printf_fixture(setup, "data/control.csv")
    treated = printf_fixture(setup, "data/treated.csv")
    pvalue_setup = block(lesson, index=5, needles=("pvalues_all_features.txt",))
    pvalues = printf_fixture(pvalue_setup, "pvalues_all_features.txt")
    (directory / "data").mkdir()
    (directory / "results").mkdir()
    (directory / "data/control.csv").write_text(control, encoding="utf-8", newline="\n")
    (directory / "data/treated.csv").write_text(treated, encoding="utf-8", newline="\n")
    python = block(lesson, index=2, needles=("from scipy import stats", "comparison.csv"))
    r = block(lesson, index=3, needles=("t.test(trt, ctrl", "comparison_R.csv"))
    return python, r, control, treated, pvalues


def prepare_design_project(directory: Path) -> tuple[str, str, str, str, str, str]:
    lesson = "tutorials/experimental-design-batch-effects.html"
    metadata_setup = block(lesson, index=1, needles=("cat > metadata.csv",))
    counts_setup = block(lesson, index=6, needles=("cat > counts.csv",))
    metadata = heredoc(metadata_setup, "metadata.csv")
    counts = heredoc(counts_setup, "counts.csv")
    (directory / "metadata.csv").write_text(metadata, encoding="utf-8", newline="\n")
    (directory / "counts.csv").write_text(counts, encoding="utf-8", newline="\n")
    return (
        block(lesson, index=3, needles=("import pandas as pd", "metadata.validated.csv")),
        block(lesson, index=4, needles=("meta <- read.csv", "metadata.validated.csv")),
        block(lesson, index=7, needles=("prcomp(", "pca_coordinates.csv")),
        block(lesson, index=9, needles=("np.linalg.svd", "pca_coordinates.csv")),
        metadata, counts,
    )


def stage_pbmc3k_archive(project: Path) -> dict[str, object]:
    """Download and stage the exact official 10x archive using only Python."""
    root = project / "data/pbmc3k"
    root.mkdir(parents=True)
    archive_path = root / "pbmc3k_filtered_gene_bc_matrices.tar.gz"
    request = Request(PBMC3K_URL, headers={"User-Agent": "OmicsHub-platform-validation/1.0"})
    digest = hashlib.sha256()
    size = 0
    with urlopen(request, timeout=90) as response, archive_path.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            output.write(chunk)
    actual_hash = digest.hexdigest()
    evidence = {"url": PBMC3K_URL, "bytes": size, "sha256": actual_hash,
                "expected_bytes": PBMC3K_BYTES, "expected_sha256": PBMC3K_SHA256}
    print("PBMC3K_ARCHIVE_JSON " + json.dumps(evidence, sort_keys=True, separators=(",", ":")), flush=True)
    if size != PBMC3K_BYTES or actual_hash != PBMC3K_SHA256:
        raise AssertionError(f"Official PBMC3k archive size/hash mismatch: {evidence}")

    extraction = root / "archive-extract"
    extraction.mkdir()
    expected_prefix = "filtered_gene_bc_matrices/hg19"
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            parts = Path(member.name).parts
            if (member.name.startswith("/") or ".." in parts
                    or not (member.name == expected_prefix
                            or member.name.startswith(expected_prefix + "/")
                            or member.name in ("filtered_gene_bc_matrices",))
                    or member.issym() or member.islnk() or member.isdev()):
                raise AssertionError(f"Unexpected unsafe path in official archive: {member.name!r}")
        archive.extractall(path=extraction, members=members, filter="data")
    legacy = extraction / expected_prefix
    for filename in ("matrix.mtx", "barcodes.tsv", "genes.tsv"):
        if not (legacy / filename).is_file():
            raise AssertionError(f"Official archive lacks expected legacy 10x file: {filename}")
    target = root / "filtered_feature_bc_matrix"
    shutil.move(str(legacy), str(target))
    shutil.rmtree(extraction)
    return evidence


class PublishedPythonFundamentalsTests(unittest.TestCase):
    def test_exact_fasta_script_reads_published_fixture_and_writes_expected_csv(self) -> None:
        lesson = "tutorials/python-fundamentals-bioinformatics.html"
        setup = block(lesson, index=0, needles=("data/raw/example.fasta",))
        script = block(lesson, index=2, needles=("def fasta_records", "gc_fraction"))
        fasta = heredoc(setup, "data/raw/example.fasta")
        with tempfile.TemporaryDirectory(prefix="omics-python-fundamentals-") as temp:
            project = Path(temp)
            input_path = project / "data/raw/example.fasta"
            output_path = project / "outputs/sequence_stats.csv"
            input_path.parent.mkdir(parents=True)
            input_path.write_text(fasta, encoding="utf-8", newline="\n")
            result = run_script(sys.executable, script, "scripts/compute_fasta_stats.py", project,
                                "data/raw/example.fasta", "outputs/sequence_stats.csv")
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = read_delimited(output_path)
            self.assertEqual([row["id"] for row in rows], ["seq1", "seq2", "seq3"])
            self.assertEqual([row["length"] for row in rows], ["14", "20", "14"])
            self.assertEqual([row["gc_fraction"] for row in rows], ["0.42857", "0.50000", ""])
            self.assertEqual([row["valid"] for row in rows], ["yes", "yes", "no"])


class PublishedStatisticsBranchesTests(unittest.TestCase):
    def test_displayed_python_welch_and_bh_examples(self) -> None:
        with tempfile.TemporaryDirectory(prefix="omics-stats-python-") as temp:
            project = Path(temp)
            python, _, _, _, pvalues = prepare_stats_project(project)
            result = run_script(sys.executable, python, "compare_groups.py", project,
                                "data/control.csv", "data/treated.csv", "results")
            self.assertEqual(result.returncode, 0, result.stderr)
            row = read_delimited(project / "results/comparison.csv")[0]
            self.assertEqual(row["n_control"], "4")
            self.assertAlmostEqual(float(row["mean_difference_treated_minus_control"]), 1.7)
            self.assertLess(float(row["ci95_low"]), float(row["ci95_high"]))
            bh = block("tutorials/statistics-for-bioinformatics.html", index=7,
                       needles=("multipletests", "pvalues_adjusted.txt"))
            (project / "pvalues_all_features.txt").write_text(pvalues, encoding="utf-8")
            adjusted = run_script(sys.executable, bh, "adjust_features.py", project)
            self.assertEqual(adjusted.returncode, 0, adjusted.stderr)
            values = [float(v) for v in (project / "pvalues_adjusted.txt").read_text().split()]
            self.assertEqual([int(v) for v in (project / "discoveries_fdr05.txt").read_text().split()], [1, 0, 0, 0])
            for actual, expected in zip(values, (0.04, 0.08, 0.2666666667, 0.8)):
                self.assertAlmostEqual(actual, expected, places=7)

    def test_displayed_base_r_welch_and_bh_examples(self) -> None:
        rscript = require_rscript()
        with tempfile.TemporaryDirectory(prefix="omics-stats-r-") as temp:
            project = Path(temp)
            _, r, _, _, pvalues = prepare_stats_project(project)
            result = run_script(rscript, r, "compare_groups.R", project,
                                "data/control.csv", "data/treated.csv", "results",
                                env=r_environment())
            self.assertEqual(result.returncode, 0, result.stderr)
            row = read_delimited(project / "results/comparison_R.csv")[0]
            self.assertEqual(row["n_control"], "4")
            self.assertAlmostEqual(float(row["mean_difference_treated_minus_control"]), 1.7)
            self.assertLess(float(row["ci95_low"]), float(row["ci95_high"]))
            bh = block("tutorials/statistics-for-bioinformatics.html", index=8,
                       needles=("p.adjust(pvals, method = \"BH\")", "discoveries_fdr05.txt"))
            (project / "pvalues_all_features.txt").write_text(pvalues, encoding="utf-8")
            adjusted = run_script(rscript, bh, "adjust_features.R", project, env=r_environment())
            self.assertEqual(adjusted.returncode, 0, adjusted.stderr)
            values = [float(v) for v in (project / "pvalues_adjusted.txt").read_text().split()]
            self.assertEqual([int(v) for v in (project / "discoveries_fdr05.txt").read_text().split()], [1, 0, 0, 0])
            for actual, expected in zip(values, (0.04, 0.08, 0.2666666667, 0.8)):
                self.assertAlmostEqual(actual, expected, places=7)


class PublishedExperimentalDesignBranchesTests(unittest.TestCase):
    def _exercise_branch(self, language: str) -> None:
        python_meta, r_meta, r_pca, python_pca, _, _ = prepare_design_project(Path(self.temp.name))
        project = Path(self.temp.name)
        if language == "python":
            executable, metadata_source, pca_source = sys.executable, python_meta, python_pca
            metadata_name, pca_name = "validate_metadata.py", "pca.py"
            env = None
        else:
            executable, metadata_source, pca_source = require_rscript(), r_meta, r_pca
            metadata_name, pca_name = "validate_metadata.R", "pca.R"
            env = r_environment()
        validated = run_script(executable, metadata_source, metadata_name, project, env=env)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertIn("Lane1", validated.stdout)
        pca = run_script(executable, pca_source, pca_name, project, env=env)
        self.assertEqual(pca.returncode, 0, pca.stderr)
        rows = read_delimited(project / "pca_coordinates.csv")
        self.assertEqual([row["sample_id"] for row in rows], ["S01", "S02", "S03", "S04"])
        self.assertTrue({"PC1", "PC2", "condition", "batch"}.issubset(rows[0]))
        for row in rows:
            self.assertTrue(math.isfinite(float(row["PC1"])))
            self.assertTrue(math.isfinite(float(row["PC2"])))
        expected = {"S01": ("control", "Lane1"), "S02": ("control", "Lane2"),
                    "S03": ("treated", "Lane1"), "S04": ("treated", "Lane2")}
        self.assertEqual({row["sample_id"]: (row["condition"], row["batch"]) for row in rows}, expected)

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="omics-design-")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_displayed_python_metadata_and_pca_examples(self) -> None:
        self._exercise_branch("python")

    def test_displayed_base_r_metadata_and_pca_examples(self) -> None:
        self._exercise_branch("r")


class PublishedTidyverseLabTests(unittest.TestCase):
    def test_exact_r_lab_selects_project_root_and_produces_expected_table_and_white_png(self) -> None:
        rscript = require_rscript()
        with tempfile.TemporaryDirectory(prefix="omics-tidyverse-") as temp:
            parent = Path(temp)
            project = write_tidyverse_project(parent)
            script = project / "scripts/01-tidy-qc.R"
            result = subprocess.run([rscript, "--vanilla", str(script)], cwd=project,
                                    env=r_environment(), capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=180, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = read_delimited(project / "results/sample_qc.tsv", delimiter="\t")
            self.assertEqual([row["sample_id"] for row in rows], ["S01", "S02", "S03"])
            self.assertEqual([int(row["total_counts"]) for row in rows], [1360, 1375, 1365])
            self.assertEqual([int(row["median_gene_count"]) for row in rows], [320, 280, 305])
            self.assertEqual([float(row["total_counts_millions"]) for row in rows],
                             [0.00136, 0.001375, 0.001365])
            assert_png_white_900x600(project / "results/reads_qc.png")
            self.assertFalse((ROOT / "results").exists(), "lesson output escaped its temporary project")

    def test_wrong_working_directory_fails_at_explicit_project_root(self) -> None:
        rscript = require_rscript()
        with tempfile.TemporaryDirectory(prefix="omics-tidyverse-root-") as temp:
            parent = Path(temp)
            project = write_tidyverse_project(parent)
            elsewhere = parent / "elsewhere"
            elsewhere.mkdir()
            result = subprocess.run([rscript, "--vanilla", str(project / "scripts/01-tidy-qc.R")],
                                    cwd=elsewhere, env=r_environment(), capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=120,
                                    check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project", result.stderr.lower())
            self.assertNotIn("gene_counts.tsv", result.stderr)
            self.assertEqual(list((project / "results").iterdir()), [])


class PublishedVisualizationPcaUmapTests(unittest.TestCase):
    def test_published_pca_then_umap_stages_run_on_public_teaching_fixture(self) -> None:
        lesson = "tutorials/data-visualization-fundamentals.html"
        pca = block(lesson, identifier="visualization-pca-stage", needles=("PCA(", "pca_full.tsv"))
        umap = block(lesson, identifier="visualization-umap-stage", needles=("umap.UMAP", "umap_coords.tsv"))
        with tempfile.TemporaryDirectory(prefix="omics-pca-umap-") as temp:
            project = Path(temp)
            (project / "data").mkdir()
            for filename in ("counts.tsv", "qc_metrics.tsv"):
                shutil.copyfile(VISUAL_FIXTURES / filename, project / "data" / filename)
            env = os.environ.copy()
            env.setdefault("MPLBACKEND", "Agg")
            env.setdefault("NUMBA_NUM_THREADS", "1")
            pca_run = run_script(sys.executable, pca, "pca_stage.py", project, env=env)
            self.assertEqual(pca_run.returncode, 0, pca_run.stderr)
            umap_run = run_script(sys.executable, umap, "umap_stage.py", project, env=env,
                                  timeout=240)
            self.assertEqual(umap_run.returncode, 0, umap_run.stderr)
            pca_rows = read_delimited(project / "results/pca_coords.tsv", delimiter="\t")
            umap_rows = read_delimited(project / "results/umap_coords.tsv", delimiter="\t")
            self.assertEqual([row["sample"] for row in pca_rows], [f"S0{i}" for i in range(1, 7)])
            self.assertEqual([row["sample"] for row in umap_rows], [f"S0{i}" for i in range(1, 7)])
            self.assertTrue(all(math.isfinite(float(row["PC1"])) and math.isfinite(float(row["PC2"]))
                                for row in pca_rows))
            self.assertTrue(all(math.isfinite(float(row["UMAP1"])) and math.isfinite(float(row["UMAP2"]))
                                for row in umap_rows))
            for filename in ("pca_plot.png", "umap_plot.png"):
                image = project / "results" / filename
                self.assertTrue(image.is_file())
                self.assertGreater(image.stat().st_size, 1000)
                self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


class PublishedSeuratPbmc3kNativeTests(unittest.TestCase):
    def test_exact_seurat_r_script_runs_on_verified_public_10x_pbmc3k(self) -> None:
        """Check real Seurat execution without cross-platform cluster/pixel equality."""
        rscript = require_rscript()
        packages = subprocess.run(
            [rscript, "--vanilla", "-e",
             'missing <- c("Seurat", "patchwork")[!vapply(c("Seurat", "patchwork"), '
             'requireNamespace, logical(1), quietly=TRUE)]; if (length(missing)) '
             'stop(paste("Missing native binary packages:", paste(missing, collapse=", ")) )'],
            env=r_environment(), capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False,
        )
        self.assertEqual(packages.returncode, 0, packages.stderr)

        lesson = "tutorials/scrna-seq-basics.html"
        script = block(lesson, needles=("library(Seurat)", "Read10X", "RunUMAP", "saveRDS"))
        with tempfile.TemporaryDirectory(prefix="omics-seurat-pbmc3k-") as temp:
            project = Path(temp)
            stage_pbmc3k_archive(project)
            run = run_script(rscript, script, "scripts/01_seurat_qc_clustering.R", project,
                             env=r_environment(), timeout=600)
            self.assertEqual(run.returncode, 0, run.stdout + "\n" + run.stderr)
            self.assertIn("After mitochondrial filter: 2638", run.stdout + run.stderr)

            rds = project / "results/pbmc_seurat.rds"
            self.assertTrue(rds.is_file())
            self.assertGreater(rds.stat().st_size, 0)
            for filename in ("qc_violin.png", "pca_elbow.png", "umap_clusters.png"):
                image = project / "results/figures" / filename
                self.assertTrue(image.is_file(), image)
                self.assertGreater(image.stat().st_size, 1000)
                self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

            check = subprocess.run(
                [rscript, "--vanilla", "-e",
                 'object <- readRDS("results/pbmc_seurat.rds"); '
                 'pca <- Seurat::Embeddings(object, "pca"); '
                 'umap <- Seurat::Embeddings(object, "umap"); '
                 'stopifnot(ncol(object) == 2638L, nrow(pca) == 2638L, ncol(pca) >= 2L, '
                 'nrow(umap) == 2638L, ncol(umap) == 2L); '
                 'cat("PBMC3K_RDS_CHECK_JSON {\\"cells\\":", ncol(object), '
                 '",\\"pca_rows\\":", nrow(pca), ",\\"pca_components\\":", ncol(pca), '
                 '",\\"umap_rows\\":", nrow(umap), ",\\"umap_components\\":", ncol(umap), "}\\n", sep="")'],
                cwd=project, env=r_environment(), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120, check=False,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("PBMC3K_RDS_CHECK_JSON", check.stdout)
            print(check.stdout.strip(), flush=True)


def package_versions(names: tuple[str, ...]) -> dict[str, str]:
    found: dict[str, str] = {}
    for name in names:
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            found[name] = "not-installed"
    return found


def environment_record() -> dict[str, object]:
    record: dict[str, object] = {
        "os": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_packages": package_versions(("numpy", "pandas", "scipy", "statsmodels",
                                                "scikit-learn", "matplotlib", "seaborn",
                                                "umap-learn", "Pillow")),
    }
    rscript = shutil.which("Rscript")
    if rscript:
        version = subprocess.run([rscript, "--version"], capture_output=True, text=True, check=False)
        packages = subprocess.run(
            [rscript, "--vanilla", "-e",
             'pkgs <- c("tidyverse", "here", "Seurat", "patchwork"); '
             'versions <- vapply(pkgs, function(p) if (requireNamespace(p, quietly=TRUE)) '
             'as.character(packageVersion(p)) else "not-installed", character(1)); '
             'cat(paste(c(R.version.string, paste0(names(versions), "=", versions)), sep="\\n"))'],
            capture_output=True, text=True, check=False,
        )
        record["r"] = version.stdout.strip() or version.stderr.strip()
        record["r_packages"] = packages.stdout.strip().splitlines() if packages.returncode == 0 else "unavailable"
    else:
        record["r"] = "not-installed"
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-json", type=Path,
                        help="optional evidence destination outside the repository")
    args = parser.parse_args()
    env = environment_record()
    print("PLATFORM_ENVIRONMENT_JSON " + json.dumps(env, sort_keys=True, separators=(",", ":")), flush=True)
    if not shutil.which("Rscript"):
        print("ERROR: Rscript is required for complete cross-platform validation", file=sys.stderr)
        return 2
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "successful": result.wasSuccessful(),
        "skipped": len(result.skipped),
    }
    print("PLATFORM_TEST_SUMMARY_JSON " + json.dumps(summary, sort_keys=True, separators=(",", ":")), flush=True)
    if args.evidence_json:
        args.evidence_json.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_json.write_text(json.dumps({"environment": env, "summary": summary},
                                                 indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
