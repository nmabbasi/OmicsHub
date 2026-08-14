import matplotlib.pyplot as plt
import numpy as np

# Create a wide figure (16:9 ratio)
fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor('#ffffff')

# Generate pseudotime trajectory data
t = np.linspace(0, 10, 500)
# Main branch
x1 = t + np.random.normal(0, 0.2, 500)
y1 = np.sin(t/2) + np.random.normal(0, 0.2, 500)
c1 = t # Color by pseudotime

# Branch 2 (diverging at t=5)
t2 = np.linspace(5, 10, 300)
x2 = t2 + np.random.normal(0, 0.2, 300)
y2 = np.sin(5/2) - (t2-5)*0.5 + np.random.normal(0, 0.2, 300)
c2 = t2

# Plot
scatter1 = ax.scatter(x1, y1, c=c1, cmap='viridis', s=30, alpha=0.7, edgecolors='none')
scatter2 = ax.scatter(x2, y2, c=c2, cmap='viridis', s=30, alpha=0.7, edgecolors='none')

# Draw Principal Graph (the "tree" lines)
ax.plot([0, 5], [0, np.sin(2.5)], color='black', linewidth=4, zorder=3)
ax.plot([5, 10], [np.sin(2.5), np.sin(5)], color='black', linewidth=4, zorder=3)
ax.plot([5, 10], [np.sin(2.5), np.sin(5) - 2.5], color='black', linewidth=4, zorder=3)

# Nodes
ax.scatter([0, 5, 10, 10], [0, np.sin(2.5), np.sin(5), np.sin(5)-2.5], color='white', edgecolor='black', s=200, zorder=4, linewidth=3)
ax.text(5, np.sin(2.5)+0.5, "Branch Point", fontsize=20, fontweight='bold', ha='center', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))

# Clean up
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0)
plt.savefig('images/scrna_heterogeneity.png', dpi=120, bbox_inches='tight', pad_inches=0)
print("Trajectory plot generated!")
