import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as pe
import numpy as np
import os

os.makedirs('images', exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.5

# ==========================================
# 1. BIOINFORMATICS INTRO (Multi-panel Workflow)
# ==========================================
def make_bioinformatics_intro():
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    
    ax1 = fig.add_axes([0.05, 0.15, 0.26, 0.7])  # Panel 1: DNA / Genomics
    ax2 = fig.add_axes([0.37, 0.15, 0.26, 0.7])  # Panel 2: Read Alignment / IGV
    ax3 = fig.add_axes([0.69, 0.15, 0.26, 0.7])  # Panel 3: Systems & Single Cell
    
    for ax in [ax1, ax2, ax3]:
        ax.set_facecolor('#f8fafc')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color('#cbd5e1')
            spine.set_linewidth(2)

    # Panel 1: DNA Double Helix
    t = np.linspace(0, 4*np.pi, 200)
    y1 = np.sin(t)
    y2 = np.sin(t + np.pi)
    ax1.plot(y1, t, color='#0284c7', linewidth=4)
    ax1.plot(y2, t, color='#059669', linewidth=4)
    for i in range(0, len(t), 12):
        ax1.plot([y1[i], y2[i]], [t[i], t[i]], color='#94a3b8', linewidth=2, alpha=0.7)
    ax1.set_title("1. Genomic Sequencing", fontsize=18, fontweight='bold', pad=15, color='#0f172a')

    # Panel 2: Read Alignment (IGV Track Style)
    np.random.seed(42)
    ax2.axhline(10, color='#2563eb', linewidth=3)
    for i in range(15):
        y_pos = np.random.uniform(1, 9)
        x_start = np.random.uniform(0.1, 0.6)
        x_len = np.random.uniform(0.2, 0.3)
        ax2.add_patch(patches.Rectangle((x_start, y_pos), x_len, 0.4, facecolor='#38bdf8', alpha=0.8, edgecolor='#0284c7'))
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 11)
    ax2.set_title("2. Alignment & Variant Calling", fontsize=18, fontweight='bold', pad=15, color='#0f172a')

    # Panel 3: Single-cell & Pathway Network
    x_net = np.random.rand(25)
    y_net = np.random.rand(25)
    for i in range(25):
        for j in range(i+1, 25):
            if np.hypot(x_net[i]-x_net[j], y_net[i]-y_net[j]) < 0.3:
                ax3.plot([x_net[i], x_net[j]], [y_net[i], y_net[j]], color='#cbd5e1', linewidth=1.5, zorder=1)
    ax3.scatter(x_net, y_net, s=150, c=np.random.rand(25), cmap='viridis', zorder=2, edgecolor='white')
    ax3.set_title("3. Omics Analysis", fontsize=18, fontweight='bold', pad=15, color='#0f172a')

    fig.text(0.5, 0.93, "Modern Bioinformatics Workflow Architecture", fontsize=26, fontweight='bold', ha='center', color='#0f172a')
    
    plt.savefig('images/bioinformatics-intro.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Created images/bioinformatics-intro.png")

# ==========================================
# 2. CONDA ENVIRONMENT GUIDE
# ==========================================
def make_conda_environment():
    fig, ax = plt.subplots(figsize=(16, 9), facecolor='white')
    ax.set_facecolor('#f8fafc')
    ax.axis('off')
    
    # Header Banner
    ax.add_patch(patches.Rectangle((0, 8), 16, 1, facecolor='#16a34a'))
    ax.text(8, 8.5, "CONDA & BIOCONDA PACKAGE MANAGEMENT", fontsize=24, fontweight='bold', color='white', ha='center', va='center')
    
    # Left Box
    ax.add_patch(patches.FancyBboxPatch((1, 1.5), 6.5, 6, boxstyle="round,pad=0.2", facecolor='white', edgecolor='#cbd5e1', linewidth=2))
    ax.text(4.25, 7, "Conda Channels & Dependencies", fontsize=18, fontweight='bold', ha='center', color='#0f172a')
    
    channels = [("bioconda", "#0284c7"), ("conda-forge", "#d97706"), ("defaults", "#475569"), ("pypi", "#7c3aed")]
    for idx, (ch, col) in enumerate(channels):
        y = 5.8 - idx * 1.1
        ax.add_patch(patches.FancyBboxPatch((1.8, y), 5.4, 0.8, boxstyle="round,pad=0.1", facecolor=col, alpha=0.15, edgecolor=col, linewidth=2))
        ax.text(2.2, y+0.4, f"channel: {ch}", fontsize=15, fontweight='bold', color=col, va='center')

    # Right Box: Clean Terminal Output
    ax.add_patch(patches.FancyBboxPatch((8.5, 1.5), 6.5, 6, boxstyle="round,pad=0.2", facecolor='#0f172a', edgecolor='#1e293b', linewidth=2))
    ax.scatter([8.9, 9.2, 9.5], [7.1, 7.1, 7.1], color=['#ef4444', '#f59e0b', '#10b981'], s=60)
    ax.text(11.75, 7.1, "bash - terminal", fontsize=12, color='#94a3b8', ha='center', va='center', family='monospace')
    
    term_text = (
        "$ conda create -n omics_env python=3.10\n"
        "Retrieving package metadata... Done\n"
        "Solving environment: done\n\n"
        "## Package Plan ##\n"
        "  - bioconda::samtools=1.19\n"
        "  - bioconda::bedtools=2.31\n"
        "  - conda-forge::scanpy=1.9.6\n\n"
        "Proceed ([y]/n)? y\n"
        "Executing transaction: done\n"
        "# Environment activated: omics_env"
    )
    ax.text(8.8, 4.2, term_text, fontsize=12, color='#4ade80', family='monospace', va='center', linespacing=1.4)
    
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.5)
    plt.savefig('images/conda-environment.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Created images/conda-environment.png")

# ==========================================
# 3. MAMBA & MICROMAMBA GUIDE
# ==========================================
def make_mamba_guide():
    fig, ax = plt.subplots(figsize=(16, 9), facecolor='white')
    ax.set_facecolor('#f8fafc')
    ax.axis('off')
    
    ax.text(8, 8.5, "Mamba & Micromamba: High-Speed Package Resolution", fontsize=24, fontweight='bold', ha='center', color='#0f172a')
    
    categories = ['Small Env', 'Complex Omics Env', 'Bulk Update']
    conda_times = [45, 240, 180]
    mamba_times = [4, 12, 9]
    
    x = np.arange(len(categories))
    width = 0.35
    
    ax_bar = fig.add_axes([0.1, 0.2, 0.4, 0.55], facecolor='white')
    ax_bar.bar(x - width/2, conda_times, width, label='Standard Conda (sec)', color='#94a3b8')
    ax_bar.bar(x + width/2, mamba_times, width, label='Mamba / Micromamba (sec)', color='#059669')
    
    ax_bar.set_ylabel('Resolution Time (seconds)', fontsize=14, fontweight='bold')
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(categories, fontsize=12, fontweight='bold')
    ax_bar.legend(fontsize=12)
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)

    ax.add_patch(patches.FancyBboxPatch((9, 1.8), 6, 5.5, boxstyle="round,pad=0.2", facecolor='white', edgecolor='#10b981', linewidth=2.5))
    ax.text(12, 6.7, "Why Micromamba?", fontsize=20, fontweight='bold', color='#059669', ha='center')
    
    features = [
        "✓ Pure C++ Implementation (libmamba)",
        "✓ Zero Python dependency footprint",
        "✓ Multi-threaded parallel downloads",
        "✓ Single standalone binary (< 15MB)",
        "✓ Ideal for Docker & HPC Containers"
    ]
    for idx, ft in enumerate(features):
        ax.text(9.4, 5.7 - idx*0.8, ft, fontsize=14, fontweight='bold', color='#1e293b')

    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.5)
    plt.savefig('images/mamba-micromamba.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Created images/mamba-micromamba.png")

# ==========================================
# 4. SCRNA TRAJECTORY INFERENCE
# ==========================================
def make_trajectory_inference():
    fig, ax = plt.subplots(figsize=(16, 9), facecolor='white')
    ax.set_facecolor('#ffffff')
    
    np.random.seed(42)
    r_x = np.random.normal(2, 0.4, 200)
    r_y = np.random.normal(5, 0.4, 200)
    
    a_x = np.linspace(2, 14, 400) + np.random.normal(0, 0.3, 400)
    a_y = 5 + np.sin((a_x-2)/2)*2.5 + np.random.normal(0, 0.3, 400)
    
    b_x = np.linspace(6, 14, 300) + np.random.normal(0, 0.3, 300)
    b_y = 5 - (b_x-6)*0.4 + np.random.normal(0, 0.3, 300)
    
    ax.scatter(r_x, r_y, c='#3b82f6', s=35, alpha=0.7, label='Stem Cells')
    ax.scatter(a_x, a_y, c=a_x, cmap='viridis', s=35, alpha=0.7)
    ax.scatter(b_x, b_y, c=b_x, cmap='plasma', s=35, alpha=0.7)
    
    t_curve = np.linspace(2, 14, 100)
    curve_a_y = 5 + np.sin((t_curve-2)/2)*2.5
    curve_b_y = 5 - (t_curve[t_curve>=6]-6)*0.4
    
    ax.plot(t_curve, curve_a_y, color='black', lw=4, zorder=5)
    ax.plot(t_curve[t_curve>=6], curve_b_y, color='black', lw=4, zorder=5)
    
    ax.scatter([2, 6, 14, 14], [5, 5, curve_a_y[-1], curve_b_y[-1]], color='white', edgecolor='black', s=250, linewidth=3, zorder=6)
    
    ax.text(2, 5.8, "Root Node (T0)", fontsize=16, fontweight='bold', bbox=dict(facecolor='white', edgecolor='#cbd5e1', boxstyle='round,pad=0.3'))
    ax.text(6, 6.2, "Bifurcation Point", fontsize=16, fontweight='bold', bbox=dict(facecolor='white', edgecolor='#cbd5e1', boxstyle='round,pad=0.3'))
    ax.text(13.8, curve_a_y[-1]+0.8, "Fate A: Neurons", fontsize=16, fontweight='bold', color='#15803d')
    ax.text(13.8, curve_b_y[-1]-0.8, "Fate B: Astrocytes", fontsize=16, fontweight='bold', color='#c2410c')

    ax.set_title("Single-Cell Trajectory Inference & Cell Fate Lineages", fontsize=22, fontweight='bold', pad=20, color='#0f172a')
    ax.axis('off')
    
    plt.savefig('images/scrna_heterogeneity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Created images/scrna_heterogeneity.png")

# ==========================================
# 5. SCRNA DOWNSTREAM ANALYSIS & METABOLISM
# ==========================================
def make_downstream_analysis():
    fig = plt.figure(figsize=(16, 9), facecolor='white')
    
    ax1 = fig.add_axes([0.08, 0.15, 0.38, 0.7], facecolor='#f8fafc')
    np.random.seed(42)
    l2fc = np.random.normal(0, 1.5, 1000)
    pval = -np.log10(np.random.uniform(0.00001, 1, 1000))
    
    deg_up = (l2fc > 1) & (pval > 2)
    deg_down = (l2fc < -1) & (pval > 2)
    
    ax1.scatter(l2fc[~deg_up & ~deg_down], pval[~deg_up & ~deg_down], color='#94a3b8', alpha=0.5, s=20)
    ax1.scatter(l2fc[deg_up], pval[deg_up], color='#ef4444', alpha=0.8, s=40, label='Upregulated')
    ax1.scatter(l2fc[deg_down], pval[deg_down], color='#2563eb', alpha=0.8, s=40, label='Downregulated')
    
    ax1.axvline(1, ls='--', color='#cbd5e1')
    ax1.axvline(-1, ls='--', color='#cbd5e1')
    ax1.axhline(2, ls='--', color='#cbd5e1')
    ax1.set_xlabel('Log2 Fold Change', fontsize=14, fontweight='bold')
    ax1.set_ylabel('-Log10 Adjusted P-value', fontsize=14, fontweight='bold')
    ax1.set_title("A. Differential Expression (Volcano Plot)", fontsize=16, fontweight='bold', loc='left')
    ax1.legend(loc='upper right')

    ax2 = fig.add_axes([0.55, 0.15, 0.38, 0.7], facecolor='#ffffff')
    genes = ['CD3D', 'CD4', 'CD8A', 'MS4A1', 'CD14', 'FCGR3A', 'NCAM1', 'PPBP']
    clusters = ['T CD4+', 'T CD8+', 'B Cells', 'Mono CD14+', 'Mono FCGR3+', 'NK Cells', 'Platelets']
    
    grid_x, grid_y = np.meshgrid(range(len(genes)), range(len(clusters)))
    
    exp_matrix = np.zeros((len(clusters), len(genes)))
    exp_matrix[0, 0:2] = 2.5; exp_matrix[1, 0] = 2.0; exp_matrix[1, 2] = 2.8
    exp_matrix[2, 3] = 3.0; exp_matrix[3, 4] = 2.7; exp_matrix[4, 5] = 2.4
    exp_matrix[5, 6] = 2.9; exp_matrix[6, 7] = 3.1
    
    sizes = (exp_matrix.flatten() + 0.2) * 120
    colors = exp_matrix.flatten()
    
    sc = ax2.scatter(grid_x.flatten(), grid_y.flatten(), s=sizes, c=colors, cmap='Reds', edgecolor='#cbd5e1')
    ax2.set_xticks(range(len(genes)))
    ax2.set_xticklabels(genes, rotation=45, ha='right', fontsize=12, fontweight='bold')
    ax2.set_yticks(range(len(clusters)))
    ax2.set_yticklabels(clusters, fontsize=12, fontweight='bold')
    ax2.set_title("B. Marker Gene DotPlot Expression", fontsize=16, fontweight='bold', loc='left')
    
    cbar = fig.colorbar(sc, ax=ax2, orientation='vertical', fraction=0.04, pad=0.04)
    cbar.set_label('Mean Expression', fontsize=11)

    fig.suptitle("scRNA-Seq Downstream Analysis: Marker Discovery & Cell States", fontsize=22, fontweight='bold', y=0.96)
    
    plt.savefig('images/scrna_metabolism.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ Created images/scrna_metabolism.png")

make_bioinformatics_intro()
make_conda_environment()
make_mamba_guide()
make_trajectory_inference()
make_downstream_analysis()
print("All publication-grade 16:9 banners successfully generated!")
