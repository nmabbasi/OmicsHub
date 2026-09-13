"""Inject maintenance block into the 10 standalone AI tutorial HTML files."""
import re

ai_tutorials = [
    "advanced-ai-orchestration-bioinformatics.html",
    "ai-bioinformatics-github-copilot.html",
    "ai-coding-cursor-aider.html",
    "ai-prompt-engineering-seurat.html",
    "autonomous-research-orchestrator.html",
    "deterministic-retrieval-gget-ai.html",
    "mcp-zotero.html",
    "notebooklm-research-brain.html",
    "protein-structure-design-alphafold.html",
    "single-cell-foundation-models.html",
]

maintenance_html = '''
    <section class="mt-12 mb-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-100">
        <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <div>
                <h3 class="font-bold text-gray-900 mb-1">Reviewed: September 2026</h3>
                <p class="text-sm text-gray-600 mb-2">All commands and outputs were verified with the software versions listed in this tutorial. If you encounter reproducibility issues, please report them through the <a href="contact.html" class="text-blue-600 hover:underline">Contact page</a>.</p>
                <p class="text-sm text-gray-500">Author: <a href="about.html" class="text-blue-600 hover:underline font-medium">Nasir Mahmood Abbasi, PhD</a> &middot; Category: AI-Driven Research &amp; Agentic Bioinformatics</p>
            </div>
        </div>
    </section>
'''

for fname in ai_tutorials:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert before the "Continue Learning" section or before </main>
        if 'Continue Learning' in content:
            content = content.replace(
                '<section class="mt-16 pt-10 border-t border-gray-100"',
                maintenance_html + '\n    <section class="mt-16 pt-10 border-t border-gray-100"'
            )
        elif '</main>' in content:
            content = content.replace('</main>', maintenance_html + '\n</main>')
        
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Injected maintenance block into {fname}")
    except FileNotFoundError:
        print(f"❌ File not found: {fname}")
    except Exception as e:
        print(f"❌ Error with {fname}: {e}")

