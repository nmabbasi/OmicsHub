"""Normalization helper for the owner-approved tutorial header and reference refinements.

Reverses the date header and reference section refinements in the reviewed
tutorials back to the state expected by downstream historical regression normalizers.
"""

HEADER_REPLACEMENTS = {
    "tutorials/python-fundamentals-bioinformatics.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-09-22</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-09-22</span><span>· Updated 2026-10-25</span></div>',
    ),
    "tutorials/r-tidyverse-fundamentals.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-09-05</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-09-05</span><span>· Updated 2026-10-24</span></div>',
    ),
    "tutorials/research-reporting-interpretation.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-08-29</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Foundations &amp; Prerequisites</span><span>-</span><span>2026-08-29</span><span>· Updated 2026-10-25</span></div>',
    ),
    "tutorials/ai-bioinformatics-github-copilot.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span>-</span><span>2026-09-03</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span>•</span><span>Updated 2026-10-25</span></div>',
    ),
    "tutorials/ai-coding-cursor-aider.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span>-</span><span>2026-09-08</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span>•</span><span>Updated 2026-10-25</span></div>',
    ),
    "tutorials/autonomous-research-orchestrator.html": (
        '<div class="flex flex-wrap items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span>-</span><span>2026-08-27</span></div>',
        '<div class="flex flex-wrap items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>AI-Driven Research &amp; Agentic Bioinformatics</span><span aria-hidden="true">•</span><span>Updated 2026-10-25</span></div>',
    ),
    "tutorials/advanced-ai-single-cell.html": (
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Advanced Single-Cell Analysis</span><span>-</span><span>2026-08-25</span></div>',
        '<div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4"><span>Advanced Single-Cell Analysis</span><span>•</span><span>2026-08-25</span></div>',
    ),
    "tutorials/hpc-connection.html": (
        '<p>This lesson does not test a connection to any particular HPC system. Hostnames, key-registration processes, transfer endpoints, scheduler rules, and graphical access vary by institution.</p>\n<h2>Official documentation</h2>\n<ul>\n<li><a href="https://man.openbsd.org/ssh.1" rel="noopener" target="_blank">OpenSSH: ssh(1) manual page</a></li>\n<li><a href="https://man.openbsd.org/ssh-keygen.1" rel="noopener" target="_blank">OpenSSH: ssh-keygen(1) manual page</a></li>\n<li><a href="https://man.openbsd.org/ssh_config.5" rel="noopener" target="_blank">OpenSSH: ssh_config(5) manual page</a></li>\n<li><a href="https://download.samba.org/pub/rsync/rsync.1" rel="noopener" target="_blank">rsync(1) manual page</a></li>\n</ul>',
        '<p>This lesson does not test a connection to any particular HPC system. Hostnames, key-registration processes, transfer endpoints, scheduler rules, and graphical access vary by institution.</p>',
    ),
    "tutorials/experimental-design-batch-effects.html": (
        '<h2>References</h2>\n<p>For additional method details, consult the <a href="https://www.bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html">DESeq2 vignette</a>, the <a href="https://bioconductor.org/packages/devel/bioc/vignettes/sva/inst/doc/sva.pdf">Bioconductor sva vignette</a>, and R\'s <a href="https://stat.ethz.ch/R-manual/R-devel/library/stats/html/prcomp.html"><code>prcomp</code> documentation</a>. These examples do not replace method-specific analysis guidance.</p>',
        '<p>For additional method details, consult the <a href="https://www.bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html">DESeq2 vignette</a>, the <a href="https://bioconductor.org/packages/devel/bioc/vignettes/sva/inst/doc/sva.pdf">Bioconductor sva vignette</a>, and R\'s <a href="https://stat.ethz.ch/R-manual/R-devel/library/stats/html/prcomp.html"><code>prcomp</code> documentation</a>. These examples do not replace method-specific analysis guidance.</p>',
    ),
}


def normalize_header_date_fix(relative_path, text):
    """Restore the previous date header or reference block for historical normalizer chains."""
    if not isinstance(text, str):
        raise TypeError("header date fix normalization requires decoded text")
    if "20261026-startup-v1" not in text:
        return text
    pair = HEADER_REPLACEMENTS.get(relative_path)
    if pair is None:
        return text
    clean, original = pair
    if clean in text and (original not in text or original in clean):
        text = text.replace(clean, original, 1)
    return text
