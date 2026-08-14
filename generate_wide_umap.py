import matplotlib.pyplot as plt
from sklearn.datasets import make_blobs
import numpy as np

# Generate fake single-cell data (5 clusters)
X, y = make_blobs(n_samples=5000, centers=5, cluster_std=[1.0, 1.5, 0.8, 1.2, 0.9], random_state=42)

# Elongate the X axis to naturally fill a wide banner
X[:, 0] = X[:, 0] * 2.5

# Colors (Seurat-like default palette)
colors = ['#F8766D', '#A3A500', '#00BF7D', '#00B0F6', '#E76BF3']
cluster_names = ['T cells', 'B cells', 'Monocytes', 'NK cells', 'Fibroblasts']

fig, ax = plt.subplots(figsize=(16, 7)) # 16:7 is a beautiful wide banner ratio
ax.set_facecolor('white')

for i in range(5):
    # Plot points for this cluster
    mask = y == i
    ax.scatter(X[mask, 0], X[mask, 1], s=4, color=colors[i], alpha=0.6, edgecolors='none')
    
    # Calculate center for annotation
    center_x, center_y = np.median(X[mask, 0]), np.median(X[mask, 1])
    
    # Add annotation text with a slight white outline for readability
    import matplotlib.patheffects as pe
    ax.text(center_x, center_y, cluster_names[i], 
            fontsize=24, fontweight='bold', color='black',
            ha='center', va='center',
            path_effects=[pe.withStroke(linewidth=4, foreground="white")])

# Hide axes, ticks, borders for a clean banner look
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0)
plt.savefig('images/single-cell-analysis.png', dpi=150, bbox_inches='tight', pad_inches=0)
print("Wide UMAP banner generated!")
