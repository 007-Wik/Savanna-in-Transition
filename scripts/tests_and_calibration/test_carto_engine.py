"""Test script for master cartography engine."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pyproj import Transformer
import numpy as np
from pathlib import Path

fig, ax = plt.subplots(figsize=(10, 8.5))
ax.set_facecolor("white")
fig.patch.set_facecolor("white")

# Test DMS coordinates
left, right, bottom, top = 641580.0, 830730.0, 1116420.0, 1297170.0
ax.set_xlim(left - 5000, right + 5000)
ax.set_ylim(bottom - 5000, top + 5000)

trans_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)

# Test Compass Rose
def draw_compass_rose(ax, cx, cy, r):
    # 4 Cardinal points
    # North
    ax.fill([cx, cx, cx - r*0.16], [cy, cy + r, cy], color="#111111", zorder=25)
    ax.fill([cx, cx, cx + r*0.16], [cy, cy + r, cy], color="#ffffff", edgecolor="#111111", lw=0.6, zorder=25)
    # South
    ax.fill([cx, cx, cx + r*0.16], [cy, cy - r*0.75, cy], color="#111111", zorder=25)
    ax.fill([cx, cx, cx - r*0.16], [cy, cy - r*0.75, cy], color="#ffffff", edgecolor="#111111", lw=0.6, zorder=25)
    # East
    ax.fill([cx, cx + r*0.75, cx], [cy, cy, cy + r*0.16], color="#111111", zorder=25)
    ax.fill([cx, cx + r*0.75, cx], [cy, cy, cy - r*0.16], color="#ffffff", edgecolor="#111111", lw=0.6, zorder=25)
    # West
    ax.fill([cx, cx - r*0.75, cx], [cy, cy, cy - r*0.16], color="#111111", zorder=25)
    ax.fill([cx, cx - r*0.75, cx], [cy, cy, cy + r*0.16], color="#ffffff", edgecolor="#111111", lw=0.6, zorder=25)
    # Pivot circle
    circle = patches.Circle((cx, cy), r*0.09, facecolor="#ffffff", edgecolor="#111111", lw=0.8, zorder=26)
    ax.add_patch(circle)
    inner = patches.Circle((cx, cy), r*0.04, facecolor="#111111", edgecolor="none", zorder=27)
    ax.add_patch(inner)
    # North Label
    ax.text(cx, cy + r + r*0.08, "N", fontfamily="Times New Roman", fontsize=13, fontweight="bold", ha="center", va="bottom", zorder=28)

draw_compass_rose(ax, right - 18000, top - 24000, 10000)

plt.savefig("outputs/test_carto.png", dpi=150)
plt.close(fig)
print("Carto test completed successfully!")

