import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.patheffects as pe

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor('#ffffff')

np.random.seed(42)
data = np.random.randn(20, 100)
data[0:5, 0:30] += 3
data[10:15, 50:100] -= 2
data[15:20, 30:70] += 2

sns.heatmap(data, cmap="RdYlBu_r", cbar=False, xticklabels=False, yticklabels=False, ax=ax)

ax.text(50, 10, "Metabolic Gene Signatures", fontsize=48, fontweight='bold', color='white',
        ha='center', va='center', path_effects=[pe.withStroke(linewidth=8, foreground="black")])

plt.tight_layout(pad=0)
plt.savefig('images/scrna_metabolism.png', dpi=120, bbox_inches='tight', pad_inches=0)
print("Metabolism heatmap generated!")
