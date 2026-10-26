"""Exact allowlist and restoration checks for the seven optional notebook reports."""
from html import escape, unescape
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_REPORT_BASELINE = "f173d664e3023a9d74b0bc353dec621eed8ed5e9"
STYLE = (
    "background:#f4f7fa;border:1px solid #c7d2dd;border-left:5px solid #35566f;"
    "border-radius:4px;box-sizing:border-box;color:#223746;line-height:1.55;"
    "margin:1rem 0 1.25rem;max-width:100%;overflow-wrap:anywhere;padding:0.9rem 1rem;"
)

REPORT_NOTES = {
    "tutorials/examples/Combined_LIANA_Analysis_Conserved_Specific_Signaling.html": (
        "Status: results are internally inconsistent and unverified.",
        "This page names seven inputs (L1-L7), but a cached conservation table reports eight cell lines. "
        "An earlier section uses a threshold of at least five, while later code and the summary use four. "
        "The later “specific interactions” section repeats conserved output, and the page logs “zero-length "
        "variable name.” The cached counts and plots should not be interpreted as verified results. Reconcile "
        "the inputs and threshold, then rerun before drawing conclusions. This review does not infer replacement values.",
    ),
    "tutorials/examples/Trajectory_inference_using_Slingshot.html": (
        "Status: failed and incomplete run; not a valid trajectory result.",
        "Section 4 records “Error: object 'All_samples_Merged' not found.” Later cells still show outputs, "
        "including “curves: 0” and multiple NA values. Those cached outputs do not establish a valid trajectory "
        "or pseudotime. Restore the intended input object and rerun before interpreting downstream plots or "
        "summaries. No trajectory result was reconstructed in this review.",
    ),
    "tutorials/examples/inferCNV_analysis.html": (
        "Status: incomplete; required inputs and a successful result are not shown.",
        "The page depends on an external Seurat object and two inferCNV RDS inputs. In the score-to-plot code, "
        "the `sample <- All_samples_Merged` assignment is commented out although later code uses `sample`; "
        "a plotting call has an empty trailing argument and a standalone `p`. No successful inferCNV plot or "
        "result is shown. The data-dependent code is left unchanged because the inputs are unavailable here.",
    ),
    "tutorials/examples/scASSIST_AI_METHOD.html": (
        "Status: saved recommendations contain corrected arithmetic and resource caveats.",
        "The saved 30,000 nCount_RNA cutoff is 2,495 above its stated 95th percentile (27,505), and the "
        "6,000 nFeature_RNA cutoff is 468 above its stated 95th percentile (5,532). Neither value is below "
        "its stated percentile. These are dataset-specific exploratory heuristics, not biological rules. The "
        "page also logs a sparse-to-dense allocation warning for 13.4 GiB. That warning does not prove the "
        "allocation completed or that the full workflow ran; check available memory and scope before rerunning.",
    ),
    "tutorials/examples/mLLM_Annotatin_of_all_clusters.html": (
        "Status: incomplete provider responses; a complete six-model consensus is not demonstrated.",
        "The saved logs show a missing API key, quota or credit failures, and “No valid responses” for cluster 0. "
        "An isolated prediction is visible for one cluster, but no complete all-cluster annotation summary is "
        "shown. Do not treat this run as validated labels or a completed consensus. A successful run with the "
        "required provider access would be needed to support those conclusions; no annotations were fabricated here.",
    ),
    "tutorials/examples/Integration_by_CCA_Harmony.html": (
        "Status: incomplete; a complete, reproducible integration run is not demonstrated.",
        "The embedded source calls `load(\"AllSample_corrected_AzimuthAnnotated_L1.Robj\")`; that "
        "workstation-relative file is not included in this HTML export. Later plot code calls "
        "`DimPlot(alldata.int, ...)`, but no explicit assignment creating `alldata.int` appears in the embedded "
        "source. Because the input is unavailable, we cannot verify whether it supplies that object. Saved plots "
        "are cached output, not proof that the workflow can be rerun. This review did not access the input or "
        "rerun the analysis.",
    ),
    "tutorials/examples/CyteTypeR_Annotation_using_AI_Finalized.html": (
        "Status: incomplete workflow example; completed annotations are not displayed.",
        "The page requires the external Seurat RDS file named in “Load Seurat Object.” Its visible output "
        "shows marker finding and blacklist filtering, including a list of removed markers, but no completed "
        "CyteTypeR labels or annotation summary. The title has been changed to remove “Finalized,” which the "
        "displayed content does not support.",
    ),
}
OPTIONAL_REPORT_PATHS = frozenset(REPORT_NOTES)


def status_note_markup(relative_path):
    heading, body = REPORT_NOTES[relative_path]
    return (
        '<aside class="optional-report-status" role="note" aria-label="Report status" '
        f'style="{STYLE}">'
        f'<p style="margin:0 0 .45rem;"><strong>{escape(heading, quote=False)}</strong></p>'
        f'<p style="margin:0;">{escape(body, quote=False)}</p></aside>'
    )


def published_report_bytes(relative_path):
    if relative_path not in OPTIONAL_REPORT_PATHS:
        raise AssertionError(f"not an approved optional report: {relative_path}")
    return subprocess.check_output(
        ["git", "show", f"{PUBLISHED_REPORT_BASELINE}:{relative_path}"], cwd=ROOT
    )


def _replace_once(text, before, after, label):
    count = text.count(before)
    if count != 1:
        raise AssertionError(f"expected one exact {label} change, found {count}")
    return text.replace(before, after, 1)


def normalize_optional_report(relative_path, content):
    if relative_path not in OPTIONAL_REPORT_PATHS:
        return content
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    note = status_note_markup(relative_path)
    text = _replace_once(text, note + "\n\n", "", f"{relative_path} status note")

    if relative_path.endswith("/scASSIST_AI_METHOD.html"):
        new_count = (
            "This value is above the displayed 95th percentile (27,505) by 2,495. It is a dataset-specific "
            "heuristic from this saved recommendation, not a universal biological rule. Check it against the "
            "dataset and analysis goal before use."
        )
        old_count = (
            "This value is chosen to be below the 95th percentile (27505) to remove high count outliers, "
            "which may represent cell doublets or other artifacts.  The value is set slightly higher to allow "
            "for some variability in highly expressing cells."
        )
        new_feature = (
            "This value is above the displayed 95th percentile (5,532) by 468. It is a dataset-specific "
            "heuristic from this saved recommendation, not a universal biological rule. Check it against the "
            "dataset and analysis goal before use."
        )
        old_feature = (
            "This value is slightly below the 95th percentile (5532) to remove cells with an unusually high "
            "number of detected genes, which may indicate doublets or other artifacts."
        )
        text = _replace_once(text, new_count, old_count, "nCount_RNA recommendation")
        text = _replace_once(text, new_feature, old_feature, "nFeature_RNA recommendation")

    if relative_path.endswith("/CyteTypeR_Annotation_using_AI_Finalized.html"):
        old_title = "CyteTypeR Annotation using AI-Finalized"
        new_title = "CyteTypeR Annotation Using AI: Incomplete Example"
        new_h1 = f'<h1 class="title toc-ignore">{new_title}</h1>'
        old_h1 = '<h1 class="title toc-ignore">CyteTypeR Annotation using\nAI-Finalized</h1>'
        text = _replace_once(text, new_h1, old_h1, "CyteTypeR visible title")
        count = text.count(new_title)
        if count != 4:
            raise AssertionError(f"expected four metadata title replacements, found {count}")
        text = text.replace(new_title, old_title)

    return text.encode("utf-8") if isinstance(content, bytes) else text


def verify_optional_report_file(relative_path, content):
    if relative_path not in OPTIONAL_REPORT_PATHS:
        raise AssertionError(f"not an approved optional report: {relative_path}")
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    note = status_note_markup(relative_path)
    if text.count(note) != 1:
        raise AssertionError(f"expected one exact status note in {relative_path}")
    if "\u2014" in unescape(note):
        raise AssertionError(f"em dash in status note: {relative_path}")

    robots = []
    for tag in re.findall(r"<meta\b[^>]*>", text, re.I):
        attrs = dict(re.findall(r"([\w:-]+)\s*=\s*['\"]([^'\"]*)['\"]", tag))
        if attrs.get("name", "").lower() == "robots":
            robots.append(attrs.get("content", "").lower())
    if not any("noindex" in value for value in robots):
        raise AssertionError(f"noindex metadata missing from {relative_path}")
    if re.search(r"adsbygoogle|pagead\.googlesyndication|google_ad_client|data-ad-client|doubleclick\.net", text, re.I):
        raise AssertionError(f"advertising code found in {relative_path}")

    visible = unescape(text)
    if relative_path.endswith("/scASSIST_AI_METHOD.html"):
        for phrase in (
            "above the displayed 95th percentile (27,505) by 2,495",
            "above the displayed 95th percentile (5,532) by 468",
            "not biological rules",
            "13.4 GiB",
        ):
            if phrase not in visible:
                raise AssertionError(f"missing scASSIST correction {phrase!r}")
    if relative_path.endswith("/CyteTypeR_Annotation_using_AI_Finalized.html"):
        title_match = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
        h1_match = re.search(r'<h1 class="title toc-ignore">(.*?)</h1>', text, re.S | re.I)
        if not title_match or not h1_match:
            raise AssertionError("CyteTypeR title elements are missing")
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", unescape(h1_match.group(1)))).strip()
        expected = "CyteTypeR Annotation Using AI: Incomplete Example"
        if title_match.group(1) != expected or title != expected:
            raise AssertionError("CyteTypeR document title and visible heading must both say Incomplete Example")

    normalized = normalize_optional_report(relative_path, content)
    expected = published_report_bytes(relative_path)
    if normalized != expected:
        raise AssertionError(
            f"unapproved content or markup change remains in {relative_path} after exact restoration"
        )
    return True
