// OmicsHub Website JavaScript

// Global variables
let tutorials = [];
let currentPage = 'home';
let currentTutorial = null;

// Initialize the website
document.addEventListener('DOMContentLoaded', function() {
    loadTutorials();
    setupEventListeners();
    createBackToTopButton();
});

// Handle initial routing after tutorials load
function handleInitialRoute() {
    const hash = window.location.hash;
    if (hash) {
        if (hash.startsWith('#tutorial-')) {
            const tutorialId = hash.substring(10); // Remove '#tutorial-'
            showTutorial(tutorialId);
        } else if (hash === '#tutorials') {
            showTutorials();
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
    
    // Back to top button
    window.addEventListener('scroll', handleScroll);

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function(event) {
        const hash = window.location.hash;
        if (hash) {
            if (hash.startsWith('#tutorial-')) {
                const tutorialId = hash.substring(10);
                showTutorial(tutorialId, false); // false to prevent adding to history again
            } else if (hash === '#tutorials') {
                showTutorials(false);
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
            'introduction-to-bioinformatics.md',
            'modern-bioinformatics-methods-2024.md',
            'conda-bioinformatics-guide.md',
            'mamba-micromamba-guide.md',
            'conda-mamba-part1.md',
            'single-cell-rnaseq-part2.md',
            'command-line-part2.md',
            '1-Connection.md',
            'single-cell-rnaseq-part3.md',
            '2-HPC_Basic_Commands.md',
            'command-line-part3.md',
            'command-line-part1.md',
            '4-Support.md',
            'hpc-submission-part1.md',
            'single-cell-rnaseq-part1.md',
            'scrna-seq-basics.md',
            'scrna-seq-trajectory-inference.md',
            'scrna-seq-downstream-analysis.md',
        ];
        
        tutorials = [];
        
        for (const file of tutorialFiles) {
            try {
                // GitHub Pages compatible path handling
                let fetchPath;
                if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    // Local development
                    fetchPath = `lessons/${file}`;
                } else {
                    // GitHub Pages - use relative path from current location
                    fetchPath = `lessons/${file}`;
                }
                
                const response = await fetch(fetchPath);
                if (response.ok) {
                    const content = await response.text();
                    const tutorial = parseTutorial(content, file);
                    if (tutorial) {
                        tutorials.push(tutorial);
                    }
                } else {
                    console.warn(`Could not load tutorial: ${file}. Status: ${response.status}`);
                }
            } catch (error) {
                console.warn(`Error fetching tutorial: ${file}`, error);
            }
        }
        
        // Sort tutorials by date (newest first)
        tutorials.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // Update the UI
        updateTutorialsList();
        updateSidebar();
        
        // Handle routing now that tutorials are loaded
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
                author: 'OmicsHub Team',
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
            author: metadata.author || 'OmicsHub Team',
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
            id: 'command-line-basics-detailed',
            title: 'Command Line Mastery: A Detailed Guide for Bioinformatics Beginners',
            date: '2025-08-14',
            author: 'OmicsHub Team',
            category: 'Shell Commands',
            excerpt: 'Master the command line from scratch, learn essential Unix commands, file manipulation, and text processing skills that every bioinformatician needs to succeed.',
            content: `# Command Line Mastery for Bioinformatics\n\n## Why the Command Line Matters\n\nThe command line is like learning to drive a manual transmission car. Sure, automatic is easier to start with, but once you master manual, you have complete control over the machine. In bioinformatics, that control translates to:\n\n- **Processing massive datasets** that would crash graphical programs\n- **Automating repetitive tasks** that would take hours manually\n- **Connecting tools together** in powerful workflows\n- **Working on remote servers** where GUIs aren't available\n\n## Essential Commands\n\n### Navigation\n\`\`\`bash\npwd          # Print working directory\nls           # List files\nls -la       # List all files with details\ncd           # Change directory\ncd ..        # Go up one level\ncd ~         # Go to home directory\n\`\`\`\n\n### File Operations\n\`\`\`bash\ncp file1 file2       # Copy file\nmv file1 file2       # Move/rename file\nrm file              # Remove file\nmkdir directory      # Create directory\nrmdir directory      # Remove empty directory\n\`\`\`\n\n### Text Processing\n\`\`\`bash\ncat file.txt         # Display file content\nhead file.txt        # Show first 10 lines\ntail file.txt        # Show last 10 lines\ngrep "pattern" file  # Search for pattern\nwc -l file.txt       # Count lines\n\`\`\`\n\n## Bioinformatics Examples\n\n### Count sequences in a FASTA file\n\`\`\`bash\ngrep -c ">" sequences.fasta\n\`\`\`\n\n### Extract sequence IDs\n\`\`\`bash\ngrep ">" sequences.fasta | sed 's/>//'\n\`\`\`\n\n### Calculate sequence lengths\n\`\`\`bash\nawk '/^>/ {if (seq) print length(seq); seq=""; next} {seq=seq$0} END {print length(seq)}' sequences.fasta\n\`\`\`\n\n## Conclusion\n\nThe command line is your gateway to powerful bioinformatics analysis. Practice these commands regularly, and you'll soon find yourself working more efficiently than ever before.`,
            filename: 'command-line-basics-detailed.md',
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
	id: 'Submission Scripts',
	title: 'Submission Scripts',
	date: '2025-08-23',
	author: 'OmicsHub Team',
	category: 'HPC',
	excerpt: 'Learn how to write and submit job scripts to HPC schedulers, automating tasks and efficiently managing computational workloads.',
	filename: '3-Writing_a_Submission_Script.md',
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
            id: 'conda-mamba-installation-guide',
            title: 'Conda and Mamba: The Complete Installation and Usage Guide for Bioinformatics',
            date: '2025-08-13',
            author: 'OmicsHub Team',
            category: 'Conda',
            excerpt: 'Master package management in bioinformatics with Conda and Mamba, learn installation, environment management, and how to install essential tools like Seurat for single-cell analysis.',
            content: `# Conda and Mamba for Bioinformatics\n\n## Why Package Management Matters\n\nIf you've ever spent hours trying to install a bioinformatics tool only to run into dependency conflicts, version mismatches, or the dreaded "it works on my machine" problem, you're not alone. Package management is one of the biggest pain points for researchers entering computational biology.\n\nThat's where Conda and Mamba come in. Think of them as your personal assistants for managing software installations, they handle all the messy details of dependencies, versions, and compatibility so you can focus on your research.\n\n## What Are Conda and Mamba?\n\n**Conda** is a package manager and environment management system that was originally created for Python but has evolved to support packages from any language. It's like having a smart librarian who not only knows where every book is but also ensures that when you check out a book, all the related materials you need are available and compatible.\n\n**Mamba** is a reimplementation of Conda that's significantly faster, we're talking about going from minutes to seconds for complex installations. It's essentially Conda with a turbo engine.\n\n## Installing Conda\n\n### Option 1: Miniconda (Recommended)\n\n\`\`\`bash\n# Download Miniconda for Linux\nwget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh\n\n# Make it executable\nchmod +x Miniconda3-latest-Linux-x86_64.sh\n\n# Run the installer\nbash Miniconda3-latest-Linux-x86_64.sh\n\`\`\`\n\n## Installing Mamba\n\n\`\`\`bash\nconda install -c conda-forge mamba\n\`\`\`\n\n## Creating Environments\n\n\`\`\`bash\n# Create environment for single-cell analysis\nmamba create -n single-cell python=3.9\n\n# Activate the environment\nconda activate single-cell\n\n# Install Seurat and dependencies\nmamba install -c conda-forge -c bioconda r-seurat r-ggplot2 r-dplyr\n\`\`\`\n\n## Best Practices\n\n1. **One Environment Per Project**\n2. **Document Your Environments**\n3. **Pin Important Versions**\n4. **Regular Maintenance**\n\nWith proper package management, you'll never have to worry about "dependency hell" again!`,
            filename: 'conda-mamba-installation-guide.md',
            image: 'images/conda-environment.png'
        },
        {
            id: 'single-cell-rnaseq-introduction',
            title: 'Single-cell RNA-seq Analysis: From Raw Data to Biological Insights',
            date: '2025-08-12',
            author: 'OmicsHub Team',
            category: 'Single-cell RNA-seq',
            excerpt: 'Discover the revolutionary world of single-cell RNA sequencing, learn how this technology is transforming our understanding of cellular heterogeneity and development.',
            content: `# Single-cell RNA-seq Analysis\n\n## Introduction to Single-cell RNA-seq\n\nSingle-cell RNA sequencing (scRNA-seq) is a revolutionary technology that allows us to measure gene expression in individual cells rather than bulk tissue samples. This approach has transformed our understanding of cellular heterogeneity, development, and disease.\n\n## Why Single-cell?\n\nTraditional bulk RNA-seq provides an average expression profile across all cells in a sample, potentially masking important biological differences between cell types or states. Single-cell RNA-seq overcomes this limitation by:\n\n- Revealing cellular heterogeneity within tissues\n- Identifying rare cell types and subtypes\n- Tracking developmental trajectories\n- Understanding cell state transitions\n- Discovering new biological mechanisms\n\n## Key Concepts\n\n### Cell Types vs. Cell States\n- **Cell types**: Distinct cellular identities (e.g., neurons, T cells, fibroblasts)\n- **Cell states**: Temporary conditions within a cell type (e.g., activated, resting, stressed)\n\n## Analysis Workflow\n\n### 1. Quality Control\n\`\`\`r\n# Load libraries\nlibrary(Seurat)\nlibrary(ggplot2)\n\n# Load data\ndata <- Read10X(data.dir = "filtered_feature_bc_matrix/")\nseurat_obj <- CreateSeuratObject(counts = data, project = "scRNA_analysis")\n\n# Calculate QC metrics\nseurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = "^MT-")\n\n# Visualize QC metrics\nVlnPlot(seurat_obj, features = c("nFeature_RNA", "nCount_RNA", "percent.mt"), ncol = 3)\n\`\`\`\n\n### 2. Normalization and Scaling\n\`\`\`r\n# Normalize data\nseurat_obj <- NormalizeData(seurat_obj)\n\n# Find variable features\nseurat_obj <- FindVariableFeatures(seurat_obj, selection.method = "vst", nfeatures = 2000)\n\n# Scale data\nseurat_obj <- ScaleData(seurat_obj)\n\`\`\`\n\n### 3. Dimensionality Reduction\n\`\`\`r\n# Principal Component Analysis\nseurat_obj <- RunPCA(seurat_obj, features = VariableFeatures(object = seurat_obj))\n\n# UMAP\nseurat_obj <- RunUMAP(seurat_obj, dims = 1:10)\n\`\`\`\n\n### 4. Clustering\n\`\`\`r\n# Find neighbors\nseurat_obj <- FindNeighbors(seurat_obj, dims = 1:10)\n\n# Find clusters\nseurat_obj <- FindClusters(seurat_obj, resolution = 0.5)\n\n# Visualize clusters\nDimPlot(seurat_obj, reduction = "umap")\n\`\`\`\n\n## Common Challenges\n\n1. **Dropout Events**: Not all genes are detected in every cell\n2. **Batch Effects**: Technical variation between experiments\n3. **Cell Cycle Effects**: Cells in different phases of division\n4. **Doublets**: Two cells captured together\n\n## Best Practices\n\n- Always perform thorough quality control\n- Use appropriate normalization methods\n- Validate findings with independent datasets\n- Consider biological context in interpretation\n\n## Conclusion\n\nSingle-cell RNA-seq is a powerful technology that continues to evolve rapidly. By understanding the key concepts and following best practices, you can unlock valuable biological insights from your data.\n\n## Next Steps\n\n- Practice with public datasets\n- Learn advanced analysis techniques\n- Explore trajectory inference methods\n- Study cell-cell communication analysis`,
            filename: 'single-cell-rnaseq-introduction.md',
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
        postLink.href = `#tutorial-${tutorial.id}`;
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

// Filter tutorials on home page by category
function filterTutorialsOnHomePage(category) {
    const filteredTutorials = category === 'all' ? tutorials : tutorials.filter(t => t.category === category);
    updateTutorialsList(filteredTutorials);
    
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
        <article class="tutorial-card" style="padding: 0; overflow: hidden; display: flex; flex-direction: column;" onclick="showTutorial('${tutorial.id}')">
            ${tutorial.image ? `
            <div class="w-full aspect-video relative overflow-hidden border-b border-gray-100 bg-gray-50">
                <img src="${tutorial.image}" alt="${tutorial.title}" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 hover:scale-105">
            </div>
            ` : ''}
            <div style="padding: 1.6rem; display: flex; flex-direction: column; flex-grow: 1;">
                <div class="flex items-center justify-between mb-3">
                    <span class="badge ${getBadgeClass(tutorial.category)}">${tutorial.category}</span>
                    <span class="meta" style="margin:0">${formatDate(tutorial.date)}</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">${tutorial.title}</h3>
                <p class="excerpt text-gray-600 mb-4">${tutorial.excerpt}</p>
                <a href="#tutorial-${tutorial.id}" class="read-more mt-auto" onclick="event.stopPropagation(); showTutorial('${tutorial.id}')">
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
async function showTutorial(tutorialId, addToHistory = true) {
    const tutorial = tutorials.find(t => t.id === tutorialId);
    if (!tutorial) {
        console.error('Tutorial not found:', tutorialId);
        return;
    }

    // Hide all pages, show tutorial page
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('tutorial-page').classList.remove('hidden');
    currentPage = 'tutorial';
    currentTutorial = tutorial;

    // Update URL hash
    if (addToHistory) {
        window.history.pushState(null, '', `#tutorial-${tutorialId}`);
    }

    const tutorialContentDiv = document.getElementById('tutorial-content');
    if (tutorialContentDiv) {
        // Display tutorial with professional styling
        let htmlContent = `
            <div class="bg-white rounded-lg shadow-lg p-8 mb-8">
                <!-- Tutorial Header -->
                <div class="border-b border-gray-200 pb-6 mb-8">
                    ${tutorial.image ? `
                    <div class="w-full aspect-video md:aspect-[21/9] relative overflow-hidden rounded-lg mb-8 shadow-sm bg-gray-50 border border-gray-100">
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

                <!-- Tutorial Footer -->
                <div class="border-t border-gray-200 pt-6 mt-8">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <span class="text-sm text-gray-500">Share this tutorial:</span>
                            <button onclick="shareOnTwitter('${tutorial.title}', '${tutorial.id}')" class="text-blue-400 hover:text-blue-600 transition-colors">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                                </svg>
                            </button>
                            <button onclick="copyToClipboard(window.location.href)" class="text-gray-400 hover:text-gray-600 transition-colors">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                </svg>
                            </button>
                        </div>
                        <button onclick="showHome()" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                            More Tutorials
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('content-area').innerHTML = htmlContent;
        
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
                    pyBtn.className = 'code-tab-btn active px-6 py-3 text-sm font-bold text-blue-700 bg-white border-b-2 border-blue-600 outline-none transition-colors';
                    pyBtn.dataset.lang = 'python';
                    pyBtn.innerText = 'Python (Scanpy)';
                    
                    const rBtn = document.createElement('button');
                    rBtn.className = 'code-tab-btn px-6 py-3 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-200 outline-none border-b-2 border-transparent transition-colors';
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
function showHome(addToHistory = true) {
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('home-page').classList.remove('hidden');
    currentPage = 'home';
    currentTutorial = null;
    if (addToHistory) {
        window.history.pushState(null, '', window.location.pathname); // Clear hash
    }
    window.scrollTo(0, 0); // Scroll to top of page
}

// Show Tutorials Page
function showTutorials(addToHistory = true) {
    document.querySelectorAll('.page-content').forEach(page => page.classList.add('hidden'));
    document.getElementById('tutorials-page').classList.remove('hidden');
    currentPage = 'tutorials';
    currentTutorial = null;
    if (addToHistory) {
        window.history.pushState(null, '', '#tutorials');
    }
    
    // Populate tutorials directly without calling filterTutorials to avoid recursion
    const allTutorialsList = document.getElementById('all-tutorials-list');
    const categoryFilter = document.getElementById('category-filter');
    
    if (!allTutorialsList || !categoryFilter) return;

    // Populate category filter buttons if not already done
    if (categoryFilter.children.length === 1) { // Only has "All Tutorials" button
        const categories = [...new Set(tutorials.map(t => t.category))];
        categories.forEach(cat => {
            const button = document.createElement('button');
            button.className = 'category-btn px-4 py-2 rounded-full text-sm font-medium transition-colors bg-gray-200 text-gray-700 hover:bg-gray-300';
            button.dataset.category = cat;
            button.textContent = cat;
            button.onclick = () => filterTutorialsOnly(cat);
            categoryFilter.appendChild(button);
        });
    }

    // Display all tutorials
    allTutorialsList.innerHTML = tutorials.map(tutorial => renderTutorialCard(tutorial)).join('');
    
    window.scrollTo(0, 0); // Scroll to top of page
}

// Filter tutorials by category (without calling showTutorials)
function filterTutorialsOnly(category) {
    const allTutorialsList = document.getElementById('all-tutorials-list');
    if (!allTutorialsList) return;

    const filteredTutorials = category === 'all' ? tutorials : tutorials.filter(t => t.category === category);

    allTutorialsList.innerHTML = filteredTutorials.map(tutorial => renderTutorialCard(tutorial)).join('');

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

function shareOnTwitter(title, tutorialId) {
    const url = `${window.location.origin}${window.location.pathname}#tutorial-${tutorialId}`;
    const text = `Check out this tutorial: ${title}`;
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
    window.open(twitterUrl, '_blank');
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
    const query = document.getElementById('search-input').value.toLowerCase();
    const filteredTutorials = tutorials.filter(tutorial => 
        tutorial.title.toLowerCase().includes(query) ||
        tutorial.excerpt.toLowerCase().includes(query) ||
        tutorial.content.toLowerCase().includes(query)
    );
    
    const tutorialsList = document.getElementById('tutorials-list');
    const allTutorialsList = document.getElementById('all-tutorials-list');

    if (currentPage === 'home' && tutorialsList) {
        tutorialsList.innerHTML = filteredTutorials.map(tutorial => `
            <article class="tutorial-card cursor-pointer" onclick="showTutorial(\'${tutorial.id}\')">
                <div class="flex items-start justify-between mb-3">
                    <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">${tutorial.category}</span>
                    <span class="text-sm text-gray-500">${formatDate(tutorial.date)}</span>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">${tutorial.title}</h3>
                <p class="text-gray-700 text-base mb-4">${tutorial.excerpt}</p>
                <a href="#tutorial-${tutorial.id}" class="text-blue-600 hover:underline font-semibold" onclick="showTutorial(\'${tutorial.id}\')">Read More →</a>
            </article>
        `).join('');
    } else if (currentPage === 'tutorials' && allTutorialsList) {
        allTutorialsList.innerHTML = filteredTutorials.map(tutorial => `
            <article class="bg-white rounded-lg shadow-md overflow-hidden transform transition-transform hover:scale-105 duration-300">
                <img src="${window.location.origin}/OmicsHub/${tutorial.image}" alt="${tutorial.title}" class="w-full h-48 object-cover">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-3">
                        <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">${tutorial.category}</span>
                        <span class="text-sm text-gray-500">${formatDate(tutorial.date)}</span>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-2">${tutorial.title}</h3>
                    <p class="text-gray-700 text-base mb-4">${tutorial.excerpt}</p>
                    <a href="#tutorial-${tutorial.id}" class="text-blue-600 hover:underline font-semibold" onclick="showTutorial(\'${tutorial.id}\')">Read More →</a>
                </div>
            </article>
        `).join('');
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
    mobileMenu.classList.toggle("hidden");
}




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
                b.className = 'code-tab-btn active px-6 py-3 text-sm font-bold text-blue-700 bg-white border-b-2 border-blue-600 outline-none transition-colors';
            } else {
                b.className = 'code-tab-btn px-6 py-3 text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-200 outline-none border-b-2 border-transparent transition-colors';
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
