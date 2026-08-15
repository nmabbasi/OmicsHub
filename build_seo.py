import os
import re
import markdown

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

from inject_html_cards import tutorial_files

# Use the explicitly ordered list instead of os.listdir
sitemap_urls = []
lessons_dir = 'lessons'

for index, filename in enumerate(tutorial_files):
    filepath = os.path.join(lessons_dir, filename)
    if not os.path.exists(filepath): continue
    
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
        '<title>The Omics Hub | Learn Bioinformatics and Single-cell RNA-seq Step by Step</title>',
        f'<title>{title} | The Omics Hub</title>'
    )
    
    if excerpt:
        custom_header = re.sub(
            r'<meta content="[^"]+" name="description"/>',
            f'<meta content="{excerpt}" name="description"/>',
            custom_header
        )
        
    # Also adjust the canonical URL for OpenGraph
    custom_header = re.sub(
        r'<meta content="https://theomicshub.com" property="og:url"/>',
        f'<meta content="https://theomicshub.com/{tutorial_id}.html" property="og:url"/>',
        custom_header
    )
    
    custom_header = re.sub(
        r'<meta content="The Omics Hub \| Learn Bioinformatics and Single-cell RNA-seq Step by Step" property="og:title"/>',
        f'<meta content="{title} | The Omics Hub" property="og:title"/>',
        custom_header
    )

    # Convert markdown body to HTML
    body_md = md_content.split('---', 2)[-1]
    rendered_html = markdown.markdown(body_md, extensions=['fenced_code', 'tables'])
    
    date_str = ""
    date_match = re.search(r'date:\s*"([^"]+)"', frontmatter)
    if date_match: date_str = date_match.group(1)
        
    author_str = "Nasir Mahmood Abbasi, PhD"
    author_match = re.search(r'author:\s*"([^"]+)"', frontmatter)
    if author_match: author_str = author_match.group(1)
        
    cat_str = "Tutorial"
    cat_match = re.search(r'category:\s*"([^"]+)"', frontmatter)
    if cat_match: cat_str = cat_match.group(1)
        
    img_str = ""
    img_match = re.search(r'image:\s*"([^"]+)"', frontmatter)
    if img_match: img_str = img_match.group(1)

    initials = "".join([n[0] for n in author_str.split(" ")]).upper()[:2]
    
    img_html = f'''
            <div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100">
                <img src="{img_str}" alt="{title}" class="w-full h-auto object-cover aspect-video">
            </div>
    ''' if img_str else ""

    # --- Generate Previous/Next Navigation ---
    prev_html = ""
    next_html = ""
    
    def get_tutorial_title(file_name):
        try:
            with open(os.path.join(lessons_dir, file_name), 'r') as f:
                c = f.read()
            m = re.search(r'title:\s*"([^"]+)"', c)
            if m: return m.group(1)
        except Exception:
            pass
        return file_name.replace('.md', '').replace('-', ' ').title()

    if index > 0:
        prev_file = tutorial_files[index - 1]
        prev_id = prev_file.replace('.md', '')
        prev_title = get_tutorial_title(prev_file)
        prev_html = f'''
        <a href="{prev_id}.html" class="flex-1 flex flex-col p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all text-left group">
            <span class="text-xs text-gray-500 font-bold tracking-wider uppercase mb-1 group-hover:text-blue-500">← Previous Tutorial</span>
            <span class="text-gray-900 font-medium group-hover:text-blue-600 line-clamp-2">{prev_title}</span>
        </a>
        '''
        
    if index < len(tutorial_files) - 1:
        next_file = tutorial_files[index + 1]
        next_id = next_file.replace('.md', '')
        next_title = get_tutorial_title(next_file)
        next_html = f'''
        <a href="{next_id}.html" class="flex-1 flex flex-col p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-sm transition-all text-right group">
            <span class="text-xs text-gray-500 font-bold tracking-wider uppercase mb-1 group-hover:text-blue-500">Next Tutorial →</span>
            <span class="text-gray-900 font-medium group-hover:text-blue-600 line-clamp-2">{next_title}</span>
        </a>
        '''
        
    nav_html = f'''
    <div class="mt-16 pt-8 border-t border-gray-200">
        <h3 class="text-xl font-bold text-gray-900 mb-6">Continue Learning</h3>
        <div class="flex flex-col sm:flex-row gap-4">
            {prev_html if prev_html else '<div class="flex-1"></div>'}
            {next_html if next_html else '<div class="flex-1"></div>'}
        </div>
    </div>
    '''

    static_content = f'''
            <div class="mb-12">
                <div class="flex items-center gap-2 text-sm text-blue-600 font-medium mb-4">
                    <span>{cat_str}</span>
                    <span>•</span>
                    <span>{date_str}</span>
                </div>
                <h1 class="text-4xl md:text-5xl font-black text-gray-900 mb-6 leading-tight">{title}</h1>
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold text-lg">
                        {initials}
                    </div>
                    <div>
                        <p class="font-bold text-gray-900">{author_str}</p>
                        <p class="text-sm text-gray-500">Bioinformatics Educator</p>
                    </div>
                </div>
            </div>
            
            {img_html}
            
            <div class="prose prose-blue prose-lg max-w-none">
                {rendered_html}
            </div>
            
            {nav_html}
    '''

    # Build JSON-LD structured data for SEO
    json_ld = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{excerpt}",
      "author": {{
        "@type": "Person",
        "name": "Nasir Mahmood Abbasi, PhD",
        "url": "https://theomicshub.com/about.html"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "The Omics Hub",
        "logo": {{
          "@type": "ImageObject",
          "url": "https://theomicshub.com/images/default-tutorial.png"
        }}
      }}
    }}
    </script>
    """
    
    canonical_tag = f'<link rel="canonical" href="https://theomicshub.com/{tutorial_id}.html" />'
    
    # Inject canonical and JSON-LD before </head>
    custom_header = custom_header.replace('</head>', f'{canonical_tag}\\n{json_ld}\\n</head>')

    # Build the page content
    page_content = f"""
    <!-- Tutorial Detail Page (Pre-rendered for SEO and Instant Load) -->
    <div class="page-content" id="tutorial-page">
        <div class="container mx-auto px-4 py-8">
            <div class="max-w-4xl mx-auto">
                <!-- SEO Hidden Markdown Data for search/index -->
                <div id="seo-markdown-data" style="display:none;">
{md_content}
                </div>
                <!-- PRE-RENDERED STATIC HTML -->
                <div id="tutorial-content">
                    {static_content}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tell script.js to skip rendering because it is already done
        window.STATIC_RENDERED = true;
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
