"""Normalization helper for the owner-approved single date header fixes.

Reverses the date header in the three reviewed tutorials back to the
state expected by downstream historical regression normalizers.
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
}


def normalize_header_date_fix(relative_path, text):
    """Restore the previous date header for historical normalizer chains."""
    if not isinstance(text, str):
        raise TypeError("header date fix normalization requires decoded text")
    if '"dateModified": "2026-10-25"' not in text:
        return text
    pair = HEADER_REPLACEMENTS.get(relative_path)
    if pair is None:
        return text
    clean, original = pair
    if clean in text and original not in text:
        text = text.replace(clean, original, 1)
    return text
