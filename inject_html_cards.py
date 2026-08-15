import os
import re

tutorial_files = [
    'introduction-to-bioinformatics.md',
    'modern-bioinformatics-methods-2026.md',
    'docker-singularity-bioinformatics.md',
    'reproducible-workflows-snakemake-nextflow.md',
    '1-Connection.md',
    '2-HPC_Basic_Commands.md',
    '4-Support.md',
    'command-line-part1.md',
    'command-line-part2.md',
    'command-line-part3.md',
    'hpc-submission-part1.md',
    'conda-mamba-part1.md',
    '16s-rrna-prokka-annotation.md',
    'metagenomics-kraken2-bracken.md',
    'metagenomics-assembly-mapping.md',
    'metatranscriptomics-guide.md',
    'metatranscriptomics-functional-pathways.md',
    'evolutionary-phylogeny-analysis.md',
    'phylogenomics-orthofinder.md',
    'wes-variant-calling-pipeline.md',
    'scrna-seq-basics.md',
    'scrna-seq-integration-strategies.md',
    'scrna-seq-downstream-analysis.md',
    'scrna-seq-trajectory-inference.md',
    'transcriptomics-differential-expression.md',
    'scrna-seq-quality-control.md',
    'advanced-visualization-packages.md',
    'tcr-bcr-repertoire-analysis.md',
    'cell-cell-communication.md',
    'cell-type-annotation-methods.md',
    'advanced-ai-single-cell.md',
    'infercnv-copy-number-variation.md',
    'single-cell-deconvolution.md',
    'cite-seq-wnn-multiomics.md',
    'spatial-transcriptomics-r-python.md',
    'long-read-pacbio-nanopore.md'
]

tutorials = []
categories_set = set()

for file in tutorial_files:
    path = os.path.join('lessons', file)
    if not os.path.exists(path): continue
    
    with open(path, 'r') as f:
        content = f.read()
        
    id_str = file.replace('.md', '')
    title = id_str.replace('-', ' ').title()
    category = "Uncategorized"
    date_str = "2026-08-15"
    image = ""
    excerpt = ""
    
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        fm = match.group(1)
        m_title = re.search(r'title:\s*"([^"]+)"', fm)
        if m_title: title = m_title.group(1)
        m_cat = re.search(r'category:\s*"([^"]+)"', fm)
        if m_cat: category = m_cat.group(1)
        m_date = re.search(r'date:\s*"([^"]+)"', fm)
        if m_date: date_str = m_date.group(1)
        m_img = re.search(r'image:\s*"([^"]+)"', fm)
        if m_img: image = m_img.group(1)
        m_exc = re.search(r'excerpt:\s*"([^"]+)"', fm)
        if m_exc: excerpt = m_exc.group(1)
        
    categories_set.add(category)
    tutorials.append({
        'id': id_str,
        'title': title,
        'category': category,
        'date': date_str,
        'image': image,
        'excerpt': excerpt
    })

def render_home_card(t):
    img_html = f'<div class="w-full aspect-video relative overflow-hidden border-b border-gray-100 bg-gray-50"><img src="{t["image"]}" alt="{t["title"]}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 hover:scale-105"></div>' if t["image"] else ''
    return f'''
        <article class="tutorial-card cursor-pointer" onclick="window.location.href='{t["id"]}.html'">
            {img_html}
            <div class="p-6 flex flex-col flex-grow">
                <div class="flex items-center justify-between mb-3">
                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">{t["category"]}</span>
                    <span class="text-sm text-gray-500 font-medium">{t["date"]}</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">{t["title"]}</h3>
                <p class="excerpt text-gray-600 mb-4">{t["excerpt"]}</p>
                <a href="{t["id"]}.html" class="text-blue-600 hover:underline font-semibold">Read More →</a>
            </div>
        </article>'''

def render_grid_card(t):
    return f'''
        <article class="bg-white rounded-lg shadow-md overflow-hidden transform transition-transform hover:scale-105 duration-300 cursor-pointer" onclick="window.location.href='{t["id"]}.html'">
            <img src="{t["image"]}" alt="{t["title"]}" class="w-full h-48 object-cover">
            <div class="p-6 flex flex-col flex-grow">
                <div class="flex items-center justify-between mb-3">
                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">{t["category"]}</span>
                    <span class="text-sm text-gray-500">{t["date"]}</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">{t["title"]}</h3>
                <p class="text-gray-700 text-base mb-4 line-clamp-3">{t["excerpt"]}</p>
                <a href="{t["id"]}.html" class="text-blue-600 hover:underline font-semibold mt-auto block">Read More →</a>
            </div>
        </article>'''

home_cards_html = "".join(render_home_card(t) for t in tutorials)
grid_cards_html = "".join(render_grid_card(t) for t in tutorials)

# Categories
cat_html = ""
for c in sorted(list(categories_set)):
    cat_html += f'<button class="sidebar-category w-full text-left px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors" onclick="filterTutorials(\'{c}\')">{c}</button>\n'

# Recent posts
recent_html = ""
for t in tutorials[:5]:
    recent_html += f'''
        <a href="{t["id"]}.html" class="sidebar-link group block px-3 py-2 rounded-md hover:bg-gray-50 transition-colors">
            <div class="font-medium text-sm text-gray-900 group-hover:text-blue-600 mb-1">{t["title"]}</div>
            <div class="text-xs text-gray-500">{t["category"]}</div>
        </a>'''

with open('index.html', 'r') as f:
    index_html = f.read()

# Replace tutorials-list
index_html = re.sub(
    r'(<div class="space-y-5" id="tutorials-list">).*?(</div>\s*</div>\s*<!-- Sidebar -->)',
    rf'\1\n{home_cards_html}\n\2',
    index_html,
    flags=re.DOTALL
)

# Replace all-tutorials-list
index_html = re.sub(
    r'(<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6" id="all-tutorials-list">).*?(</div>\s*</div>\s*</div>\s*</div>)',
    rf'\1\n{grid_cards_html}\n\2',
    index_html,
    flags=re.DOTALL
)

# Replace categories-list
index_html = re.sub(
    r'(<div class="space-y-1 mb-7" id="categories-list">).*?(</div>\s*<h3 class="text-xs font-bold text-gray-400 mb-3 uppercase tracking-widest">Recent Posts</h3>)',
    rf'\1\n{cat_html}\n\2',
    index_html,
    flags=re.DOTALL
)

# Replace recent-posts
index_html = re.sub(
    r'(<div class="space-y-2" id="recent-posts">).*?(</div>\s*</div>\s*</div>\s*</div>\s*</section>)',
    rf'\1\n{recent_html}\n\2',
    index_html,
    flags=re.DOTALL
)

with open('index.html', 'w') as f:
    f.write(index_html)
    
print("Successfully injected pre-rendered HTML cards into index.html")
