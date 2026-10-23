"""Bounded Tidyverse revision contracts; optional R tests never install packages.

Set TIDYVERSE_TEST_R_LIBRARY to an existing prepared library to run the full
synthetic lab. Default CI can run source checks without scientific packages.
"""
from html.parser import HTMLParser
from pathlib import Path
import csv
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials/r-tidyverse-fundamentals.html"
PUBLISHED_PR10 = "d1748a93e9fb9a59ec20ee3ab7aabece9c0ae1f8"


class CodeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.named, self.blocks, self.current = {}, [], None
        self.identifier = None

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.current = []
            self.identifier = dict(attrs).get("id")

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "pre" and self.current is not None:
            code = "".join(self.current)
            self.blocks.append(code)
            if self.identifier:
                self.named[self.identifier] = code
            self.current = None


def displayed():
    parser = CodeParser()
    parser.feed(PAGE.read_text(encoding="utf-8"))
    return parser


def r_environment():
    env = dict(os.environ)
    library = env.get("TIDYVERSE_TEST_R_LIBRARY")
    if library:
        if not Path(library).is_dir():
            raise AssertionError("TIDYVERSE_TEST_R_LIBRARY must name an existing prepared library")
        env["R_LIBS_USER"] = library
    return env


def run_r(project, expression=None, script=None):
    command = [shutil.which("Rscript") or "Rscript", "--vanilla"]
    command += ["-e", expression] if expression is not None else [str(script or "scripts/01-tidy-qc.R")]
    return subprocess.run(command, cwd=project, env=r_environment(), text=True,
                          capture_output=True, check=False, timeout=120)


def make_project(parent):
    result = subprocess.run(["bash", "-e", "-c", displayed().named["tidyverse-fixture-setup"]],
                            cwd=parent, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr)
    project = parent / "tidy-qc"
    (project / "scripts/01-tidy-qc.R").write_text(displayed().named["tidyverse-workflow"], encoding="utf-8")
    return project


def read_qc(project):
    with (project / "results/sample_qc.tsv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class TidyverseSourceContractTests(unittest.TestCase):
    def test_scientific_script_changes_only_explicit_root_and_saved_background(self):
        old = subprocess.check_output(["git", "show", f"{PUBLISHED_PR10}:tutorials/r-tidyverse-fundamentals.html"],
                                      cwd=ROOT, text=True)
        parser = CodeParser(); parser.feed(old)
        original = next(block for block in parser.blocks if block.startswith("library(tidyverse)"))
        expected = original.replace('library(here)\n', 'library(here)\nhere::i_am("scripts/01-tidy-qc.R")\n', 1)
        expected = expected.replace('dpi = 150)', 'dpi = 150, bg = "white")', 1)
        self.assertEqual(displayed().named["tidyverse-workflow"], expected)

    def test_project_marker_and_library_exist_before_first_r_process(self):
        setup = displayed().named["tidyverse-fixture-setup"]
        self.assertLess(setup.index("touch .here"), setup.index("Rscript --version"))
        self.assertLess(setup.index("mkdir -p .r-library"), setup.index("Rscript --version"))
        workflow = displayed().named["tidyverse-workflow"]
        self.assertLess(workflow.index("here::i_am"), workflow.index("counts_file <-"))

    def test_install_preflight_and_run_use_the_same_fresh_process_library(self):
        named = displayed().named
        for key in ("tidyverse-package-install", "tidyverse-package-preflight", "tidyverse-run"):
            self.assertIn('R_LIBS_USER="$PWD/.r-library" Rscript --vanilla', named[key])
        install = named["tidyverse-package-install"]
        self.assertLess(install.index('install.packages("dplyr"'), install.index('install.packages(c("tidyverse"'))
        self.assertIn('lib = lib', install)
        self.assertIn('packageVersion("dplyr") >= "1.1.1"', named["tidyverse-package-preflight"])
        text = PAGE.read_text(encoding="utf-8")
        for phrase in ("libxml2-dev", "filter_out", "not a lockfile", "not separately tested", "other", "12 invalid-input"):
            self.assertIn(phrase, text)
        self.assertNotIn("\u2014", text)


class TidyverseOptionalRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("Rscript") or not shutil.which("bash"):
            raise unittest.SkipTest("Rscript and Bash are required for the optional lab execution")
        result = run_r(ROOT, expression='quit(status=as.integer(!all(vapply(c("tidyverse", "here"), requireNamespace, logical(1), quietly=TRUE))))')
        if result.returncode:
            raise unittest.SkipTest("tidyverse/here unavailable in the selected existing R library")

    def test_fixture_tables_plot_objects_and_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            result = run_r(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = read_qc(project)
            self.assertEqual([row["sample_id"] for row in rows], ["S01", "S02", "S03"])
            self.assertEqual([int(row["total_counts"]) for row in rows], [1360, 1375, 1365])
            self.assertEqual([int(row["median_gene_count"]) for row in rows], [320, 280, 305])
            self.assertEqual([float(row["total_counts_millions"]) for row in rows], [0.00136, 0.001375, 0.001365])
            expected = (project / "results/sample_qc.tsv").read_bytes()
            objects = run_r(project, expression='source("scripts/01-tidy-qc.R"); stopifnot(nrow(long_counts)==9L,nrow(joined)==9L,nrow(sample_qc)==3L,identical(levels(sample_qc$condition),c("control","treated")),p$labels$y=="Sum of supplied counts (millions)",p$labels$title=="Per-sample count totals",nrow(ggplot_build(p)$data[[1]])==3L)')
            self.assertEqual(objects.returncode, 0, objects.stderr)
            counts = project / "data/raw/gene_counts.tsv"
            original = counts.read_text()
            for output in (project / "results").iterdir(): output.unlink()
            counts.write_text(original.replace("150\t", "150.5\t", 1))
            failed = run_r(project)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(list((project / "results").iterdir()), [])
            counts.write_text(original)
            recovered = run_r(project)
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertEqual((project / "results/sample_qc.tsv").read_bytes(), expected)

    def test_all_twelve_invalid_input_cases_stop_without_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            initial = Path(temporary) / "initial"; initial.mkdir()
            project = make_project(initial)
            counts = (project / "data/raw/gene_counts.tsv").read_text()
            meta = (project / "data/metadata/samples.tsv").read_text()
            cases = [
                ("missing-sample", counts, meta.replace("S03\ttreated\n", "")),
                ("extra-sample", counts, meta + "S04\ttreated\n"),
                ("duplicate-sample", counts, meta + "S02\ttreated\n"),
                ("missing-gene", counts.replace("TP53\t", "\t"), meta),
                ("duplicate-gene", counts.replace("BRCA1\t", "TP53\t"), meta),
                ("negative-count", counts.replace("150\t", "-1\t", 1), meta),
                ("fractional-count", counts.replace("150\t", "150.5\t", 1), meta),
                ("nonnumeric-count", counts.replace("150\t", "oops\t", 1), meta),
                ("missing-count", counts.replace("150\t", "\t", 1), meta),
                ("infinite-count", counts.replace("150\t", "Inf\t", 1), meta),
                ("unknown-condition", counts, meta.replace("S02\ttreated", "S02\tother")),
                ("missing-condition", counts, meta.replace("S02\ttreated", "S02\t")),
            ]
            self.assertEqual(len(cases), 12)
            for name, c, m in cases:
                with self.subTest(case=name):
                    parent = Path(temporary) / name; parent.mkdir()
                    p = make_project(parent)
                    (p / "data/raw/gene_counts.tsv").write_text(c)
                    (p / "data/metadata/samples.tsv").write_text(m)
                    result = run_r(p)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertEqual(list((p / "results").iterdir()), [])

    def test_valid_zero_counts_and_reordered_metadata_remain_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            original_run = run_r(project)
            self.assertEqual(original_run.returncode, 0, original_run.stderr)
            expected = (project / "results/sample_qc.tsv").read_bytes()
            (project / "data/metadata/samples.tsv").write_text("sample_id\tcondition\nS03\ttreated\nS01\tcontrol\nS02\ttreated\n")
            reordered = run_r(project)
            self.assertEqual(reordered.returncode, 0, reordered.stderr)
            self.assertEqual((project / "results/sample_qc.tsv").read_bytes(), expected)
            counts = project / "data/raw/gene_counts.tsv"
            counts.write_text(counts.read_text().replace("150\t", "0\t", 1))
            zero = run_r(project)
            self.assertEqual(zero.returncode, 0, zero.stderr)
            self.assertEqual(int(read_qc(project)[0]["total_counts"]), 320 + 890)

    def test_ancestor_git_root_and_previously_loaded_here_are_reset(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary); (parent / ".git").mkdir()
            project = make_project(parent)
            result = run_r(parent, expression='library(here); stopifnot(identical(here::here(),normalizePath("."))); setwd("tidy-qc"); source("scripts/01-tidy-qc.R"); stopifnot(identical(here::here(),normalizePath(".")))')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "results/sample_qc.tsv").is_file())
            self.assertFalse((parent / "results").exists())
            (project / ".here").unlink()
            explicit = run_r(project)
            self.assertEqual(explicit.returncode, 0, explicit.stderr)

    def test_wrong_working_directory_fails_at_root_declaration(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary); project = make_project(parent)
            elsewhere = parent / "elsewhere"; elsewhere.mkdir()
            result = run_r(elsewhere, script=project / "scripts/01-tidy-qc.R")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project", result.stderr.lower())
            self.assertNotIn("gene_counts.tsv", result.stderr)
            self.assertEqual(list((project / "results").iterdir()), [])

    def test_documented_preflight_and_run_select_the_project_library(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            library = os.environ.get("TIDYVERSE_TEST_R_LIBRARY")
            if library:
                (project / ".r-library").rmdir()
                (project / ".r-library").symlink_to(Path(library).resolve(), target_is_directory=True)
            for key in ("tidyverse-package-preflight", "tidyverse-run"):
                result = subprocess.run(["bash", "-e", "-c", displayed().named[key]],
                                        cwd=project, env=r_environment(), capture_output=True,
                                        text=True, timeout=120, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "results/reads_qc.png").is_file())

    def test_saved_png_is_opaque_white_at_the_edges(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is optional; install it to inspect PNG pixels")
        with tempfile.TemporaryDirectory() as temporary:
            project = make_project(Path(temporary))
            result = run_r(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(project / "results/reads_qc.png") as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (900, 600))
                rgba = image.convert("RGBA")
                self.assertEqual(rgba.getchannel("A").getextrema(), (255, 255))
                for point in ((0, 0), (899, 0), (0, 599), (899, 599)):
                    self.assertEqual(rgba.getpixel(point), (255, 255, 255, 255))


if __name__ == "__main__":
    unittest.main()
