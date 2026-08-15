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

from inject_html_cards import tutorials

sitemap_urls = []
lessons_dir = 'lessons'

for index, tut in enumerate(tutorials):
    filename = tut['id'] + '.md'
    filepath = os.path.join(lessons_dir, filename)
    if not os.path.exists(filepath): continue
    
    tutorial_id = tut['id']
    cat_str = tut['category']
    
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
    
    date_str = tut['date']
    author_str = "Nasir Mahmood Abbasi, PhD"
    author_match = re.search(r'author:\s*"([^"]+)"', frontmatter)
    if author_match: author_str = author_match.group(1)
        
    img_str = tut['image']

    initials = "".join([n[0] for n in author_str.split(" ")]).upper()[:2]
    
    img_html = f'''
            <div class="mb-12 rounded-2xl overflow-hidden shadow-lg border border-gray-100">
                <img src="{img_str}" alt="{title}" class="w-full h-auto object-cover aspect-video">
            </div>
    ''' if img_str else ""

    # --- Generate Beautiful Intra-Category Previous/Next Navigation ---
    prev_html = ""
    next_html = ""
    
    # Get all tutorials in the current category
    cat_tuts = [t for t in tutorials if t['category'] == cat_str]
    current_cat_idx = next((i for i, t in enumerate(cat_tuts) if t['id'] == tutorial_id), 0)

    if current_cat_idx > 0:
        prev_tut = cat_tuts[current_cat_idx - 1]
        prev_html = f'''
        <a href="{prev_tut['id']}.html" class="group relative flex flex-col justify-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden text-left">
            <div class="absolute inset-0 bg-gradient-to-r from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div class="relative z-10 flex items-center gap-4">
                <div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-300">
                    <svg class="w-6 h-6 text-gray-400 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path></svg>
                </div>
                <div>
                    <span class="block text-xs font-bold tracking-widest text-gray-400 uppercase mb-1">Previous Lesson</span>
                    <span class="block text-gray-900 font-bold group-hover:text-blue-700 transition-colors line-clamp-2 leading-snug">{prev_tut['title']}</span>
                </div>
            </div>
        </a>
        '''
        
    if current_cat_idx < len(cat_tuts) - 1:
        next_tut = cat_tuts[current_cat_idx + 1]
        next_html = f'''
        <a href="{next_tut['id']}.html" class="group relative flex flex-col justify-center p-6 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden text-right">
            <div class="absolute inset-0 bg-gradient-to-l from-blue-50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div class="relative z-10 flex items-center justify-end gap-4">
                <div>
                    <span class="block text-xs font-bold tracking-widest text-gray-400 uppercase mb-1">Next Lesson</span>
                    <span class="block text-gray-900 font-bold group-hover:text-blue-700 transition-colors line-clamp-2 leading-snug">{next_tut['title']}</span>
                </div>
                <div class="w-12 h-12 flex-shrink-0 rounded-full bg-gray-50 flex items-center justify-center group-hover:bg-blue-600 transition-colors duration-300">
                    <svg class="w-6 h-6 text-gray-400 group-hover:text-white transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                </div>
            </div>
        </a>
        '''
        
    # Only show the section if there is at least one navigation button
    nav_html = f'''
    <div class="mt-16 pt-10 border-t border-gray-100">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <h3 class="text-2xl font-black text-gray-900 tracking-tight">Continue Learning</h3>
            <span class="inline-block bg-blue-50 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider">{cat_str}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {prev_html if prev_html else '<div></div>'}
            {next_html if next_html else '<div></div>'}
        </div>
    </div>
    ''' if (prev_html or next_html) else ""

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
