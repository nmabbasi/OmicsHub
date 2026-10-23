"""Offline structural checks for the revised Micromamba lesson."""
from html import unescape
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tutorials" / "conda-mamba-part1.html"


class MicromambaLessonRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        cls.text = unescape(cls.html)

    def test_no_em_dash_and_existing_reader_structure_remains(self):
        self.assertNotIn("\u2014", self.html)
        for marker in (
            '<div class="page-content" id="tutorial-page">',
            '<article aria-labelledby="tutorial-title"',
            '<nav aria-label="Learning path navigation"',
            '<nav aria-label="Learning path continuation"',
            'id="reader-course-navigation"',
        ):
            self.assertIn(marker, self.html)
        self.assertNotIn("text-align: center", self.html.lower())

    def test_every_displayed_micromamba_create_route_has_explicit_bioconda_policy(self):
        lines = self.text.splitlines()
        commands = []
        index = 0
        while index < len(lines):
            if "micromamba create" not in lines[index]:
                index += 1
                continue
            parts = [lines[index]]
            while parts[-1].rstrip().endswith("\\") and index + 1 < len(lines):
                index += 1
                parts.append(lines[index])
            commands.append(" ".join(part.rstrip().rstrip("\\") for part in parts))
            index += 1
        self.assertGreaterEqual(len(commands), 8, "Expected the displayed create examples to be checked")
        for flattened in commands:
            with self.subTest(command=flattened[:120]):
                self.assertIn("--override-channels", flattened)
                self.assertIn("-c conda-forge", flattened)
                self.assertIn("-c bioconda", flattened)
                self.assertIn("--channel-priority strict", flattened)

    def test_lesson_shows_saved_yaml_and_checks_versions_export_and_recreate(self):
        for required in (
            "cat &gt; environment.yml &lt;&lt;'YAML'",
            "micromamba create -f environment.yml",
            "fastqc --version",
            "multiqc --version",
            "micromamba env export -n qc-tools",
            "qc-tools-copy",
            "fresh solve on this platform",
            "authored request",
            "Small variation",
        ):
            self.assertIn(required, self.html)

    def test_no_machine_level_channel_setup_is_required_for_create_commands(self):
        self.assertIn("prevents configured default channels from silently joining the solve", self.html)
        self.assertNotIn("conda config --set", self.html)

    def test_resolved_export_is_reviewed_before_recreation(self):
        for required in (
            "cp environment-resolved.yml environment-resolved-reviewed.yml",
            "-f environment-resolved-reviewed.yml",
            "An export can reorder channels",
            "remove any top-level",
            "prefix:",
            "micromamba run -n qc-tools-copy python --version",
            "micromamba run -n qc-tools-copy fastqc --version",
            "micromamba run -n qc-tools-copy multiqc --version",
            "fresh solve failed with a libdeflate build conflict",
            "fresh-name recreation and all three version checks then succeeded",
        ):
            self.assertIn(required, self.html)
        self.assertNotIn("-f environment-resolved.yml --override-channels", self.text)


if __name__ == "__main__":
    unittest.main()
