import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patheffects as pe

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor('#ffffff') # White background

# Generate a stylized DNA double helix transforming into data points
t = np.linspace(0, 16, 1000)
# Helix 1
y1 = np.sin(t) * 3 + 4.5
# Helix 2
y2 = np.sin(t + np.pi) * 3 + 4.5

# Plot continuous lines for the "biological" left side
mask_left = t < 8
ax.plot(t[mask_left], y1[mask_left], color='#0ea5e9', linewidth=4, alpha=0.8)
ax.plot(t[mask_left], y2[mask_left], color='#10b981', linewidth=4, alpha=0.8)

# Add biological rungs on the left
for i in np.arange(0, 8, 0.5):
    ax.plot([i, i], [np.sin(i)*3 + 4.5, np.sin(i + np.pi)*3 + 4.5], color='#94a3b8', linewidth=2, alpha=0.5)

# Plot discrete data points for the "computational" right side (transitioning)
mask_right = t >= 8
# Subsample for data points
t_right = t[mask_right][::5]
y1_right = y1[mask_right][::5]
y2_right = y2[mask_right][::5]

# Add noise to simulate "data points" spreading out
noise1 = np.random.normal(0, 0.4, len(t_right))
noise2 = np.random.normal(0, 0.4, len(t_right))

ax.scatter(t_right, y1_right + noise1, color='#0ea5e9', s=50, alpha=0.6, edgecolors='white')
ax.scatter(t_right, y2_right + noise2, color='#10b981', s=50, alpha=0.6, edgecolors='white')

# Add "digital" connections on the right
for i in range(len(t_right)):
    if np.random.rand() > 0.5:
        ax.plot([t_right[i], t_right[i]], [4.5, y1_right[i] + noise1[i]], color='#cbd5e1', linewidth=1, alpha=0.4, linestyle='--')
        ax.plot([t_right[i], t_right[i]], [4.5, y2_right[i] + noise2[i]], color='#cbd5e1', linewidth=1, alpha=0.4, linestyle='--')

# Text reflecting the website's core identity
ax.text(8, 4.5, "OmicsHub", fontsize=64, fontweight='bold', color='#1e293b',
        ha='center', va='bottom', path_effects=[pe.withStroke(linewidth=8, foreground="white")])
ax.text(8, 4.1, "Single-cell & Bioinformatics Workflows", fontsize=28, color='#475569',
        ha='center', va='top', path_effects=[pe.withStroke(linewidth=6, foreground="white")])

ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0)
plt.savefig('images/bioinformatics-intro.png', dpi=120, bbox_inches='tight', pad_inches=0)
print("DNA to Data workflow banner generated!")
