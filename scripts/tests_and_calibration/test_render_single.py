"""Test script to verify layout of DEM and LULC maps."""
import rasterio
import numpy as np
import geopandas as gpd
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm, LinearSegmentedColormap
import matplotlib.patches as patches
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # repository root
import warnings
warnings.filterwarnings("ignore")

OUT_R = ROOT / "outputs" / "rasters"
OUT_M = ROOT / "outputs" / "maps"
OUT_V = ROOT / "outputs" / "vectors"

# 1. Times New Roman
plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.serif": ["Times New Roman"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Times New Roman",
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#111111",
    "axes.labelcolor": "#111111",
})

CLASS_NAMES = {
    1: "Woodland / Forest",
    2: "Cropland / Agriculture",
    3: "Grassland / Savanna",
    4: "Bare / Degraded",
    5: "Waterbody",
    6: "Settlement",
}

LULC_COLORS = {
    1: "#2D6A4F",   # Woodland / Forest
    2: "#E5A93C",   # Cropland / Agriculture
    3: "#8CB369",   # Grassland / Savanna
    4: "#BC6C25",   # Bare / Degraded
    5: "#1D6F8A",   # Waterbody
    6: "#BA181B",   # Settlement
}

DEM_COLORS = ["#0055ff", "#00bfff", "#2ecc71", "#a8e063", "#f1c40f", "#e67e22", "#a0522d", "#8b4513", "#d2b48c", "#ffffff"]
DEM_CMAP = LinearSegmentedColormap.from_list("dem_rainbow", DEM_COLORS, N=256)

TRANS_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)

DMS_TICKS_X = [
    (4.50, "4°30'E"),
    (4.75, "4°45'E"),
    (5.00, "5°00'E"),
    (5.25, "5°15'E"),
    (5.50, "5°30'E"),
    (5.75, "5°45'E"),
    (6.00, "6°00'E"),
]

DMS_TICKS_Y = [
    (10.25, "10°15'N"),
    (10.50, "10°30'N"),
    (10.75, "10°45'N"),
    (11.00, "11°00'N"),
    (11.25, "11°15'N"),
    (11.50, "11°30'N"),
    (11.75, "11°45'N"),
]

def load_hillshade_and_elev():
    with rasterio.open(OUT_R / "Hillshade.tif") as src:
        hs = src.read(1)
        bounds = src.bounds
        transform = src.transform
    with rasterio.open(str(ROOT / "data" / "Kebbi_SRTM.tif")) as src:
        elev = src.read(1).astype(np.float32)
    hs_m = np.ma.masked_equal(hs, 0)
    elev_m = np.ma.masked_where((elev <= 0) | ~np.isfinite(elev) | (hs == 0), elev)
    return hs_m, elev_m, bounds, transform

def load_vectors():
    lgas = gpd.read_file(OUT_V / "LGAs.shp")
    aoi = gpd.read_file(OUT_V / "AOI.shp")
    return lgas, aoi

def draw_north_needle(ax, x, y, length):
    w = length * 0.18
    ax.fill([x, x, x - w], [y, y + length, y], color="#111111", zorder=30)
    ax.fill([x, x, x + w], [y, y + length, y], color="#ffffff", edgecolor="#111111", lw=0.8, zorder=30)
    ax.text(x, y + length + length * 0.08, "N", fontfamily="Times New Roman", fontsize=11, fontweight="bold",
            ha="center", va="bottom", color="#111111", zorder=31)

def draw_carto_scalebar(ax, x0, y0, length_km=40, height_m=2000):
    total_len = length_km * 1000.0
    seg_len = total_len / 4.0
    blocks = [
        (x0, seg_len * 0.5, "#111111"),
        (x0 + seg_len * 0.5, seg_len * 0.5, "#ffffff"),
        (x0 + seg_len, seg_len, "#111111"),
        (x0 + seg_len * 2, seg_len, "#ffffff"),
        (x0 + seg_len * 3, seg_len, "#111111"),
    ]
    for bx, bw, col in blocks:
        ax.add_patch(patches.Rectangle((bx, y0), bw, height_m, facecolor=col, edgecolor="#111111", lw=0.8, zorder=25))
    labels = [(0, "0"), (seg_len, "10"), (seg_len * 2, "20"), (total_len, f"{length_km} km")]
    for offset, text in labels:
        ax.plot([x0 + offset, x0 + offset], [y0 + height_m, y0 + height_m + 800], color="#111111", lw=0.8, zorder=26)
        ax.text(x0 + offset, y0 + height_m + 1100, text, fontfamily="Times New Roman", fontsize=7.5,
                ha="center", va="bottom", color="#111111", zorder=26)

def setup_phd_neatline(ax, bounds):
    left, right, bottom, top = bounds.left, bounds.right, bounds.bottom, bounds.top
    w = right - left
    h = top - bottom

    rect = patches.Rectangle((left, bottom), w, h, linewidth=1.2, edgecolor="#111111", facecolor="none", zorder=40)
    ax.add_patch(rect)

    for lon, label in DMS_TICKS_X:
        lats_pts = np.linspace(9.9, 12.0, 150)
        xs, ys = TRANS_TO_UTM.transform(np.full_like(lats_pts, lon), lats_pts)
        valid = (xs >= left) & (xs <= right) & (ys >= bottom) & (ys <= top)
        if valid.any():
            ax.plot(xs[valid], ys[valid], color="#dcdcdc", linestyle="-", linewidth=0.5, zorder=5)

        x_bot = np.interp(bottom, ys, xs)
        x_top = np.interp(top, ys, xs)

        if left <= x_bot <= right:
            ax.plot([x_bot, x_bot], [bottom, bottom - h * 0.010], color="#111111", lw=1.0, clip_on=False, zorder=41)
            ax.text(x_bot, bottom - h * 0.016, label, fontfamily="Times New Roman", fontsize=8.0,
                    ha="center", va="top", color="#111111")
        if left <= x_top <= right:
            ax.plot([x_top, x_top], [top, top + h * 0.010], color="#111111", lw=1.0, clip_on=False, zorder=41)
            ax.text(x_top, top + h * 0.016, label, fontfamily="Times New Roman", fontsize=8.0,
                    ha="center", va="bottom", color="#111111")

    for lat, label in DMS_TICKS_Y:
        lons_pts = np.linspace(4.0, 6.3, 150)
        xs, ys = TRANS_TO_UTM.transform(lons_pts, np.full_like(lons_pts, lat))
        valid = (xs >= left) & (xs <= right) & (ys >= bottom) & (ys <= top)
        if valid.any():
            ax.plot(xs[valid], ys[valid], color="#dcdcdc", linestyle="-", linewidth=0.5, zorder=5)

        y_left = np.interp(left, xs, ys)
        y_right = np.interp(right, xs, ys)

        if bottom <= y_left <= top:
            ax.plot([left, left - w * 0.010], [y_left, y_left], color="#111111", lw=1.0, clip_on=False, zorder=41)
            ax.text(left - w * 0.014, y_left, label, fontfamily="Times New Roman", fontsize=8.0,
                    ha="right", va="center", color="#111111")
        if bottom <= y_right <= top:
            ax.plot([right, right + w * 0.010], [y_right, y_right], color="#111111", lw=1.0, clip_on=False, zorder=41)
            ax.text(right + w * 0.014, y_right, label, fontfamily="Times New Roman", fontsize=8.0,
                    ha="left", va="center", color="#111111")

    ax.set_xlim(left, right)
    ax.set_ylim(bottom, top)
    ax.set_xticks([])
    ax.set_yticks([])

def draw_lga_boundaries_and_centres(ax, lgas, bounds):
    lgas.boundary.plot(ax=ax, edgecolor="#444444", linewidth=0.6, linestyle="--", zorder=15)
    offsets = {
        "Zuru": (0, 3000),
        "Fakai": (0, 0),
        "Shanga": (0, 0),
        "Sakaba": (0, 0),
        "Yauri": (0, -2500),
        "Danko Wasagu": (0, 0),
        "Ngaski": (0, 0),
    }
    for _, row in lgas.iterrows():
        c = row.geometry.centroid
        name = row["ADM2_NAME"]
        dx, dy = offsets.get(name, (0, 0))
        if bounds.left <= c.x <= bounds.right and bounds.bottom <= c.y <= bounds.top:
            ax.plot(c.x + dx, c.y + dy, "o", color="#111111", markersize=2.5, zorder=22)
            ax.text(c.x + dx + 1500, c.y + dy + 1000, name, fontfamily="Times New Roman", fontsize=6.8,
                    fontweight="bold", color="#111111",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="white", alpha=0.85, edgecolor="none"), zorder=23)

def add_phd_header_and_footer(fig, title_line1, title_line2, title_line3, source_text):
    # Prominent Header outside neatline at top
    fig.text(0.5, 0.962, title_line1, fontfamily="Times New Roman", fontsize=11, ha="center", va="center", color="#222222")
    fig.text(0.5, 0.936, title_line2, fontfamily="Times New Roman", fontsize=20, ha="center", va="center", fontweight="bold", color="#111111")
    fig.text(0.5, 0.912, title_line3, fontfamily="Times New Roman", fontsize=9.5, ha="center", va="center", fontstyle="italic", color="#444444")

    # Bottom Footer outside neatline
    fig.text(0.10, 0.032, "Projection: UTM Zone 31N | Datum: WGS 84", fontfamily="Times New Roman", fontsize=7.5, color="#555555", ha="left")
    fig.text(0.92, 0.032, source_text, fontfamily="Times New Roman", fontsize=7.5, color="#555555", ha="right")

print("Rendering test DEM...")
hs, elev, bounds, transform = load_hillshade_and_elev()
lgas, aoi = load_vectors()

fig = plt.figure(figsize=(10, 13), dpi=200)
ax = fig.add_axes([0.10, 0.065, 0.82, 0.82])

ax.imshow(elev, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
          cmap=DEM_CMAP, vmin=110, vmax=656, aspect="equal", zorder=2)
ax.imshow(hs, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
          cmap="gray", vmin=1, vmax=255, aspect="equal", alpha=0.45, zorder=3)

aoi.boundary.plot(ax=ax, edgecolor="#8B0000", linewidth=1.8, zorder=20)
draw_lga_boundaries_and_centres(ax, lgas, bounds)
setup_phd_neatline(ax, bounds)

# Lower-Right Quadrant placement (0.0 km² land overlap):
# 1. Elevation colorbar
cb_x = 746000
cb_y = 1192000
cb_w = 70000
cb_h = 4200
ax.text(cb_x + cb_w * 0.5, cb_y + cb_h + 1800, "Elevation (m a.s.l.)", fontfamily="Times New Roman",
        fontsize=8.0, fontweight="bold", ha="center", va="bottom", color="#111111", zorder=30)
cb_box = patches.Rectangle((cb_x, cb_y), cb_w, cb_h, facecolor="none", edgecolor="#111111", lw=0.6, zorder=30)
ax.add_patch(cb_box)
gradient = np.linspace(0, 1, 256).reshape(1, 256)
ax.imshow(gradient, extent=[cb_x, cb_x + cb_w, cb_y, cb_y + cb_h], cmap=DEM_CMAP, aspect="auto", zorder=29)
ax.text(cb_x, cb_y - 2000, "110", fontfamily="Times New Roman", fontsize=7.5, ha="center", va="top", color="#111111", zorder=30)
ax.text(cb_x + cb_w * 0.5, cb_y - 2000, "383", fontfamily="Times New Roman", fontsize=7.5, ha="center", va="top", color="#111111", zorder=30)
ax.text(cb_x + cb_w, cb_y - 2000, "656", fontfamily="Times New Roman", fontsize=7.5, ha="center", va="top", color="#111111", zorder=30)

# 2. Legend Box
leg_x = 746000
leg_y = 1146000
leg_w = 70000
leg_h = 32000
bg = patches.Rectangle((leg_x, leg_y), leg_w, leg_h, facecolor="#ffffff", edgecolor="#333333", lw=0.6, alpha=0.95, zorder=25)
ax.add_patch(bg)
ax.text(leg_x + 3000, leg_y + leg_h - 4500, "Legend", fontfamily="Times New Roman", fontsize=9.0, fontweight="bold", color="#111111", zorder=26)

ax.plot([leg_x + 3500, leg_x + 15000], [leg_y + leg_h - 11000, leg_y + leg_h - 11000], color="#8B0000", lw=2.0, zorder=26)
ax.text(leg_x + 18000, leg_y + leg_h - 11000, "Southern Kebbi boundary", fontfamily="Times New Roman", fontsize=7.2, va="center", color="#222222", zorder=26)

ax.plot([leg_x + 3500, leg_x + 15000], [leg_y + leg_h - 18500, leg_y + leg_h - 18500], color="#444444", lw=0.8, linestyle="--", zorder=26)
ax.text(leg_x + 18000, leg_y + leg_h - 18500, "LGA boundary", fontfamily="Times New Roman", fontsize=7.2, va="center", color="#222222", zorder=26)

ax.plot(leg_x + 9250, leg_y + leg_h - 25500, "o", color="#111111", markersize=3.0, zorder=26)
ax.text(leg_x + 18000, leg_y + leg_h - 25500, "LGA headquarters", fontfamily="Times New Roman", fontsize=7.2, va="center", color="#222222", zorder=26)

# 3. Scale Bar & North Arrow
draw_carto_scalebar(ax, 746000, 1124000, length_km=40)
draw_north_needle(ax, 810000, 1124000, length=12000)

add_phd_header_and_footer(fig,
                          "DIGITAL ELEVATION MODEL (DEM) OF",
                          "SOUTHERN KEBBI",
                          "Kebbi State, Federal Republic of Nigeria",
                          "NASA SRTM 30m / USGS Topographic Survey (1:250,000)")

fig.savefig("outputs/test_dem_rendered.png", dpi=200, facecolor="white")
plt.close(fig)
print("[OK] Test DEM rendered successfully!")
