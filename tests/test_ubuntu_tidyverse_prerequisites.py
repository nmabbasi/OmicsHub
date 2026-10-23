"""Ubuntu setup contracts; all installer tests here are offline simulations.

The real fresh-filesystem installation is separate evidence. These tests never
run apt, download R packages, or alter a system/project package library.
"""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import tempfile
import unittest

from test_tidyverse_setup_revision import displayed, PAGE


class UbuntuPrerequisiteSourceTests(unittest.TestCase):
    def test_complete_ubuntu_block_precedes_fixture_r_version_and_package_install(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertLess(text.index('id="tidyverse-ubuntu-prerequisites"'), text.index('id="tidyverse-fixture-setup"'))
        self.assertLess(text.index('id="tidyverse-fixture-setup"'), text.index('id="tidyverse-package-install"'))
        words = shlex.split(displayed().named["tidyverse-ubuntu-prerequisites"].replace("\\\n", " "))
        expected = {
            "r-base", "r-base-dev", "build-essential", "pkg-config", "ca-certificates",
            "libcurl4-openssl-dev", "libssl-dev", "libxml2-dev", "libuv1-dev",
            "libfontconfig1-dev", "libfreetype6-dev", "libharfbuzz-dev", "libfribidi-dev",
            "libpng-dev", "libtiff-dev", "libjpeg-dev", "libwebp-dev", "libicu-dev",
            "zlib1g-dev", "fonts-dejavu-core",
        }
        self.assertTrue(expected.issubset(words))
        self.assertEqual(words[:4], ["sudo", "apt-get", "update", "&&"])
        self.assertFalse(any(word.startswith("r-cran-") for word in words))

    def test_postinstall_and_fresh_readiness_have_distinct_real_loading_gates(self):
        named = displayed().named
        install = named["tidyverse-package-install"]
        for fragment in ('timeout = max(600, getOption("timeout"))', 'Ncpus = 2',
                         'requireNamespace(pkg, lib.loc = lib, quietly = TRUE)',
                         'stop("Installation incomplete: "', 'packageVersion("dplyr", lib.loc = lib)'):
            self.assertIn(fragment, install)
        readiness = named["tidyverse-package-preflight"]
        self.assertIn('library(tidyverse)', readiness)
        self.assertIn('library(here)', readiness)
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn('exit code 0', text)
        self.assertIn('If the readiness check fails, the lab is not ready to run.', text)
        self.assertNotIn("\u2014", text)


@unittest.skipUnless(shutil.which("bash"), "Bash is needed for offline command simulations")
class UbuntuAptSimulationTests(unittest.TestCase):
    def run_mock(self, mode):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            log = root / "calls.log"
            sudo = root / "sudo"
            sudo.write_text('#!/bin/sh\nexec "$@"\n')
            apt = root / "apt-get"
            apt.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$APT_TEST_LOG"\nif [ "$1" = update ] && [ "$APT_TEST_MODE" = update-fails ]; then exit 41; fi\nif [ "$1" = install ] && [ "$APT_TEST_MODE" = install-fails ]; then exit 42; fi\nexit 0\n')
            sudo.chmod(0o755); apt.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ.get("PATH", ""),
                       APT_TEST_LOG=str(log), APT_TEST_MODE=mode)
            result = subprocess.run([shutil.which("bash"), "-c", displayed().named["tidyverse-ubuntu-prerequisites"]],
                                    env=env, text=True, capture_output=True, check=False)
            return result, log.read_text().splitlines()

    def test_failed_update_does_not_continue_to_install(self):
        result, calls = self.run_mock("update-fails")
        self.assertEqual(result.returncode, 41)
        self.assertEqual(calls, ["update"])

    def test_failed_system_install_propagates_failure(self):
        result, calls = self.run_mock("install-fails")
        self.assertEqual(result.returncode, 42)
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[1].startswith("install "))

    def test_success_passes_all_declared_packages_without_extra_commands(self):
        result, calls = self.run_mock("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 2)
        self.assertIn("libuv1-dev", calls[1])
        self.assertIn("libwebp-dev", calls[1])


def r_expression(key):
    words = shlex.split(displayed().named[key])
    if words[1:4] != ["Rscript", "--vanilla", "-e"] or len(words) != 5:
        raise AssertionError("expected the existing per-command R_LIBS_USER/fresh R expression form")
    return words[4]


@unittest.skipUnless(shutil.which("Rscript"), "Rscript is optional for offline R installer simulations")
class RInstallerSimulationTests(unittest.TestCase):
    def run_mock(self, mode, key="tidyverse-package-install", timeout=60):
        with tempfile.TemporaryDirectory() as temporary:
            lib = Path(temporary) / ".r-library"; lib.mkdir()
            env = dict(os.environ, R_LIBS_USER=str(lib), UBUNTU_INSTALL_TEST_MODE=mode)
            preamble = '''
mode <- Sys.getenv("UBUNTU_INSTALL_TEST_MODE")
calls <- character()
install.packages <- function(pkgs, lib, ...) {
  stopifnot(identical(lib, Sys.getenv("R_LIBS_USER")))
  calls <<- c(calls, pkgs)
  if (mode != "success") warning("simulated package/download failure")
  invisible(NULL)
}
requireNamespace <- function(package, lib.loc = NULL, quietly = FALSE, ...) {
  if (mode == "global-only") return(is.null(lib.loc))
  if (mode == "missing-all") return(FALSE)
  if (startsWith(mode, "missing-")) return(package != sub("^missing-", "", mode))
  if (!is.null(lib.loc)) stopifnot(identical(lib.loc, Sys.getenv("R_LIBS_USER")))
  TRUE
}
packageVersion <- function(package, lib.loc = NULL, ...) {
  if (mode == "old-dplyr") package_version("1.1.0") else package_version("1.2.1")
}
library <- function(package, ...) {
  if (mode == "attach-fails") stop("simulated fresh-session attach failure")
  invisible(NULL)
}
'''
            final = '\nif (length(calls)) stopifnot(identical(calls,c("dplyr","tidyverse","here")),getOption("Ncpus")==2L,getOption("timeout")>=600)\ncat("OFFLINE_SIMULATION_OK\\n")\n'
            if key == "tidyverse-package-install":
                final += f'\nstopifnot(getOption("timeout") == max(600, {timeout}))\n'
            expression = f'options(timeout={timeout})\n' + preamble + r_expression(key) + final
            return subprocess.run([shutil.which("Rscript"), "--vanilla", "-e", expression],
                                  env=env, cwd=temporary, capture_output=True, text=True,
                                  check=False, timeout=30)

    def test_success_checks_all_requested_packages_and_timeout_workers(self):
        result = self.run_mock("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OFFLINE_SIMULATION_OK", result.stdout)

    def test_longer_existing_timeout_is_not_reduced(self):
        result = self.run_mock("success", timeout=1200)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_missing_package_returns_nonzero_despite_warning_only_installer(self):
        for package in ("dplyr", "tidyverse", "here", "all"):
            with self.subTest(missing=package):
                result = self.run_mock("missing-" + package)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Installation incomplete:", result.stderr)

    def test_preexisting_global_packages_do_not_hide_failed_project_installation(self):
        result = self.run_mock("global-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Installation incomplete:", result.stderr)

    def test_dplyr_below_join_api_minimum_returns_nonzero(self):
        result = self.run_mock("old-dplyr")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("OFFLINE_SIMULATION_OK", result.stdout)

    def test_fresh_readiness_fails_if_namespace_is_missing(self):
        result = self.run_mock("missing-tidyverse", "tidyverse-package-preflight")
        self.assertNotEqual(result.returncode, 0)

    def test_fresh_readiness_also_requires_package_attachment(self):
        result = self.run_mock("attach-fails", "tidyverse-package-preflight")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simulated fresh-session attach failure", result.stderr)


if __name__ == "__main__":
    unittest.main()
