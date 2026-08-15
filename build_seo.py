import os
import re

# Ensure tutorials directory exists
os.makedirs('tutorials', exist_ok=True)

# Read base HTML (we will strip the main content and replace it)
with open('index.html', 'r') as f:
    base_html = f.read()

# Extract the header and footer from index.html to wrap our tutorial pages
# We'll split the HTML at the <main> tag
header_split = base_html.split('<main class="min-h-screen">')
footer_split = header_split[1].split('</main>')

header_html = header_split[0] + '<main class="min-h-screen">\n'
footer_html = '\n</main>' + footer_split[1]

# Adjust paths in header and footer since these pages will be in /tutorials/ subfolder
# Actually, it's easier to put the HTML files in the root directory (e.g., tutorial_name.html)
# That way, image paths (images/...) and css paths (style.css) remain perfectly intact!

sitemap_urls = []

lessons_dir = 'lessons'
for filename in os.listdir(lessons_dir):
    if not filename.endswith('.md'):
        continue
        
    filepath = os.path.join(lessons_dir, filename)
    tutorial_id = filename.replace('.md', '')
    
    with open(filepath, 'r') as f:
        md_content = f.read()
        
    # Parse frontmatter
    title = tutorial_id.replace('-', ' ').title()
    excerpt = ""
    
    frontmatter_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', md_content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        title_match = re.search(r'title:\s*"([^"]+)"', frontmatter)
        if title_match:
            title = title_match.group(1)
            
        excerpt_match = re.search(r'excerpt:\s*"([^"]+)"', frontmatter)
        if excerpt_match:
            excerpt = excerpt_match.group(1)
    
    # Create customized header
    custom_header = header_html.replace(
        '<title>Bioinformatics Workflow Hub | Learn Bioinformatics and Single-cell RNA-seq Step by Step</title>',
        f'<title>{title} | Bioinformatics Workflow Hub</title>'
    )
    
    if excerpt:
        custom_header = re.sub(
            r'<meta content="[^"]+" name="description"/>',
            f'<meta content="{excerpt}" name="description"/>',
            custom_header
        )
        
    # Also adjust the canonical URL for OpenGraph
    custom_header = re.sub(
        r'<meta content="https://nmabbasi.github.io/OmicsHub" property="og:url"/>',
        f'<meta content="https://theomicshub.com/{tutorial_id}.html" property="og:url"/>',
        custom_header
    )
    
    custom_header = re.sub(
        r'<meta content="Bioinformatics Workflow Hub - Learn Bioinformatics and Single-cell RNA-seq Step by Step" property="og:title"/>',
        f'<meta content="{title} | Bioinformatics Workflow Hub" property="og:title"/>',
        custom_header
    )

    # Build the page content
    page_content = f"""
    <!-- Tutorial Detail Page (Pre-rendered for SEO) -->
    <div class="page-content" id="tutorial-page">
        <div class="container mx-auto px-4 py-8">
            <div class="max-w-4xl mx-auto">
                <!-- SEO Hidden Markdown Data -->
                <div id="seo-markdown-data" style="display:none;">
{md_content}
                </div>
                <!-- Rendered content will be injected here by script.js -->
                <div id="tutorial-content">
                    <div class="text-center py-20">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mb-4"></div>
                        <p class="text-gray-600 font-medium">Rendering tutorial...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tell script.js to render THIS specific page's hidden markdown on load
        window.PRELOADED_TUTORIAL_ID = "{tutorial_id}";
    </script>
    """
    
    final_html = custom_header + page_content + footer_html
    
    # Save the file to the root directory
    out_path = f'{tutorial_id}.html'
    with open(out_path, 'w') as f:
        f.write(final_html)
        
    sitemap_urls.append(f'https://theomicshub.com/{tutorial_id}.html')
    print(f"Generated {out_path}")

# Generate Sitemap
sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap_content += '  <url>\n    <loc>https://theomicshub.com/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
for url in sitemap_urls:
    sitemap_content += f'  <url>\n    <loc>{url}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
sitemap_content += '</urlset>'

with open('sitemap.xml', 'w') as f:
    f.write(sitemap_content)
    
print("Generated sitemap.xml")
