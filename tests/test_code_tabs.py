"""Regression checks for R-first language tabs and reviewed source ranges."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TutorialCodeTabOrderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = json.loads((ROOT / 'tools/tutorial-code-groups.json').read_text())['tutorials']

    def test_all_paired_groups_declare_r_then_python_display_and_source_order(self):
        groups = [group for tutorial in self.groups.values() for group in tutorial]
        self.assertEqual(len(groups), 28)
        self.assertTrue(all(group['tabOrder'] == ['r', 'python'] for group in groups))
        self.assertTrue(all([p['language'] for p in group['panels']] == ['r', 'python'] for group in groups))
        self.assertTrue(all(group['panels'][0]['end'] + 1 == group['panels'][1]['start'] for group in groups))

    def test_complete_author_reviewed_groups_are_present(self):
        expected = {
            'scrna-seq-basics': 1,
            'data-visualization-fundamentals': 5,
            'statistics-for-bioinformatics': 2,
            'experimental-design-batch-effects': 2,
            'spatial-transcriptomics-r-python': 3,
            'quality-control-fundamentals': 1,
            'scrna-seq-quality-control': 1,
            'git-github-bioinformatics': 1,
            'biological-data-formats': 1,
            'single-cell-foundation-models': 1,
            'protein-structure-design-alphafold': 2,
            'ai-bioinformatics-github-copilot': 1,
            'ai-coding-cursor-aider': 1,
            'autonomous-research-orchestrator': 1,
            'python-fundamentals-bioinformatics': 1,
            'hpc-basic-commands': 2,
            'evolutionary-phylogeny-analysis': 2,
        }
        self.assertEqual({slug: len(groups) for slug, groups in self.groups.items()}, expected)

    def test_snakefile_keeps_its_dsl_display_label_without_an_r_tab(self):
        data = json.loads((ROOT / 'tools/tutorial-code-languages.json').read_text())['tutorials']
        labels = [block['language'] for block in data['reproducible-workflows-snakemake-nextflow']['blocks']]
        self.assertEqual(labels[0], 'python')
        article = (ROOT / 'tutorials/reproducible-workflows-snakemake-nextflow.html').read_text()
        self.assertIn('data-code-label="Snakemake DSL"', article)

    def test_script_builds_tabs_from_declared_order_and_defaults_to_r(self):
        source = (ROOT / 'code-tabs.js').read_text()
        self.assertIn("const orderedPanels = tabOrder.map(language => sourcePanels.find(panel => panel.language === language));", source)
        self.assertIn("controller.activate(preference || 'r');", source)
        self.assertIn("pre.dataset.codeSourceIndex = String(index);", source)
        self.assertIn("sessionStorage.setItem(preferenceKey, language)", source)
        self.assertIn("selectLanguage(panel.dataset.language, controller, false, false)", source)


if __name__ == '__main__':
    unittest.main()
