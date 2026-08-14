import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches
import matplotlib.patheffects as pe

fig, ax = plt.subplots(figsize=(16, 9))
ax.set_facecolor('#ffffff')

# --- 1. Draw Connecting Pipeline ---
ax.plot([2, 14], [5.5, 5.5], color='#e2e8f0', linewidth=6, zorder=0)
# Arrow heads
for x in [4, 8, 12]:
    ax.add_patch(patches.Polygon([[x-0.2, 5.7], [x+0.2, 5.5], [x-0.2, 5.3]], color='#cbd5e1', zorder=1))

# --- Stage 1: DNA (X=2) ---
t = np.linspace(-1, 1, 100)
ax.plot(2 + np.sin(t*3)*0.6, 5.5 + t*1.5, color='#0ea5e9', linewidth=4)
ax.plot(2 + np.sin(t*3 + np.pi)*0.6, 5.5 + t*1.5, color='#10b981', linewidth=4)
for i in np.arange(-0.8, 0.9, 0.3):
    ax.plot([2 + np.sin(i*3)*0.6, 2 + np.sin(i*3 + np.pi)*0.6], [5.5 + i*1.5, 5.5 + i*1.5], color='#94a3b8', linewidth=2)
ax.text(2, 3.2, "1. Samples & DNA", fontsize=22, fontweight='bold', color='#1e293b', ha='center')
ax.text(2, 2.7, "Tissue isolation\n& extraction", fontsize=16, color='#64748b', ha='center', linespacing=1.5)

# --- Stage 2: Wet Lab Flask (X=6) ---
# Flask outline
flask_x = [5.7, 5.7, 5.2, 6.8, 6.3, 6.3]
flask_y = [7.0, 6.0, 4.0, 4.0, 6.0, 7.0]
ax.add_patch(patches.Polygon(list(zip(flask_x, flask_y)), fill=False, edgecolor='#334155', linewidth=4, zorder=2))
# Liquid inside
liq_x = [5.3, 6.7, 6.4, 5.6]
liq_y = [4.3, 4.3, 5.5, 5.5]
ax.add_patch(patches.Polygon(list(zip(liq_x, liq_y)), fill=True, color='#0ea5e9', alpha=0.6, zorder=1))
# Bubbles
ax.scatter([5.8, 6.1, 6.3], [4.6, 5.0, 4.7], color='white', s=[30, 50, 20], zorder=2)
ax.text(6, 3.2, "2. Wet Lab Prep", fontsize=22, fontweight='bold', color='#1e293b', ha='center')
ax.text(6, 2.7, "Library construction\n& QC", fontsize=16, color='#64748b', ha='center', linespacing=1.5)

# --- Stage 3: NGS Sequencer (X=10) ---
ax.add_patch(patches.Rectangle((9.0, 4.0), 2.0, 3.0, fill=True, color='#f1f5f9', edgecolor='#334155', linewidth=4, zorder=2))
# Screen/Slots
ax.add_patch(patches.Rectangle((9.2, 6.0), 1.6, 0.8, fill=True, color='#1e293b', zorder=3))
ax.add_patch(patches.Rectangle((9.2, 4.5), 1.6, 0.2, fill=True, color='#cbd5e1', zorder=3))
ax.add_patch(patches.Rectangle((9.2, 5.0), 1.6, 0.2, fill=True, color='#cbd5e1', zorder=3))
# Glowing lights
ax.scatter([9.4, 9.7, 10.0], [6.4, 6.4, 6.4], color=['#10b981', '#10b981', '#38bdf8'], s=80, zorder=4)
ax.text(10, 3.2, "3. Sequencing", fontsize=22, fontweight='bold', color='#1e293b', ha='center')
ax.text(10, 2.7, "Illumina NGS &\nFastQ generation", fontsize=16, color='#64748b', ha='center', linespacing=1.5)

# --- Stage 4: Bioinformatics (X=14) ---
# Laptop screen
ax.add_patch(patches.Rectangle((12.8, 4.5), 2.4, 2.0, fill=True, color='#1e293b', edgecolor='#334155', linewidth=3, zorder=2))
# Laptop base
ax.add_patch(patches.Polygon([[12.4, 4.0], [15.6, 4.0], [15.2, 4.5], [12.8, 4.5]], fill=True, color='#94a3b8', zorder=2))
# Code lines on screen
ax.plot([13.0, 14.0], [6.0, 6.0], color='#10b981', linewidth=3, zorder=3)
ax.plot([13.0, 14.8], [5.6, 5.6], color='#38bdf8', linewidth=3, zorder=3)
ax.plot([13.0, 14.3], [5.2, 5.2], color='#38bdf8', linewidth=3, zorder=3)
ax.text(14, 3.2, "4. Bioinformatics", fontsize=22, fontweight='bold', color='#1e293b', ha='center')
ax.text(14, 2.7, "Data analysis &\nVisualization", fontsize=16, color='#64748b', ha='center', linespacing=1.5)

# --- Main Title ---
ax.text(8, 8.0, "OmicsHub Workflow", fontsize=48, fontweight='bold', color='#0f172a', ha='center',
        path_effects=[pe.withStroke(linewidth=6, foreground="white")])

ax.set_xlim(0, 16)
ax.set_ylim(0, 9)
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout(pad=0)
plt.savefig('images/bioinformatics-intro.png', dpi=150, bbox_inches='tight', pad_inches=0)
print("Infographic banner generated!")
