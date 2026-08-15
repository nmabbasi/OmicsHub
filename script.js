// OmicsHub Website JavaScript

// Global variables
let tutorials = [];
let currentPage = 'home';
let currentTutorial = null;

// Initialize the website
document.addEventListener('DOMContentLoaded', function() {
    if (window.PRELOADED_TUTORIAL_ID) {
        const seoData = document.getElementById('seo-markdown-data');
        if (window.STATIC_RENDERED) {
            // Already rendered statically by Python! Just show it.
            document.getElementById('tutorial-page').classList.remove('hidden');
            document.getElementById('home-page').classList.add('hidden');
            document.getElementById('services-page').classList.add('hidden');
            document.getElementById('contact-page').classList.add('hidden');
            document.getElementById('about-page').classList.add('hidden');
            window.scrollTo(0, 0);
            
            // Highlight code blocks
            if (window.hljs) {
                document.querySelectorAll('#tutorial-content pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            }
        } else if (seoData && seoData.textContent.trim()) {
            const tempTutorial = parseTutorial(seoData.textContent.trim(), window.PRELOADED_TUTORIAL_ID + '.md');
            if (tempTutorial) {
                tutorials = [tempTutorial];
                showTutorial(window.PRELOADED_TUTORIAL_ID, false);
            }
        }
    }
    handleInitialRoute();
    setupEventListeners();
    createBackToTopButton();
});

// Handle initial routing after tutorials load
function handleInitialRoute() {
    if (window.PRELOADED_TUTORIAL_ID) {
        showTutorial(window.PRELOADED_TUTORIAL_ID, false);
        return;
    }

    const hash = window.location.hash;
    if (hash) {
        if (hash.startsWith('#tutorial-')) {
            const tutorialId = hash.substring(10); // Remove '#tutorial-'
            window.location.href = `${tutorialId}.html`; // Redirect to real page
        } else if (hash === '#all-tutorials') {
            showTutorials();
        } else if (hash === '#tutorials') {
            showHome(true, true); // Prevent scroll to top
            setTimeout(() => {
                const el = document.getElementById('tutorials');
                if (el) el.scrollIntoView();
            }, 100);
        } else {
            showHome(); // Default to home if hash is not recognized
        }
    } else {
        showHome();
    }
}

// Setup event listeners
function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }

    // Accessible Legal dropdown: support click, Escape, and outside-click dismissal.
    const legalButton = document.getElementById('legal-menu-button');
    const legalMenu = document.getElementById('legal-menu');
    if (legalButton && legalMenu) {
        legalButton.addEventListener('click', function(event) {
            event.stopPropagation();
            const expanded = legalButton.getAttribute('aria-expanded') === 'true';
            legalButton.setAttribute('aria-expanded', String(!expanded));
            legalMenu.classList.toggle('opacity-0', expanded);
            legalMenu.classList.toggle('invisible', expanded);
        });
        legalMenu.querySelectorAll('a').forEach(link => link.setAttribute('role', 'menuitem'));
        document.addEventListener('click', function(event) {
            if (!legalButton.parentElement.contains(event.target)) {
                legalButton.setAttribute('aria-expanded', 'false');
                legalMenu.classList.add('opacity-0', 'invisible');
            }
        });
        legalButton.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                legalButton.setAttribute('aria-expanded', 'false');
                legalMenu.classList.add('opacity-0', 'invisible');
                legalButton.focus();
            }
        });
    }
    
    // Back to top button
    window.addEventListener('scroll', handleScroll);

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function(event) {
        const hash = window.location.hash;
        if (hash) {
            if (hash.startsWith('#tutorial-')) {
                const tutorialId = hash.substring(10);
                showTutorial(tutorialId, false); // false to prevent adding to history again
            } else if (hash === '#all-tutorials') {
                showTutorials(false);
            } else if (hash === '#tutorials') {
                showHome(false, true); // Prevent scroll to top
                setTimeout(() => {
                    const el = document.getElementById('tutorials');
                    if (el) el.scrollIntoView();
                }, 100);
            } else {
                showHome(false);
            }
        } else {
            showHome(false);
        }
    });
}

// Load tutorials from markdown files
async function loadTutorials() {
    try {
        // Check if we're running from file:// protocol (local file system)
        if (window.location.protocol === 'file:') {
            // Use fallback tutorials immediately for local file system
            showFallbackTutorials();
            return;
        }
        
        // List of tutorial files (you'll add more as you create them)
        const tutorialFiles = [
            // Introduction to Bioinformatics
            'introduction-to-bioinformatics.md',
            'modern-bioinformatics-methods-2026.md',
            
            // Shell Command Basics
            'command-line-part1.md',
            'command-line-part2.md',
            'command-line-part3.md',
            
            // Package Management
            'conda-mamba-part1.md',
            
            // High-Performance Computing (HPC)
            '1-Connection.md',
            '2-HPC_Basic_Commands.md',
            'hpc-submission-part1.md',
            '4-Support.md',
            
            // Workflow & Containerization
            'reproducible-workflows-snakemake-nextflow.md',
            'docker-singularity-bioinformatics.md',
            
            // Metagenomics
            '16s-rrna-prokka-annotation.md',
            'metagenomics-assembly-mapping.md',
            'metagenomics-kraken2-bracken.md',
            
            // Metatranscriptomics
            'metatranscriptomics-guide.md',
            'metatranscriptomics-functional-pathways.md',
            
            // Evolutionary Bioinformatics Analysis
            'evolutionary-phylogeny-analysis.md',
            'phylogenomics-orthofinder.md',
            
            // Genomics & Whole Exome Sequencing
            'wes-variant-calling-pipeline.md',
            
            // Single-Cell RNA-seq
            'scrna-seq-basics.md',
            'scrna-seq-integration-strategies.md',
            'scrna-seq-downstream-analysis.md',
            'scrna-seq-trajectory-inference.md',
            'transcriptomics-differential-expression.md',
            
            // Advanced Single-Cell Analysis
            'scrna-seq-quality-control.md',
            'advanced-visualization-packages.md',
            'tcr-bcr-repertoire-analysis.md',
            'cell-cell-communication.md',
            'cell-type-annotation-methods.md',
            'advanced-ai-single-cell.md',
            'infercnv-copy-number-variation.md',
            'single-cell-deconvolution.md',
            'cite-seq-wnn-multiomics.md',
            
            // Spatial Transcriptomics
            'spatial-transcriptomics-r-python.md',
            
            // Long-Read Sequencing
            'long-read-pacbio-nanopore.md'
        ];
        
        tutorials = [];
        
        const fetchPromises = tutorialFiles.map(async (file) => {
            try {
                let fetchPath = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                    ? `lessons/${file}`
                    : `lessons/${file}`;
                
                const response = await fetch(fetchPath);
                if (response.ok) {
                    const content = await response.text();
                    return parseTutorial(content, file);
                } else {
                    console.warn(`Could not load tutorial: ${file}. Status: ${response.status}`);
                    return null;
                }
            } catch (error) {
                console.warn(`Error fetching tutorial: ${file}`, error);
                return null;
            }
        });

        const results = await Promise.all(fetchPromises);
        
        // Merge the instantly-rendered tutorial with the fully loaded set
        const fullyLoadedTutorials = results.filter(t => t !== null);
        
        if (tutorials.length > 0 && window.PRELOADED_TUTORIAL_ID) {
            // If we are currently viewing a preloaded tutorial, seamlessly swap in the full array 
            // without interrupting the UI state.
            tutorials = fullyLoadedTutorials;
        } else {
            tutorials = fullyLoadedTutorials;
        }
        
        // We intentionally DO NOT sort by date anymore.
        // The tutorials will render in the exact pedagogical order defined in the tutorialFiles array above,
        // ensuring beginners start with the Introduction and end with Advanced Single-Cell analysis.
        
        // Handle routing now that tutorials are loaded (deprecated)
        handleInitialRoute();
        
    } catch (error) {
        console.error('Error loading tutorials:', error);
        // Show fallback content if all fetches fail
        showFallbackTutorials();
    }
    
    // If no tutorials were loaded (due to CORS or other issues), use fallback
    if (tutorials.length === 0) {
        showFallbackTutorials();
    }
}

// Parse tutorial markdown content
function parseTutorial(content, filename) {
    try {
        // Extract front matter (metadata between --- lines)
        const frontMatterMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
        
        if (!frontMatterMatch) {
            // If no front matter, create basic tutorial info
            return {
                id: filename.replace('.md', ''),
                title: filename.replace('.md', '').replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                date: new Date().toISOString().split('T')[0],
                author: 'Nasir Mahmood Abbasi, PhD',
                category: 'Bioinformatics',
                excerpt: content.substring(0, 200) + '...', // Take first 200 chars as excerpt
                content: content,
                filename: filename
            };
        }
        
        const frontMatter = frontMatterMatch[1];
        const mainContent = frontMatterMatch[2];
        
        // Parse front matter
        const metadata = {};
        frontMatter.split('\n').forEach(line => {
            const match = line.match(/^(\w+):\s*(.+)$/);
            if (match) {
                metadata[match[1]] = match[2].replace(/^["']|["']$/g, '');
            }
        });
        
        // Extract excerpt from content if not provided
        let excerpt = metadata.excerpt || '';
        if (!excerpt) {
            const contentWithoutHeaders = mainContent.replace(/^#+\s+.*/gm, ''); // Remove markdown headers
            excerpt = contentWithoutHeaders.substring(0, 200).trim() + '...';
        }
        
        return {
            id: filename.replace('.md', ''),
            title: metadata.title || 'Untitled Tutorial',
            date: metadata.date || new Date().toISOString().split('T')[0],
            author: metadata.author || 'Nasir Mahmood Abbasi, PhD',
            category: metadata.category || 'Bioinformatics',
            excerpt: excerpt,
            content: mainContent,
            filename: filename,
            image: metadata.image || 'images/default-tutorial.png' // Default image if not specified
        };
        
    } catch (error) {
        console.error('Error parsing tutorial:', filename, error);
        return null;
    }
}

// Show fallback tutorials when markdown files can't be loaded
function showFallbackTutorials() {
    // This function remains largely the same, providing hardcoded content
    // if fetching from 'lessons/' fails. This is a good fallback for GitHub Pages
    // if there are issues with fetching raw content.
    tutorials = [
        {
            id: 'introduction-to-bioinformatics',
            title: 'Introduction to Bioinformatics: Getting Started with Biological Data Analysis',
            date: '2025-08-15',
            author: 'OmicsHub Team',
            category: 'Bioinformatics',
            excerpt: 'Learn the fundamentals of bioinformatics and discover how computational methods are revolutionizing biological research. This tutorial covers basic concepts, tools, and workflows.',
            content: `# Introduction to Bioinformatics\n\n## What is Bioinformatics?\n\nBioinformatics is an interdisciplinary field that combines biology, computer science, mathematics, and statistics to analyze and interpret biological data. With the explosion of biological data from genomics, proteomics, and other high-throughput technologies, bioinformatics has become essential for modern biological research.\n\n## Why Learn Bioinformatics?\n\nIn today's data-driven world, biological research generates massive amounts of information. Consider these statistics:\n\n- The human genome contains approximately 3.2 billion base pairs\n- A single RNA-seq experiment can generate millions of sequencing reads\n- Protein databases contain information on hundreds of thousands of proteins\n\nWithout computational tools, analyzing this data would be impossible. Bioinformatics enables researchers to:\n\n- Process large datasets efficiently\n- Identify patterns in biological data\n- Make predictions about biological functions\n- Accelerate discovery in medicine and biology\n\n## Getting Started\n\nTo begin your bioinformatics journey, you'll need to master several key areas:\n\n1. **Command Line Skills** - Essential for running bioinformatics tools\n2. **Programming** - R and Python are the most popular languages\n3. **Statistics** - Understanding data analysis and interpretation\n4. **Biology** - Domain knowledge is crucial for meaningful analysis\n\n## Next Steps\n\nReady to dive deeper? Check out our other tutorials on command line basics, package management with Conda, and single-cell RNA-seq analysis.`,
            filename: 'introduction-to-bioinformatics.md',
            image: 'images/bioinformatics-intro.png'
        },
        {
            id: 'command-line-basics',
            title: 'Linux Command Line',
            description: 'Master the essential command-line tools and shell scripting for bioinformatics data processing.',
            filename: 'command-line-part1.md',
            author: 'OmicsHub Team',
            category: 'Shell Commands',
            excerpt: 'Master the command line from scratch, learn essential Unix commands, file manipulation, and text processing skills that every bioinformatician needs to succeed.',
            content: `# Command Line Mastery for Bioinformatics\n\n## Why the Command Line Matters\n\nThe command line is like learning to drive a manual transmission car. Sure, automatic is easier to start with, but once you master manual, you have complete control over the machine. In bioinformatics, that control translates to:\n\n- **Processing massive datasets** that would crash graphical programs\n- **Automating repetitive tasks** that would take hours manually\n- **Connecting tools together** in powerful workflows\n- **Working on remote servers** where GUIs aren't available\n\n## Essential Commands\n\n### Navigation\n\`\`\`bash\npwd          # Print working directory\nls           # List files\nls -la       # List all files with details\ncd           # Change directory\ncd ..        # Go up one level\ncd ~         # Go to home directory\n\`\`\`\n\n### File Operations\n\`\`\`bash\ncp file1 file2       # Copy file\nmv file1 file2       # Move/rename file\nrm file              # Remove file\nmkdir directory      # Create directory\nrmdir directory      # Remove empty directory\n\`\`\`\n\n### Text Processing\n\`\`\`bash\ncat file.txt         # Display file content\nhead file.txt        # Show first 10 lines\ntail file.txt        # Show last 10 lines\ngrep "pattern" file  # Search for pattern\nwc -l file.txt       # Count lines\n\`\`\`\n\n## Bioinformatics Examples\n\n### Count sequences in a FASTA file\n\`\`\`bash\ngrep -c ">" sequences.fasta\n\`\`\`\n\n### Extract sequence IDs\n\`\`\`bash\ngrep ">" sequences.fasta | sed 's/>//'\n\`\`\`\n\n### Calculate sequence lengths\n\`\`\`bash\nawk '/^>/ {if (seq) print length(seq); seq=""; next} {seq=seq$0} END {print length(seq)}' sequences.fasta\n\`\`\`\n\n## Conclusion\n\nThe command line is your gateway to powerful bioinformatics analysis. Practice these commands regularly, and you'll soon find yourself working more efficiently than ever before.`,
            image: 'images/command-line-terminal.png'
        },
        
         {
	id: 'connection',
	title: 'connection',
	date: '2025-08-23',
	author: 'OmicsHub Team',
	category: 'HPC',
	excerpt: 'Learn how to connect securely to remote HPC systems using SSH and MobaXterm, and set up your working environment efficiently.',
	filename: '1-Connection.md',
	image: 'images/connection.png'
},
{
	id: 'HPC Basic commands',
	title: 'HPC Basic commands',
	date: '2025-08-23',
	author: 'OmicsHub Team',
	category: 'HPC',
	excerpt: 'Master fundamental HPC commands for navigating the file system, managing files, and exploring data on remote clusters.',
	filename: '2-HPC_Basic_Commands.md',
	image: 'images/HPC.png'
},
{
	id: '3-writing_a_submission_script',
	title: 'HPC Job Submission',
	date: '2025-08-23',
	author: 'OmicsHub Team',
	category: 'HPC',
	description: 'Learn how to write and submit batch scripts using Slurm on high-performance computing clusters.',
	excerpt: 'Learn how to write and submit job scripts to HPC schedulers, automating tasks and efficiently managing computational workloads.',
	filename: 'hpc-submission-part1.md',
	image: 'images/sc.png'
},
{
	id: 'Support',
	title: 'Support to HPC',
	date: '2025-08-23',
	author: 'OmicsHub Team',
	category: 'HPC',
	excerpt: 'Discover how to troubleshoot issues and get help effectively when working on HPC systems, ensuring smooth workflow execution.',
	filename: '4-Support.md',
	image: 'images/support.png'
},

        {
            id: 'conda-mamba-guide',
            title: 'Conda & Mamba Environments',
            description: 'Learn how to manage software dependencies, create reproducible environments, and install bioinformatics tools safely.',
            filename: 'conda-mamba-part1.md',
            author: 'OmicsHub Team',
            category: 'Conda',
            excerpt: 'Master package management in bioinformatics with Conda and Mamba, learn installation, environment management, and how to install essential tools like Seurat for single-cell analysis.',
            content: `# Conda and Mamba for Bioinformatics\n\n## Why Package Management Matters\n\nIf you've ever spent hours trying to install a bioinformatics tool only to run into dependency conflicts, version mismatches, or the dreaded "it works on my machine" problem, you're not alone. Package management is one of the biggest pain points for researchers entering computational biology.\n\nThat's where Conda and Mamba come in. Think of them as your personal assistants for managing software installations, they handle all the messy details of dependencies, versions, and compatibility so you can focus on your research.\n\n## What Are Conda and Mamba?\n\n**Conda** is a package manager and environment management system that was originally created for Python but has evolved to support packages from any language. It's like having a smart librarian who not only knows where every book is but also ensures that when you check out a book, all the related materials you need are available and compatible.\n\n**Mamba** is a reimplementation of Conda that's significantly faster, we're talking about going from minutes to seconds for complex installations. It's essentially Conda with a turbo engine.\n\n## Installing Conda\n\n### Option 1: Miniconda (Recommended)\n\n\`\`\`bash\n# Download Miniconda for Linux\nwget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh\n\n# Make it executable\nchmod +x Miniconda3-latest-Linux-x86_64.sh\n\n# Run the installer\nbash Miniconda3-latest-Linux-x86_64.sh\n\`\`\`\n\n## Installing Mamba\n\n\`\`\`bash\nconda install -c conda-forge mamba\n\`\`\`\n\n## Creating Environments\n\n\`\`\`bash\n# Create environment for single-cell analysis\nmamba create -n single-cell python=3.9\n\n# Activate the environment\nconda activate single-cell\n\n# Install Seurat and dependencies\nmamba install -c conda-forge -c bioconda r-seurat r-ggplot2 r-dplyr\n\`\`\`\n\n## Best Practices\n\n1. **One Environment Per Project**\n2. **Document Your Environments**\n3. **Pin Important Versions**\n4. **Regular Maintenance**\n\nWith proper package management, you'll never have to worry about "dependency hell" again!`,
            image: 'images/conda-environment.png'
        },
        {
            id: 'single-cell-rnaseq',
            title: 'Single-cell RNA-seq',
            description: 'A complete end-to-end guide to analyzing single-cell RNA-seq data, from QC and clustering to trajectory inference.',
            filename: 'scrna-seq-basics.md',
            excerpt: 'Discover the revolutionary world of single-cell RNA sequencing, learn how this technology is transforming our understanding of cellular heterogeneity and development.',
            content: `# Single-cell RNA-seq Analysis\n\n## Introduction to Single-cell RNA-seq\n\nSingle-cell RNA sequencing (scRNA-seq) is a revolutionary technology that allows us to measure gene expression in individual cells rather than bulk tissue samples. This approach has transformed our understanding of cellular heterogeneity, development, and disease.\n\n## Why Single-cell?\n\nTraditional bulk RNA-seq provides an average expression profile across all cells in a sample, potentially masking important biological differences between cell types or states. Single-cell RNA-seq overcomes this limitation by:\n\n- Revealing cellular heterogeneity within tissues\n- Identifying rare cell types and subtypes\n- Tracking developmental trajectories\n- Understanding cell state transitions\n- Discovering new biological mechanisms\n\n## Key Concepts\n\n### Cell Types vs. Cell States\n- **Cell types**: Distinct cellular identities (e.g., neurons, T cells, fibroblasts)\n- **Cell states**: Temporary conditions within a cell type (e.g., activated, resting, stressed)\n\n## Analysis Workflow\n\n### 1. Quality Control\n\`\`\`r\n# Load libraries\nlibrary(Seurat)\nlibrary(ggplot2)\n\n# Load data\ndata <- Read10X(data.dir = "filtered_feature_bc_matrix/")\nseurat_obj <- CreateSeuratObject(counts = data, project = "scRNA_analysis")\n\n# Calculate QC metrics\nseurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = "^MT-")\n\n# Visualize QC metrics\nVlnPlot(seurat_obj, features = c("nFeature_RNA", "nCount_RNA", "percent.mt"), ncol = 3)\n\`\`\`\n\n### 2. Normalization and Scaling\n\`\`\`r\n# Normalize data\nseurat_obj <- NormalizeData(seurat_obj)\n\n# Find variable features\nseurat_obj <- FindVariableFeatures(seurat_obj, selection.method = "vst", nfeatures = 2000)\n\n# Scale data\nseurat_obj <- ScaleData(seurat_obj)\n\`\`\`\n\n### 3. Dimensionality Reduction\n\`\`\`r\n# Principal Component Analysis\nseurat_obj <- RunPCA(seurat_obj, features = VariableFeatures(object = seurat_obj))\n\n# UMAP\nseurat_obj <- RunUMAP(seurat_obj, dims = 1:10)\n\`\`\`\n\n### 4. Clustering\n\`\`\`r\n# Find neighbors\nseurat_obj <- FindNeighbors(seurat_obj, dims = 1:10)\n\n# Find clusters\nseurat_obj <- FindClusters(seurat_obj, resolution = 0.5)\n\n# Visualize clusters\nDimPlot(seurat_obj, reduction = "umap")\n\`\`\`\n\n## Common Challenges\n\n1. **Dropout Events**: Not all genes are detected in every cell\n2. **Batch Effects**: Technical variation between experiments\n3. **Cell Cycle Effects**: Cells in different phases of division\n4. **Doublets**: Two cells captured together\n\n## Best Practices\n\n- Always perform thorough quality control\n- Use appropriate normalization methods\n- Validate findings with independent datasets\n- Consider biological context in interpretation\n\n## Conclusion\n\nSingle-cell RNA-seq is a powerful technology that continues to evolve rapidly. By understanding the key concepts and following best practices, you can unlock valuable biological insights from your data.\n\n## Next Steps\n\n- Practice with public datasets\n- Learn advanced analysis techniques\n- Explore trajectory inference methods\n- Study cell-cell communication analysis`,
            image: 'images/single-cell-analysis.png'
        },
        
      ];
    
    updateTutorialsList();
    updateSidebar();
}

// Map category to color badge CSS class
function getBadgeClass(category) {
    const map = {
        'HPC': 'badge-hpc',
        'Shell Commands': 'badge-shell',
        'Conda': 'badge-conda',
        'Single-cell RNA-seq': 'badge-scrna',
        'Bioinformatics': 'badge-bio',
    };
    return map[category] || 'badge-bio';
}

// (Removed duplicate updateTutorialsList)

// Update sidebar with categories and recent posts
function updateSidebar() {
    const categoriesList = document.getElementById('categories-list');
    const recentPosts = document.getElementById('recent-posts');
    
    if (!categoriesList || !recentPosts) return;

    // Clear previous content
    categoriesList.innerHTML = '';
    recentPosts.innerHTML = '';

    // Populate Categories with counts
    const categories = [...new Set(tutorials.map(t => t.category))];
    categories.forEach(category => {
        const count = tutorials.filter(t => t.category === category).length;
        const categoryButton = document.createElement('button');
        categoryButton.className = 'category-btn w-full text-left px-3 py-2 rounded-md transition-colors hover:bg-blue-50 hover:text-blue-600 flex items-center justify-between';
        categoryButton.innerHTML = `
            <span class="font-medium">${category}</span>
            <span class="category-count text-xs bg-gray-200 text-gray-600 px-2 py-1 rounded-full">${count}</span>
        `;
        categoryButton.onclick = () => {
            filterTutorialsOnHomePage(category);
        };
        categoriesList.appendChild(categoryButton);
    });

    // Populate Recent Posts (top 5)
    const latestPosts = tutorials.slice(0, 5);
    latestPosts.forEach(tutorial => {
        const postLink = document.createElement('a');
        postLink.href = `${tutorial.id}.html`;
        postLink.className = 'sidebar-link';
        postLink.innerHTML = `
            <div class="font-medium text-sm text-gray-900 mb-1">${tutorial.title}</div>
            <div class="text-xs text-gray-500">${formatDate(tutorial.date)}</div>
        `;
        postLink.onclick = (e) => {
            e.preventDefault();
            showTutorial(tutorial.id);
        };
        recentPosts.appendChild(postLink);
    });
}

// Filter tutorials on home page by category using DOM elements
function filterTutorialsOnHomePage(category) {
    const homeTutorialsList = document.getElementById('tutorials-list');
    if (homeTutorialsList) {
        const cards = homeTutorialsList.querySelectorAll('.tutorial-card');
        cards.forEach(card => {
            // Check the category span inside the card
            const catSpan = card.querySelector('span.bg-blue-100');
            const cardCategory = catSpan ? catSpan.textContent.trim() : '';
            if (category === 'all' || cardCategory === category) {
                card.style.display = 'flex'; // It's technically display:block but we can just clear it
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
    
    // Update active category button
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('bg-blue-100', 'text-blue-800');
        btn.classList.add('hover:bg-blue-50', 'hover:text-blue-600');
    });
    
    // Find and highlight the active category
    const activeBtn = Array.from(document.querySelectorAll('.category-btn')).find(btn => 
        btn.textContent.trim().startsWith(category)
    );
    if (activeBtn) {
        activeBtn.classList.add('bg-blue-100', 'text-blue-800');
        activeBtn.classList.remove('hover:bg-blue-50', 'hover:text-blue-600');
    }
}

// Helper function to render a single tutorial card with cinematic image
function renderTutorialCard(tutorial) {
    return `
        <article class="tutorial-card" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;" onclick="window.location.href='${tutorial.id}.html'">
            ${tutorial.image ? `
            <div class="w-full aspect-video relative overflow-hidden border-b border-gray-100 bg-gray-50">
                <img src="${tutorial.image}" alt="${tutorial.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 hover:scale-105">
            </div>
            ` : ''}
            <div style="padding: 1.6rem; display: flex; flex-direction: column; flex-grow: 1;">
                <div class="flex flex-col items-start gap-2 mb-3">
                    <span class="badge ${getBadgeClass(tutorial.category)}">${tutorial.category}</span>
                    <span class="meta" style="margin:0">${formatDate(tutorial.date)}</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">${tutorial.title}</h3>
                <p class="excerpt text-gray-600 mb-4">${tutorial.excerpt}</p>
                <a href="${tutorial.id}.html" class="read-more mt-auto">
                    Read article <svg style="width:14px;height:14px;display:inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </a>
            </div>
        </article>
    `;
}

// Update tutorials list display
function updateTutorialsList(tutorialsToShow = null) {
    const tutorialsList = document.getElementById('tutorials-list');
    if (!tutorialsList) return;
    
    const displayTutorials = tutorialsToShow || tutorials;
    
    if (displayTutorials.length === 0) {
        tutorialsList.innerHTML = '<p class="text-gray-500 text-center py-8">No tutorials found.</p>';
        return;
    }
    
    tutorialsList.innerHTML = displayTutorials.map(tutorial => renderTutorialCard(tutorial)).join('');
}

// Filter tutorials by category
function filterTutorials(category) {
    if (currentPage !== 'tutorials') {
        showTutorials(); // First, show the tutorials page
    }
    filterTutorialsOnly(category); // Then filter without recursion
}

// Show individual tutorial
async function showTutorial(id, addToHistory = true) {
    if (window.STATIC_RENDERED && id === window.PRELOADED_TUTORIAL_ID) {
        // Already shown correctly by the initial load handler
        return;
    }
    const tutorial = tutorials.find(t => t.id === id);
    if (!tutorial) {
        console.error('Tutorial not found:', id);
        const tutorialContentDiv = document.getElementById('tutorial-content');
        if (tutorialContentDiv) {
            tutorialContentDiv.innerHTML = `
                <div class="bg-red-50 border-l-4 border-red-500 p-8 rounded-lg shadow-sm text-center">
                    <h2 class="text-2xl font-bold text-red-700 mb-4">Tutorial Not Found</h2>
                    <p class="text-gray-700 mb-6">This tutorial could not be loaded. It may have been moved or the connection timed out.</p>
                    <button onclick="showHome()" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                        Return to Tutorials
                    </button>
                </div>
            `;
            document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
            document.getElementById('tutorial-page').classList.remove('hidden');
        }
        return;
    }

    // Hide all pages, show tutorial page
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('tutorial-page').classList.remove('hidden');
    currentPage = 'tutorial';
    currentTutorial = tutorial;

    // Update URL if we are dynamically navigating from within the same page
    if (addToHistory && !window.PRELOADED_TUTORIAL_ID) {
        window.history.pushState(null, '', `${tutorialId}.html`);
    }

    const tutorialContentDiv = document.getElementById('tutorial-content');
    if (tutorialContentDiv) {
        // Display tutorial with professional styling
        let htmlContent = `
            <div class="bg-white rounded-lg shadow-lg p-8 mb-8">
                <!-- Tutorial Header -->
                <div class="border-b border-gray-200 pb-6 mb-8">
                    ${tutorial.image ? `
                    <div class="w-full aspect-video md:aspect-video relative overflow-hidden rounded-lg mb-8 shadow-sm bg-gray-50 border border-gray-100">
                        <img src="${tutorial.image}" alt="${tutorial.title}" class="absolute inset-0 w-full h-full object-cover">
                    </div>
                    ` : ''}
                    <div class="flex items-center justify-between mb-4">
                        <span class="badge ${getBadgeClass(tutorial.category)}">
                            ${tutorial.category}
                        </span>
                        <button onclick="showHome()" class="inline-flex items-center text-gray-600 hover:text-blue-600 transition-colors text-sm font-medium">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                            </svg>
                            Back to Tutorials
                        </button>
                    </div>
                    <h1 class="text-4xl font-bold text-gray-900 mb-4 leading-tight">${tutorial.title}</h1>
                    <div class="flex items-center space-x-6 text-gray-600">
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                            <span class="font-medium">${tutorial.author}</span>
                        </div>
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                            </svg>
                            <span>${formatDate(tutorial.date)}</span>
                        </div>
                        <div class="flex items-center">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span>${estimateReadingTime(tutorial.content)} min read</span>
                        </div>
                    </div>
                </div>

                <!-- Tutorial Content -->
                <div class="tutorial-content prose prose-lg max-w-none">
                    ${marked.parse(tutorial.content)}
                </div>

                ${(function() {
                    const currentIndex = tutorials.findIndex(t => t.id === tutorialId);
                    if (currentIndex !== -1 && currentIndex < tutorials.length - 1) {
                        const nextTutorial = tutorials[currentIndex + 1];
                        if (nextTutorial.category === tutorial.category) {
                            return `
                            <div class="mt-12 mb-4 p-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl border border-blue-100 flex items-center justify-between group cursor-pointer transition-all duration-300 hover:shadow-md hover:-translate-y-1" onclick="window.location.href='${nextTutorial.id}.html'">
                                <div>
                                    <span class="text-xs font-black tracking-widest text-blue-600 uppercase mb-2 block opacity-80">Next Step in ${tutorial.category}</span>
                                    <h4 class="text-2xl font-bold text-gray-900 group-hover:text-blue-800 transition-colors">${nextTutorial.title}</h4>
                                </div>
                                <div class="bg-white p-4 rounded-full shadow-sm text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
                                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                                    </svg>
                                </div>
                            </div>
                            `;
                        }
                    }
                    return '';
                })()}

                <!-- Services CTA -->
                <div class="my-10 bg-gray-50 border border-gray-200 rounded-2xl p-8 text-center shadow-sm">
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-900 mb-3">Need help with your own dataset?</h3>
                    <p class="text-gray-600 mb-6 max-w-2xl mx-auto">Get expert, 1-on-1 support for your bioinformatics analysis. Whether it's troubleshooting Conda environments, reviewing Scanpy/Seurat pipelines, or personalized mentoring, I can help you accelerate your research.</p>
                    <div class="flex gap-4 justify-center flex-wrap">
                        <a href="services.html" class="inline-block bg-blue-600 text-white font-bold px-8 py-3 rounded-xl hover:bg-blue-700 transition-colors shadow-md">View Consulting Services</a>
                        <a href="services.html" class="inline-block bg-white text-gray-700 border border-gray-200 font-bold px-8 py-3 rounded-xl hover:bg-gray-50 transition-colors shadow-sm">Get Free Cheat Sheet</a>
                    </div>
                </div>

                <!-- Tutorial Footer -->
                <div class="border-t border-gray-200 pt-6 mt-8">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <span class="text-sm text-gray-500">Share this tutorial:</span>

                            <button onclick="shareOnLinkedIn('${tutorial.title}', '${tutorial.id}')" class="text-blue-700 hover:text-blue-900 transition-colors" title="Share on LinkedIn">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                                </svg>
                            </button>
                            <button onclick="copyToClipboard(window.location.href)" class="text-gray-400 hover:text-gray-600 transition-colors" title="Copy Link">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                </svg>
                            </button>
                        </div>
                        <div class="flex gap-3">
                            <a href="https://paypal.me/nmabbasi12020?locale.x=en_US&country.x=FR" target="_blank" class="inline-flex items-center gap-2 px-6 py-2 bg-emerald-500 text-white font-bold rounded-lg hover:bg-emerald-600 transition-colors shadow-sm">
                                <span class="text-base">☕</span> Buy me a coffee
                            </a>
                            <button onclick="showHome()" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                                More Tutorials
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        tutorialContentDiv.innerHTML = htmlContent;
        
        // Dynamically convert adjacent Python and R code blocks into interactive tabs
        const contentDiv = document.querySelector('.tutorial-content');
        if (contentDiv) {
            const pythonBlocks = Array.from(contentDiv.querySelectorAll('pre code.language-python, pre code.language-py')).map(code => code.parentElement);
            
            pythonBlocks.forEach(pyPre => {
                let next = pyPre.nextElementSibling;
                if (next && next.tagName === 'PRE' && (next.querySelector('code.language-r') || next.querySelector('code.language-R'))) {
                    const rPre = next;
                    
                    const wrapper = document.createElement('div');
                    wrapper.className = 'code-tab-container mb-8 border border-gray-200 rounded-lg overflow-hidden shadow-sm';
                    
                    const header = document.createElement('div');
                    header.className = 'code-tab-header flex bg-gray-100 border-b border-gray-200';
                    
                    const pyBtn = document.createElement('button');
                    pyBtn.className = 'code-tab-btn active px-6 py-3 text-sm font-bold text-white bg-blue-600 rounded-md shadow-sm outline-none transition-all m-1';
                    pyBtn.dataset.lang = 'python';
                    pyBtn.innerText = 'Python (Scanpy)';
                    
                    const rBtn = document.createElement('button');
                    rBtn.className = 'code-tab-btn px-6 py-3 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-md outline-none transition-all m-1';
                    rBtn.dataset.lang = 'r';
                    rBtn.innerText = 'R (Seurat)';
                    
                    header.appendChild(pyBtn);
                    header.appendChild(rBtn);
                    
                    const pyContent = document.createElement('div');
                    pyContent.className = 'code-tab-content block';
                    pyContent.dataset.lang = 'python';
                    
                    const rContent = document.createElement('div');
                    rContent.className = 'code-tab-content hidden';
                    rContent.dataset.lang = 'r';
                    
                    // Remove margins and border-radius from the pre tags since they are in a container now
                    pyPre.style.margin = '0';
                    pyPre.style.borderRadius = '0';
                    rPre.style.margin = '0';
                    rPre.style.borderRadius = '0';
                    
                    pyPre.parentNode.insertBefore(wrapper, pyPre);
                    pyContent.appendChild(pyPre);
                    rContent.appendChild(rPre);
                    
                    wrapper.appendChild(header);
                    wrapper.appendChild(pyContent);
                    wrapper.appendChild(rContent);
                }
            });

            // Event delegation for tab buttons
            contentDiv.addEventListener('click', (e) => {
                if (e.target.classList.contains('code-tab-btn')) {
                    const container = e.target.closest('.code-tab-container');
                    const lang = e.target.dataset.lang;
                    
                    container.querySelectorAll('.code-tab-btn').forEach(btn => {
                        btn.classList.toggle('active', btn === e.target);
                        btn.classList.toggle('bg-white', btn === e.target);
                        btn.classList.toggle('text-blue-700', btn === e.target);
                        btn.classList.toggle('border-blue-600', btn === e.target);
                        btn.classList.toggle('text-gray-600', btn !== e.target);
                    });
                    
                    container.querySelectorAll('.code-tab-content').forEach(content => {
                        content.classList.toggle('hidden', content.dataset.lang !== lang);
                        content.classList.toggle('block', content.dataset.lang === lang);
                    });
                }
            });
        }

        // Initialize syntax highlighting code blocks after content is loaded
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
    }

    window.scrollTo(0, 0); // Scroll to top of page
}

// Show Home Page
function showHome(addToHistory = true, preventScroll = false) {
    updateNavActiveState('home');
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('home-page').classList.remove('hidden');
    currentPage = 'home';
    currentTutorial = null;
    if (addToHistory) {
        window.history.pushState(null, '', window.location.pathname); // Clear hash
    }
    if (!preventScroll) {
        window.scrollTo(0, 0); // Scroll to top of page
    }
}

// Show Tutorials Page
function showTutorials(addToHistory = true) {
    updateNavActiveState('tutorials');
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('tutorials-page').classList.remove('hidden');
    currentPage = 'tutorials';
    currentTutorial = null;
    if (addToHistory) {
        window.history.pushState(null, '', '#all-tutorials');
    }
    
    // We no longer populate category filter buttons or render grid cards dynamically.
    // They are fully baked into the static HTML by inject_html_cards.py.
    
    window.scrollTo(0, 0); // Scroll to top of page
}

// Filter tutorials by category using static HTML data-category attributes
function filterTutorialsOnly(category) {
    const allTutorialsList = document.getElementById('all-tutorials-list');
    if (!allTutorialsList) return;

    const cards = allTutorialsList.querySelectorAll('.tutorial-grid-card');
    cards.forEach(card => {
        if (category === 'all' || card.getAttribute('data-category') === category) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });

    // Update active category button
    document.querySelectorAll('#category-filter .category-btn').forEach(btn => {
        if (btn.dataset.category === category) {
            btn.classList.add('bg-blue-600', 'text-white');
            btn.classList.remove('bg-gray-200', 'text-gray-700');
        } else {
            btn.classList.remove('bg-blue-600', 'text-white');
            btn.classList.add('bg-gray-200', 'text-gray-700');
        }
    });
}

// Show Static Pages (About, Contact, Legal)
// This function is now removed as we are using dedicated HTML files for these pages.
// The navigation links will directly point to these HTML files.

// Utility functions
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function estimateReadingTime(content) {
    const wordsPerMinute = 200;
    const words = content.split(/\s+/).length;
    return Math.ceil(words / wordsPerMinute);
}

function shareOnLinkedIn(title, tutorialId) {
    const url = `${window.location.origin}${window.location.pathname.replace('index.html', '')}${tutorialId}.html`;
    const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`;
    window.open(linkedInUrl, '_blank');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show a temporary notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        notification.textContent = 'Link copied to clipboard!';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 3000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

function handleSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    const query = searchInput.value.toLowerCase();
    
    const homeTutorialsList = document.getElementById('tutorials-list');
    if (homeTutorialsList) {
        const cards = homeTutorialsList.querySelectorAll('.tutorial-card');
        cards.forEach(card => {
            const title = card.querySelector('h3') ? card.querySelector('h3').textContent.toLowerCase() : '';
            const cat = card.querySelector('span.bg-blue-100') ? card.querySelector('span.bg-blue-100').textContent.toLowerCase() : '';
            const exc = card.querySelector('.excerpt') ? card.querySelector('.excerpt').textContent.toLowerCase() : '';
            
            if (query === '' || title.includes(query) || cat.includes(query) || exc.includes(query)) {
                card.classList.remove('hidden');
                card.style.display = '';
            } else {
                card.classList.add('hidden');
                card.style.display = 'none';
            }
        });
    }
    
    const allTutorialsList = document.getElementById('all-tutorials-list');
    if (allTutorialsList) {
        const gridCards = allTutorialsList.querySelectorAll('.tutorial-grid-card');
        gridCards.forEach(card => {
            const title = card.querySelector('h3') ? card.querySelector('h3').textContent.toLowerCase() : '';
            const cat = card.getAttribute('data-category') ? card.getAttribute('data-category').toLowerCase() : '';
            const exc = card.querySelector('.line-clamp-3') ? card.querySelector('.line-clamp-3').textContent.toLowerCase() : '';
            
            if (query === '' || title.includes(query) || cat.includes(query) || exc.includes(query)) {
                card.style.display = 'flex';
                card.classList.remove('hidden');
            } else {
                card.style.display = 'none';
                card.classList.add('hidden');
            }
        });
    }
}

// Back to top button functionality
function createBackToTopButton() {
    const backToTopBtn = document.createElement('button');
    backToTopBtn.id = 'back-to-top';
    backToTopBtn.className = 'fixed bottom-8 right-8 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:bg-blue-700 transition-all duration-300 hidden z-50';
    backToTopBtn.innerHTML = `
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
        </svg>
    `;
    document.body.appendChild(backToTopBtn);

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

function handleScroll() {
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        if (window.scrollY > 300) {
            backToTopBtn.classList.remove('hidden');
        } else {
            backToTopBtn.classList.add('hidden');
        }
    }
}

// Mobile menu toggle
function toggleMobileMenu() {
    const mobileMenu = document.getElementById("mobile-menu");
    const toggle = document.querySelector('button[aria-controls="mobile-menu"]');
    const isOpen = mobileMenu.classList.toggle("hidden") === false;
    if (toggle) {
        toggle.setAttribute("aria-expanded", String(isOpen));
        toggle.setAttribute("aria-label", isOpen ? "Close navigation menu" : "Open navigation menu");
    }
}

function closeMobileMenu() {
    const mobileMenu = document.getElementById("mobile-menu");
    const toggle = document.querySelector('button[aria-controls="mobile-menu"]');
    if (mobileMenu) mobileMenu.classList.add("hidden");
    if (toggle) {
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open navigation menu");
    }
}

document.addEventListener('click', function(event) {
    const link = event.target.closest('#mobile-menu a');
    if (link) closeMobileMenu();
});




// Function to handle showing different sections/pages
// This function is now simplified as static pages are handled by direct links
// and tutorial loading is handled by showTutorial and showTutorials

// Note: The showPage function is removed as static pages are now direct HTML files.
// The navigation links in index.html and other pages are updated to reflect this.

// Event delegation for switching code tabs within tutorials
document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('code-tab-btn')) {
        const btn = e.target;
        const lang = btn.dataset.lang;
        const container = btn.closest('.code-tab-container');
        
        if (!container) return;
        
        container.querySelectorAll('.code-tab-btn').forEach(b => {
            if (b.dataset.lang === lang) {
                b.className = 'code-tab-btn active px-6 py-3 text-sm font-bold text-white bg-blue-600 rounded-md shadow-sm outline-none transition-all m-1';
            } else {
                b.className = 'code-tab-btn px-6 py-3 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-200 rounded-md outline-none transition-all m-1';
            }
        });
        
        container.querySelectorAll('.code-tab-content').forEach(c => {
            if (c.dataset.lang === lang) {
                c.classList.remove('hidden');
                c.classList.add('block');
            } else {
                c.classList.remove('block');
                c.classList.add('hidden');
            }
        });
    }
});

// Update Navigation Active States
function updateNavActiveState(activeTab) {
    const navDesktopHome = document.getElementById('nav-desktop-home');
    const navDesktopTutorials = document.getElementById('nav-desktop-tutorials');
    const navMobileHome = document.getElementById('nav-mobile-home');
    const navMobileTutorials = document.getElementById('nav-mobile-tutorials');

    if (activeTab === 'home') {
        if (navDesktopHome) navDesktopHome.className = 'px-4 py-2 text-sm font-semibold bg-blue-600 text-white rounded-md shadow-sm transition-all';
        if (navDesktopTutorials) navDesktopTutorials.className = 'px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all cursor-pointer';
        
        if (navMobileHome) navMobileHome.className = 'px-4 py-2 text-sm font-semibold text-blue-600 bg-blue-50 rounded-lg transition-colors';
        if (navMobileTutorials) navMobileTutorials.className = 'px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer';
    } else if (activeTab === 'tutorials') {
        if (navDesktopHome) navDesktopHome.className = 'px-4 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 rounded-md hover:bg-gray-50 transition-all cursor-pointer';
        if (navDesktopTutorials) navDesktopTutorials.className = 'px-4 py-2 text-sm font-semibold bg-blue-600 text-white rounded-md shadow-sm transition-all';
        
        if (navMobileHome) navMobileHome.className = 'px-4 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer';
        if (navMobileTutorials) navMobileTutorials.className = 'px-4 py-2 text-sm font-semibold text-blue-600 bg-blue-50 rounded-lg transition-colors';
    }
}
