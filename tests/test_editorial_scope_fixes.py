#!/usr/bin/env python3
"""Regression checks for approved tutorial scope and comparison-table fixes."""
from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENAMED = {
    "mcp-zotero": {
        "title": "Choosing and Safely Evaluating a Zotero MCP Server",
        "description": (
            "A conceptual guide to selecting and safely evaluating a specific Zotero MCP server: "
            "inspect its access path, permissions, and data flow, then verify a read-only test "
            "against a disposable collection. No MCP server installation or live Zotero test is included."
        ),
        "neighbors": (
            "tutorials/ai-coding-cursor-aider.html",
            "tutorials/notebooklm-research-brain.html",
        ),
    },
    "single-cell-foundation-models": {
        "title": "Evaluating External scGPT & Geneformer Embeddings",
        "description": (
            "Use a standard-library evaluator to check externally generated scGPT or Geneformer "
            "embedding exports with donor-held-out kNN; first run a deliberately synthetic software "
            "check. This lesson includes no model output, inference, or biological accuracy claim."
        ),
        "neighbors": (
            "tutorials/protein-structure-design-alphafold.html",
            "tutorials/ai-prompt-engineering-seurat.html",
        ),
    },
}


class PageParser(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.metas: dict[str, str] = {}
        self.headings: list[str] = []
        self.title = ""
        self.jsonld: list[str] = []
        self.links: list[dict[str, str]] = []
        self._capture: str | None = None
        self._buffer: list[str] = []
        self._anchor: dict[str, str] | None = None
        self.feed(text)

    def handle_starttag(self, tag: str, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("name", attrs.get("property", ""))
            if key:
                self.metas[key] = attrs.get("content", "")
        if tag in ("h1", "title") or (tag == "script" and attrs.get("type") == "application/ld+json"):
            self._capture = tag
            self._buffer = []
        if tag == "a":
            self._anchor = {"href": attrs.get("href", ""), "title": attrs.get("title", ""), "text": ""}

    def handle_data(self, data: str):
        if self._capture:
            self._buffer.append(data)
        if self._anchor is not None:
            self._anchor["text"] += data

    def handle_endtag(self, tag: str):
        if tag == self._capture:
            value = "".join(self._buffer).strip()
            if tag == "h1":
                self.headings.append(value)
            elif tag == "title":
                self.title = value
            elif tag == "script":
                self.jsonld.append(value)
            self._capture = None
            self._buffer = []
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = self._anchor["text"].strip()
            self.links.append(self._anchor)
            self._anchor = None


def page(path: str) -> PageParser:
    return PageParser((ROOT / path).read_text(encoding="utf-8"))


class EditorialScopeFixTests(unittest.TestCase):
    def test_about_separates_executed_examples_from_guidance(self):
        text = (ROOT / "about.html").read_text(encoding="utf-8")
        self.assertNotIn("based entirely on direct benchmarking", text)
        self.assertIn("documentation-based conceptual guidance and reusable templates", text)
        self.assertIn("do not imply that a workflow was executed or directly benchmarked", text)
        self.assertIn("run and checked where stated", text)

    def test_retitled_pages_have_consistent_metadata_and_catalogue_entries(self):
        catalogue = (ROOT / "tutorials.html").read_text(encoding="utf-8")
        for slug, spec in RENAMED.items():
            with self.subTest(slug=slug):
                p = page(f"tutorials/{slug}.html")
                title = spec["title"]
                desc = spec["description"]
                self.assertEqual(p.title.split(" | ", 1)[0], title)
                self.assertEqual(p.headings, [title])
                self.assertEqual(p.metas.get("og:title"), title)
                self.assertEqual(p.metas.get("twitter:title"), title)
                for key in ("description", "og:description", "twitter:description"):
                    self.assertEqual(p.metas.get(key), desc)
                schema = [json.loads(item) for item in p.jsonld]
                article = next(item for item in schema if item.get("@type") == "TechArticle")
                self.assertEqual(article["headline"], title)
                self.assertEqual(article["name"], title)
                self.assertEqual(article["description"], desc)
                card_start = catalogue.index(f'data-search="{slug} ')
                card_start = catalogue.rfind("<article ", 0, card_start)
                card_end = catalogue.index("</article>", card_start) + len("</article>")
                card = catalogue[card_start:card_end]
                escaped_title = title.replace("&", "&amp;")
                self.assertIn(f"<h3", card)
                self.assertIn(escaped_title, card)
                self.assertIn(desc, card)
                self.assertIn(f'href="tutorials/{slug}.html"', card)

    def test_neighbor_navigation_uses_renamed_titles(self):
        for slug, spec in RENAMED.items():
            title = spec["title"]
            escaped_title = title.replace("&", "&amp;")
            target = f"{slug}.html"
            for neighbor in spec["neighbors"]:
                with self.subTest(target=target, neighbor=neighbor):
                    p = page(neighbor)
                    refs = [link for link in p.links if link["href"].endswith(target)]
                    self.assertTrue(refs, f"{neighbor} no longer links to {target}")
                    for ref in refs:
                        self.assertTrue(
                            ref["title"] in (title, escaped_title)
                            or title in ref["text"]
                            or escaped_title in ref["text"],
                            f"outdated/missing neighboring title in {neighbor}: {ref}",
                        )

    def test_mcp_page_is_server_selection_and_safe_evaluation_not_installation(self):
        text = (ROOT / "tutorials/mcp-zotero.html").read_text(encoding="utf-8")
        self.assertIn("server-selection and safety checklist", text)
        self.assertIn("not a universal installation walkthrough", text)
        self.assertIn("No server or Zotero records are supplied", text)
        self.assertIn("disposable test collection", text)
        self.assertIn("verify a read-only test", text)
        self.assertIn("No MCP server installation or live Zotero test is included.", text)

    def test_embedding_evaluator_foregrounds_external_vectors_and_synthetic_check(self):
        text = (ROOT / "tutorials/single-cell-foundation-models.html").read_text(encoding="utf-8")
        self.assertIn("evaluator for externally generated scGPT or Geneformer embedding exports", text)
        self.assertIn("deliberately synthetic fixture", text)
        self.assertIn("not scGPT or Geneformer outputs", text)
        self.assertIn("no pretrained model output or biological accuracy claim is supplied", text)
        self.assertIn("no pretrained model output is supplied", text)

    def test_methods_table_compares_inputs_outputs_and_assumptions(self):
        text = (ROOT / "tutorials/modern-bioinformatics-methods-2026.html").read_text(encoding="utf-8")
        required_headers = (
            "Method area and examples",
            "Minimum inputs",
            "Expected output",
            "Key assumption or check",
        )
        for header in required_headers:
            self.assertIn(f"<th scope=\"col\">{header}</th>", text)
        for area in (
            "Cell annotation",
            "Multimodal mapping",
            "Spatial neighborhoods",
            "Isoform discovery",
            "Trajectory or velocity",
            "Donor-aware differential expression",
        ):
            self.assertIn(area, text)
        self.assertIn("paired multimodal bridge data", text)
        self.assertIn("spliced/unspliced counts", text)
        self.assertIn("biological samples/donors are replicates", text.lower())


if __name__ == "__main__":
    unittest.main()
