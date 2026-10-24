"""Learner-facing editorial contracts, not execution of resource-dependent tools."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = re.compile(r'<article\b[^>]*>(.*?)</article\s*>', re.S | re.I)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.descriptions = []
        self.keywords = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            if attrs.get('name') in ('description', 'twitter:description') or attrs.get('property') == 'og:description':
                self.descriptions.append(attrs['content'])
            if attrs.get('name') == 'keywords':
                self.keywords = [item.strip() for item in attrs['content'].split(',')]

    def handle_data(self, data):
        self.parts.append(data)


def source(slug):
    return (ROOT / 'tutorials' / (slug + '.html')).read_text(encoding='utf-8')


def article_text(slug):
    parser = TextParser()
    match = ARTICLE.search(source(slug))
    if not match:
        raise AssertionError('missing article: ' + slug)
    parser.feed(match.group(1))
    return ' '.join(' '.join(parser.parts).split())


class ResourceContentLearningTests(unittest.TestCase):
    def test_previews_describe_supplied_learning_routes(self):
        expectations = {
            'ai-coding-cursor-aider': ('offline Git fixture', 'optionally'),
            'ai-prompt-engineering-seurat': ('supplied Seurat and Scanpy templates', 'statistical assumptions'),
            'docker-singularity-bioinformatics': ('local Docker BWA example', 'optional Apptainer/Slurm adaptation'),
        }
        for slug, phrases in expectations.items():
            with self.subTest(slug=slug):
                parser = TextParser()
                parser.feed(source(slug))
                self.assertEqual(len(parser.descriptions), 3)
                self.assertEqual(len(set(parser.descriptions)), 1)
                for phrase in phrases:
                    self.assertIn(phrase, parser.descriptions[0])

    def test_protein_lesson_does_not_advertise_unprovided_design_methods(self):
        page = source('protein-structure-design-alphafold')
        parser = TextParser()
        parser.feed(page)
        self.assertTrue({'AlphaFold DB', 'UniProt', 'pLDDT'}.issubset(parser.keywords))
        self.assertFalse({'AlphaFold 3', 'ESMFold', 'ESM3', 'protein design'}.intersection(parser.keywords))
        self.assertNotIn('alphafold-esmfold.webp', page)
        text = article_text('protein-structure-design-alphafold')
        self.assertIn('does not predict a new structure or design a protein', text)
        self.assertIn('recorded retrieval', text)
        self.assertIn('not a guaranteed result from a later fetch', text)

    def test_cluster_free_reading_route_does_not_claim_job_completion(self):
        connection = article_text('hpc-connection')
        submission = article_text('hpc-submission-part1')
        support = article_text('hpc-support')
        self.assertIn('Planning check, no cluster required', connection)
        self.assertIn('Keep the private key local', connection)
        self.assertIn('Before you have cluster access', submission)
        self.assertIn('not that the job started or completed', submission)
        self.assertIn('Interpret a hypothetical job record', support)
        self.assertIn('successful job-script termination only', support)

    def test_account_free_review_tasks_have_reasoned_answers(self):
        for slug, expected in {
            'ai-bioinformatics-github-copilot': 'duplicate-name behavior',
            'notebooklm-research-brain': 'Mark the claim unresolved',
            'mcp-zotero': 'not an access-control boundary',
        }.items():
            with self.subTest(slug=slug):
                text = article_text(slug)
                self.assertIn('Account-free', text)
                self.assertIn('Reasoned answer:', text)
                self.assertIn(expected, text)

    def test_single_cell_decision_checks_preserve_inference_limits(self):
        expected = {
            'cell-cell-communication': 'not independent experimental validation',
            'single-cell-deconvolution': 'normalization to one does not show',
            'tcr-bcr-repertoire-analysis': 'independent biological samples',
            'scrna-seq-quality-control': 'Neither score resolves this confounding',
            'scrna-seq-downstream-analysis': 'does not create independent biological replicates',
        }
        for slug, phrase in expected.items():
            with self.subTest(slug=slug):
                text = article_text(slug)
                self.assertIn('Hypothetical decision check', text)
                self.assertIn('Reasoned feedback', text)
                self.assertIn(phrase, text)

    def test_mapping_and_phylogeny_checks_do_not_inflate_evidence(self):
        assembly = article_text('metagenomics-assembly-mapping')
        phylogeny = article_text('evolutionary-phylogeny-analysis')
        self.assertIn('Hypothetical review', assembly)
        self.assertIn('not independent validation of the assembly', assembly)
        self.assertIn('Hypothetical review', phylogeny)
        self.assertIn('not proof of the species history', phylogeny)

    def test_wes_negative_result_is_limited_to_its_assayed_scope(self):
        text = article_text('wes-variant-calling-pipeline')
        self.assertIn('not every coding base', text)
        self.assertIn('most noncoding sequence is not systematically assessed', text)
        self.assertIn('validated target and callable regions', text)

    def test_prompt_lesson_names_actual_materials_and_path_handoff(self):
        text = article_text('ai-prompt-engineering-seurat')
        self.assertIn('What this lesson provides', text)
        self.assertIn('A generated script and its outputs are not supplied', text)
        self.assertIn('Align paths before using the prompt and template together', text)
        self.assertNotIn('so an assistant produces runnable code', text)


if __name__ == '__main__':
    unittest.main()
