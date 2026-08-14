import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor('#ffffff') # White background!

np.random.seed(42)
n_nodes = 250 # More nodes for a denser network
# Ensure nodes reach the absolute edges by using -1 to 17 and -1 to 10
x = np.random.uniform(-1, 17, n_nodes)
y = np.random.uniform(-1, 10, n_nodes)

# Plot network lines connecting close nodes
for i in range(n_nodes):
    for j in range(i+1, n_nodes):
        dist = np.sqrt((x[i]-x[j])**2 + (y[i]-y[j])**2)
        if dist < 1.8: # Slightly longer connections
            ax.plot([x[i], x[j]], [y[i], y[j]], color='#94a3b8', alpha=0.4, linewidth=1.5)

# Plot nodes (much bigger and more colorful)
sizes = np.random.rand(n_nodes) * 600 + 100
colors = np.random.rand(n_nodes)
ax.scatter(x, y, s=sizes, c=colors, cmap='viridis', alpha=0.7, edgecolors='white', linewidth=1)

# Add central text (adapted for white background)
ax.text(8, 4.5, "Bioinformatics & Systems Biology", fontsize=48, fontweight='bold', color='black',
        ha='center', va='center', bbox=dict(facecolor='white', alpha=0.9, edgecolor='#cbd5e1', boxstyle='round,pad=0.5'))

ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0)
plt.savefig('images/bioinformatics-intro.png', dpi=120, bbox_inches='tight', pad_inches=0)
print("Intro network generated with white background!")
