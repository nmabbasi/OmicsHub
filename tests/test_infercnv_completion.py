"""Setup and durable-output contracts for the original R inferCNV route.

The opt-in tests use a completed public-data run. They do not simulate a
biological analysis, rerun inference, or modify the original result artifacts.
"""
from html.parser import HTMLParser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials/infercnv-copy-number-variation.html"
RSCRIPT = shutil.which("Rscript")


class LessonContent(HTMLParser):
    """Collect displayed code and text with only the Python standard library."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.code_blocks = []
        self.text = []
        self.pre_depth = 0
        self.in_code = False
        self.current = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.pre_depth += 1
        elif tag == "code" and self.pre_depth:
            self.in_code = True
            self.current = []

    def handle_endtag(self, tag):
        if tag == "code" and self.in_code:
            self.code_blocks.append("".join(self.current))
            self.in_code = False
        elif tag == "pre":
            self.pre_depth -= 1

    def handle_data(self, data):
        self.text.append(data)
        if self.in_code:
            self.current.append(data)


def lesson_content():
    parser = LessonContent()
    parser.feed(PAGE.read_text())
    parser.close()
    return parser


def blocks():
    return lesson_content().code_blocks


def analysis():
    return next(code for code in blocks() if "library(infercnv)" in code)


def checkpoint():
    marker = "# 6) Save the returned object"
    return marker + analysis().split(marker, 1)[1]


def run_r(code, env=None):
    with tempfile.TemporaryDirectory(prefix="infercnv-contract-") as directory:
        script = Path(directory) / "check.R"
        script.write_text(code)
        return subprocess.run(
            [RSCRIPT, "--vanilla", str(script)], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=180,
        )


class InfercnvCompletionSourceTests(unittest.TestCase):
    def test_code_parser_preserves_nested_text_and_escaped_operators(self):
        parser = LessonContent()
        parser.feed('<p>JAGS 4.x</p><code>inline only</code>'
                    '<pre><code>x &lt;- 2 &amp; 3<span>\nHMM = TRUE</span></code></pre>')
        parser.close()
        self.assertEqual(parser.code_blocks, ["x <- 2 & 3\nHMM = TRUE"])
        self.assertIn("JAGS 4.x", "".join(parser.text))

    def test_jags_setup_is_separate_and_dependency_failure_is_checked(self):
        self.assertIn("JAGS 4.x", "".join(lesson_content().text))
        setup = next(code for code in blocks() if "BiocManager::install" in code)
        self.assertIn('BiocManager::install("infercnv", ask = FALSE, update = FALSE)', setup)
        self.assertIn('needed <- c("rjags", "infercnv")', setup)
        self.assertIn('if (length(missing)) stop("Setup incomplete: "', setup)
        self.assertNotIn("install.packages(", analysis())
        self.assertNotIn("BiocManager::install", analysis())

    def test_scientific_options_are_not_weakened(self):
        code = analysis()
        for option in ("cutoff = 0.1", "cluster_by_groups = TRUE", "denoise = TRUE", "HMM = TRUE"):
            self.assertIn(option, code)
        self.assertNotIn("HMM = FALSE", code)
        self.assertNotIn("denoise = FALSE", code)

    def test_reused_output_folder_is_not_accepted_as_a_fresh_run(self):
        code = analysis()
        self.assertIn('length(list.files(out_dir, all.files = TRUE, no.. = TRUE))', code)
        self.assertLess(code.index('stop("Choose an empty output directory'),
                        code.index('infercnv_obj <- infercnv::run('))

    def test_checkpoint_requires_a_durable_object_and_hmm_reports(self):
        code = checkpoint()
        for contract in ('saveRDS(infercnv_obj, final_path)', 'readRDS(final_path)',
                         'methods::validObject(final_check)', 'all(is.finite(final_check@expr.data))',
                         'if (!length(hmm_reports)) stop(', 'report$state %in% legal_states',
                         '"cell_group_name", "cnv_name", "state", "chr", "start", "end"'):
            self.assertIn(contract, code)
        self.assertNotIn('length(list.files(out_dir, all.files = TRUE)) > 2', code)
        self.assertIn('zero retained regions can be a valid outcome', PAGE.read_text())
        self.assertNotIn('stopifnot(nrow(report) > 0', code)

    @unittest.skipUnless(RSCRIPT, "Rscript is not installed")
    def test_all_displayed_r_code_parses(self):
        for code in blocks():
            if "BiocManager::install" not in code and "library(infercnv)" not in code:
                continue
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "displayed.R"
                source.write_text(code)
                result = run_r('parse(file = ' + repr(str(source)) + ')\n')
                self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(RSCRIPT, "Rscript is not installed")
    def test_failed_package_readiness_stops_before_analysis(self):
        setup = next(code for code in blocks() if "BiocManager::install" in code)
        readiness = setup[setup.index('needed <-'):]
        result = run_r('requireNamespace <- function(...) FALSE\n' + readiness)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Setup incomplete: rjags, infercnv", result.stderr)


@unittest.skipUnless(RSCRIPT and os.environ.get("INFERCNV_TEST_ROOT"),
                     "set INFERCNV_TEST_ROOT to the completed genuine public-data run")
class InfercnvRealArtifactTests(unittest.TestCase):
    def replay(self, mode):
        root = Path(os.environ["INFERCNV_TEST_ROOT"])
        original = root / "results/installed_full_options"
        self.assertTrue((original / "returned_final_infercnv.rds").is_file())
        with tempfile.TemporaryDirectory(prefix="infercnv-checkpoint-replay-") as directory:
            target = Path(directory)
            if mode != "missing":
                reports = list(original.rglob("*.pred_cnv_regions.dat"))
                self.assertTrue(reports)
                for index, source in enumerate(reports):
                    destination = target / (str(index) + ".pred_cnv_regions.dat")
                    if mode == "bad_header" and index == 0:
                        text = source.read_text()
                        header, rest = text.split("\n", 1)
                        destination.write_text(header.replace("\tstate\t", "\tmissing_state\t") + "\n" + rest)
                    else:
                        shutil.copyfile(source, destination)
            env = os.environ.copy()
            env["CONTRACT_INFER_ROOT"] = str(root)
            env["CONTRACT_INFER_OUTPUT"] = str(target)
            setup = '''
root <- Sys.getenv("CONTRACT_INFER_ROOT")
extra <- strsplit(Sys.getenv("INFERCNV_TEST_R_LIBRARIES"), .Platform$path.sep, fixed=TRUE)[[1]]
.libPaths(c(file.path(root,"library"), extra, .libPaths()))
library(infercnv)
infercnv_obj <- readRDS(file.path(root,"results","installed_full_options","returned_final_infercnv.rds"))
counts <- readRDS(file.path(root,"inputs","counts_matrix.rds"))
out_dir <- Sys.getenv("CONTRACT_INFER_OUTPUT")
'''
            result = run_r(setup + checkpoint(), env=env)
            if mode == "valid":
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((target / "returned_final_infercnv.rds").is_file())
                self.assertTrue((target / "session-info.txt").is_file())
            else:
                self.assertNotEqual(result.returncode, 0, "Corrupt/missing HMM evidence was accepted")
                self.assertIn("No HMM region report" if mode == "missing" else "is not TRUE", result.stderr)

    def test_checkpoint_passes_on_real_completed_object_and_reports(self):
        self.replay("valid")

    def test_missing_hmm_report_is_rejected_despite_a_saved_object(self):
        self.replay("missing")

    def test_corrupt_report_schema_is_rejected(self):
        self.replay("bad_header")


if __name__ == "__main__":
    unittest.main()
