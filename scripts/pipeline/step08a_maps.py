#!/usr/bin/env python3
"""
Step 8a: Master Cartographic Production Engine (Lohara Taluka Reference Standard).
Generates all 14 publication-grade 300 DPI cartographic map plates:
1.  00_StudyArea.png                     - SRTM 30m Topographic Relief & Administrative Boundaries
2.  LULC_2000.png                         - Baseline Land Use & Land Cover (Landsat 5 TM)
3.  LULC_2026.png                         - Current Land Use & Land Cover (Landsat 8/9 OLI, ESRI Benchmarked)
4.  TCC_2000.png                          - True Colour Composite Landsat 5 TM (RGB: 3, 2, 1) [NO THEMATIC LEGEND]
5.  TCC_2026.png                          - True Colour Composite Landsat 8/9 OLI (RGB: 4, 3, 2) [NO THEMATIC LEGEND]
6.  NDVI_2000.png                         - Seasonal Vegetation Health & Greenness (2000)
7.  NDVI_2026.png                         - Seasonal Vegetation Health & Greenness (2026)
8.  NDVI_Change_2000_2026.png             - Bi-temporal Canopy Degradation Dynamics
9.  Transition_overview.png               - Categorical Landscape Transition Architecture
10. Footprint_Forest_to_Agriculture.png   - Agrarian Encroachment Footprint
11. Footprint_Forest_to_Grassland.png     - Pastoral Savannization Footprint
12. Footprint_Forest_to_Bare.png          - Gully Erosion & Severe Degradation Footprint
13. Hotspot_Forest_Loss_KDE.png           - Spatial Kernel Density Deforestation Hotspots (50m KDE)
14. Forest_Loss_Trajectories_Vector.png   - Sieve-Filtered (MMU >= 0.45 ha) Vector Shapefile Trajectories

STRICT SPECIFICATIONS:
- Coordinate tick labels present on ALL FOUR SIDES (Top, Bottom, Left, and Right).
- True Colour Composites (TCC) contain NO thematic legend; only scalebar, north arrow, and sensor text.
- Standard 300 DPI output with Times New Roman typography and dynamic relative paths.
- Outputs saved EXCLUSIVELY into outputs/maps/.
"""
import warnings
from pathlib import Path
import numpy as np
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import pyproj
import scipy.ndimage as ndi
from shapely.geometry import box

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.path import Path as MPath

warnings.filterwarnings("ignore")

# ----------------- Dynamic Base Directory & Paths -----------------
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
OUT_R = BASE_DIR / "outputs" / "rasters"
OUT_V = BASE_DIR / "outputs" / "vectors"
MAPS_DIR = BASE_DIR / "outputs" / "maps"
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# ----------------- Typography & Cartographic Colors -----------------
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]
plt.rcParams["axes.linewidth"] = 0.9

RED = "#c1121f"
INK = "#1a1a1a"
GREY = "#6b7280"
DOT = "#262626"
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]
SUBTITLE = "Kebbi State, Federal Republic of Nigeria"

MAP_MAX_W, MAP_MAX_H, MAP_MIN_W = 9.0, 11.0, 6.5
M_LEFT, M_RIGHT, M_TOP, M_BOTTOM = 0.65, 0.65, 1.45, 0.55
PAD_FRAC = 0.03

# ----------------- Coordinate Transformers -----------------
TO_WGS = pyproj.Transformer.from_crs("EPSG:32631", "EPSG:4326", always_xy=True)
TO_UTM = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32631", always_xy=True)

# ----------------- Vector Layers -----------------
AOI_GDF = gpd.read_file(OUT_V / "AOI.shp")
LGAS_GDF = gpd.read_file(OUT_V / "LGAs.shp")
AOI_UNION = AOI_GDF.geometry.union_all()

LULC_LUT = {
    1: ("Dense Woodland / Tree Canopy",   "#1b4332"),
    2: ("Agricultural / Fallow Matrix",    "#d4a373"),
    3: ("Sudan Savanna Rangeland",         "#ccd5ae"),
    4: ("Bare Soil / Degraded Surface",    "#e29578"),
    5: ("Open Waterbody (Lake Kainji)",    "#2a6f97"),
    6: ("Settlement / Artificial Surface", "#9d0208"),
}

# ----------------- Cartographic Geometry & Clipping -----------------
def geom_to_path(geom):
    verts, codes = [], []
    for poly in getattr(geom, "geoms", [geom]):
        for ring in [poly.exterior, *poly.interiors]:
            xy = np.asarray(ring.coords)
            verts.extend(xy)
            codes.extend([MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY])
    return MPath(verts, codes)

def clip_to_geom(artist, ax, geom):
    patch = mpatches.PathPatch(geom_to_path(geom), transform=ax.transData, fc="none", ec="none")
    try:
        artist.set_clip_path(patch)
    except AttributeError:
        for c in getattr(artist, "collections", []):
            c.set_clip_path(patch)

def hillshade(ax, geom, alpha=0.35, zorder=1):
    p = OUT_R / "Hillshade.tif"
    if not p.exists():
        return
    with rasterio.open(p) as src:
        out_img, out_tr = mask(src, [geom], crop=True, nodata=0)
        arr = out_img[0]
        ext = (out_tr[2], out_tr[2] + out_tr[0] * arr.shape[1],
               out_tr[5] + out_tr[4] * arr.shape[0], out_tr[5])
    arr_m = np.ma.masked_equal(arr, 0)
    im = ax.imshow(arr_m, extent=ext, cmap="gray", vmin=1, vmax=255, zorder=zorder, alpha=alpha, interpolation="bilinear")
    clip_to_geom(im, ax, geom)

def overlay_lgas(ax):
    LGAS_GDF.boundary.plot(ax=ax, color="#1a1a1a", linewidth=0.75, linestyle="--", alpha=0.85, zorder=8)
    AOI_GDF.boundary.plot(ax=ax, color=RED, linewidth=1.5, zorder=9)
    offsets = {
        "ZURU": (0, 3200),
        "FAKAI": (0, 0),
        "SHANGA": (0, 0),
        "SAKABA": (0, 0),
        "YAURI": (0, -2800),
        "DANKO WASAGU": (0, 0),
        "NGASKI": (0, 0),
    }
    for _, r in LGAS_GDF.iterrows():
        name = str(r.get("ADM2_NAME", "")).strip().upper()
        c = r.geometry.centroid
        dx, dy = offsets.get(name, (0, 0))
        ax.plot(c.x + dx, c.y + dy, "o", color=DOT, markersize=3.8, mec="white", mew=0.6, zorder=11)
        ax.text(c.x + dx + 1800, c.y + dy + 1200, name, fontsize=8.0, fontweight="bold",
                color=INK, path_effects=HALO, zorder=12)

# ----------------- Strict 4-Sided Graticule Coordinate Ticks -----------------
def dms_ticks_4sides(ax):
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    cs = [TO_WGS.transform(x, y) for x in (x0, x1) for y in (y0, y1)]
    lons, lats = [c[0] for c in cs], [c[1] for c in cs]
    lo0, lo1, la0, la1 = min(lons), max(lons), min(lats), max(lats)
    span = max(lo1 - lo0, la1 - la0) * 60
    step = next((s for s in (5, 10, 15, 20, 30) if span / s <= 8), 15)

    xt, xl, yt, yl = [], [], [], []
    for m in range(int(np.ceil(lo0 * 60 / step)) * step, int(np.floor(lo1 * 60 / step)) * step + 1, step):
        x = TO_UTM.transform(m / 60, (la0 + la1) / 2)[0]
        if x0 <= x <= x1:
            xt.append(x)
            xl.append(f"{m // 60}°{m % 60:02d}′E")
    for m in range(int(np.ceil(la0 * 60 / step)) * step, int(np.floor(la1 * 60 / step)) * step + 1, step):
        y = TO_UTM.transform((lo0 + lo1) / 2, m / 60)[1]
        if y0 <= y <= y1:
            yt.append(y)
            yl.append(f"{m // 60}°{m % 60:02d}′N")

    ax.set_xticks(xt)
    ax.set_xticklabels(xl, fontsize=8.0, fontweight="bold", color=INK)
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=8.0, fontweight="bold", color=INK)

    # Enable tick marks AND coordinate labels on ALL 4 SIDES
    ax.tick_params(axis="x", direction="out", length=4, width=0.8, pad=3, colors=INK,
                   top=True, bottom=True, labeltop=True, labelbottom=True)
    ax.tick_params(axis="y", direction="out", length=4, width=0.8, pad=3, colors=INK,
                   left=True, right=True, labelleft=True, labelright=True)

    for t in ax.yaxis.get_major_ticks():
        t.label1.set_rotation(90)
        t.label1.set_va("center")
        t.label2.set_rotation(270)
        t.label2.set_va("center")

    ax.grid(True, linestyle=":", linewidth=0.55, color="#94a3b8", alpha=0.65, zorder=8)

# ----------------- Sheet Layout & Furniture -----------------
def new_sheet(title_main, subtitle=SUBTITLE):
    bounds = AOI_GDF.total_bounds
    bw, bh = bounds[2] - bounds[0], bounds[3] - bounds[1]
    pad_x, pad_y = bw * PAD_FRAC, bh * PAD_FRAC
    xlim = (bounds[0] - pad_x, bounds[2] + pad_x)
    ylim = (bounds[1] - pad_y, bounds[3] + pad_y)
    ar = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])

    if ar >= 1.0:
        map_w = MAP_MAX_W
        map_h = max(map_w / ar, 4.5)
    else:
        map_h = MAP_MAX_H
        map_w = max(map_h * ar, MAP_MIN_W)

    fw = map_w + M_LEFT + M_RIGHT
    fh = map_h + M_TOP + M_BOTTOM

    fig = plt.figure(figsize=(fw, fh), dpi=300, facecolor="white")
    ax = fig.add_axes([M_LEFT / fw, M_BOTTOM / fh, map_w / fw, map_h / fh])
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal", adjustable="box")

    fig.text(0.5, 1 - 0.45 / fh, title_main.upper(), fontsize=13.0, fontweight="bold", ha="center", va="center", color=INK)
    fig.text(0.5, 1 - 0.75 / fh, subtitle, fontsize=9.5, style="italic", ha="center", va="center", color=GREY)
    fig.text(M_LEFT / fw, 0.15 / fh, "Projection: UTM Zone 31N | Datum: WGS 84", fontsize=7.5, color=GREY, ha="left", va="center")

    return fig, ax, (xlim[0], xlim[1], ylim[0], ylim[1])

def draw_scalebar(ax, km=40):
    ax.patch.set_alpha(0.0)
    ax.patch.set_facecolor("none")
    ax.axis("off")
    sb_w = km * 1000.0
    sb_h = 2400.0
    ox, oy = 0.10, 0.50
    # Draw scale bar line
    ax.plot([ox, ox + 0.80], [oy, oy], color="#111", lw=1.6)
    for frac, lab in [(0.0, "0"), (0.40, f"{km//2}"), (0.80, f"{km} km")]:
        ax.plot([ox + frac, ox + frac], [oy - 0.08, oy + 0.08], color="#111", lw=1.4)
        ax.text(ox + frac, oy - 0.22, lab, ha="center", va="top", fontsize=8.0, fontfamily="Times New Roman", fontweight="bold")
    # North arrow
    nx, ny = ox + 0.90, oy
    ax.annotate("N", xy=(nx, ny + 0.35), xytext=(nx, ny - 0.20),
                arrowprops=dict(facecolor="black", width=1.8, headwidth=6.0),
                ha="center", va="bottom", fontsize=9.5, fontweight="bold")

def draw_legend(ax, title, entries):
    ax.patch.set_alpha(0.0)
    ax.patch.set_facecolor("none")
    ax.axis("off")
    ax.text(0.02, 0.94, title, fontsize=9.0, fontweight="bold", fontfamily="Times New Roman", color=INK, va="top")
    y = 0.82
    for kind, val, lbl in entries:
        if kind == "patch":
            ax.add_patch(mpatches.Rectangle((0.02, y - 0.035), 0.09, 0.065, facecolor=val, edgecolor="#333", lw=0.6))
        elif kind == "line":
            ax.plot([0.02, 0.11], [y, y], color=val, lw=1.8, linestyle="--" if "LGA" in lbl else "-")
        ax.text(0.14, y, lbl, fontsize=7.8, va="center", fontfamily="Times New Roman", color=INK)
        y -= 0.115

def place_elements(fig, ax, ext, geom):
    # Place furniture in lower right void
    leg_ax = ax.inset_axes([0.62, 0.06, 0.36, 0.25])
    scale_ax = ax.inset_axes([0.62, 0.01, 0.36, 0.05])
    return leg_ax, scale_ax

# ==============================================================================
# 1. TOPOGRAPHIC ATLAS & ELEVATION MAP
# ==============================================================================
def render_dem_map():
    print("  [MAPS] Rendering 00_StudyArea.png (SRTM 30m Topography)...")
    fig, ax, ext = new_sheet("TOPOGRAPHIC RELIEF & ADMINISTRATIVE OROGRAPHY")
    with rasterio.open(DATA_DIR / "Kebbi_SRTM.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=-9999)
        dem = out_img[0].astype(np.float32)
        dem_ext = (out_tr[2], out_tr[2] + out_tr[0] * dem.shape[1],
                   out_tr[5] + out_tr[4] * dem.shape[0], out_tr[5])
    dem_m = np.ma.masked_equal(dem, -9999)
    hillshade(ax, AOI_UNION, alpha=0.45)
    im = ax.imshow(dem_m, extent=dem_ext, cmap="terrain", vmin=110, vmax=650, alpha=0.75, zorder=2, interpolation="bilinear")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#386641", "Lowland Alluvial Plains (110–200 m)"),
        ("patch", "#a7c957", "Savanna Tablelands (200–350 m)"),
        ("patch", "#e07a5f", "Crystalline Escarpments (350–500 m)"),
        ("patch", "#7f4f24", "Precambrian Inselbergs (> 500 m)"),
    ]
    draw_legend(leg_ax, "Elevation (m a.s.l.)", entries)
    draw_scalebar(scale_ax, km=40)
    fig.text(0.95, 0.15 / (ax.get_position().height * fig.get_figheight() + M_TOP + M_BOTTOM),
             "NASA SRTM 30m Digital Elevation Model", fontsize=7.5, color=GREY, ha="right", va="center")

    out_file = MAPS_DIR / "00_StudyArea.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 2 & 3. CLASSIFIED LAND USE / LAND COVER MAPS (2000 & 2026)
# ==============================================================================
def render_lulc_map(year):
    print(f"  [MAPS] Rendering LULC_{year}.png...")
    title = f"LAND USE AND LAND COVER (LULC) — {year}"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.35)

    with rasterio.open(OUT_R / f"LULC_{year}.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=0)
        arr = out_img[0]
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * arr.shape[1],
                 out_tr[5] + out_tr[4] * arr.shape[0], out_tr[5])

    rgba = np.zeros((*arr.shape, 4), dtype=np.float32)
    for c, (lbl, col) in LULC_LUT.items():
        m = (arr == c)
        rgba[m] = mcolors.to_rgba(col)

    im = ax.imshow(rgba, extent=ext_r, zorder=2, interpolation="nearest")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [("line", RED, "Southern Kebbi Boundary"), ("line", "#1a1a1a", "LGA Boundaries")]
    for c in range(1, 7):
        entries.append(("patch", LULC_LUT[c][1], LULC_LUT[c][0]))

    draw_legend(leg_ax, "Land Cover Classes", entries)
    draw_scalebar(scale_ax, km=40)

    sensor = "Landsat 5 TM (30m)" if year == 2000 else "Landsat 8/9 OLI (30m) & ESRI 2025"
    fig.text(0.95, 0.15 / (ax.get_position().height * fig.get_figheight() + M_TOP + M_BOTTOM),
             f"USGS / NASA {sensor}", fontsize=7.5, color=GREY, ha="right", va="center")

    out_file = MAPS_DIR / f"LULC_{year}.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 4 & 5. TRUE COLOUR COMPOSITES (TCC) — NO THEMATIC LEGEND
# ==============================================================================
def render_tcc_map(year):
    print(f"  [MAPS] Rendering TCC_{year}.png (True Colour Composite - NO LEGEND)...")
    title = f"LANDSAT TRUE COLOUR COMPOSITE (RGB: {'3, 2, 1' if year == 2000 else '4, 3, 2'}) — {year}"
    fig, ax, ext = new_sheet(title)

    landsat_path = DATA_DIR / f"Kebbi_Landsat_{year}.tif"
    with rasterio.open(landsat_path) as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=np.nan)
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * out_img.shape[2],
                 out_tr[5] + out_tr[4] * out_img.shape[1], out_tr[5])

    # Landsat 5 TM: B3(Red), B2(Green), B1(Blue)
    # Landsat 8/9: B4(Red), B3(Green), B2(Blue)
    if year == 2000:
        rgb = np.stack([out_img[2], out_img[1], out_img[0]], axis=-1).astype(np.float32)
    else:
        rgb = np.stack([out_img[2], out_img[1], out_img[0]], axis=-1).astype(np.float32)

    # Robust 2.5% - 97.5% percentile stretch
    stretched = np.zeros_like(rgb)
    for b in range(3):
        band = rgb[:, :, b]
        valid_b = np.isfinite(band) & (band > 0)
        if valid_b.sum() > 0:
            p2 = np.percentile(band[valid_b], 2.5)
            p98 = np.percentile(band[valid_b], 97.5)
            stretched[:, :, b] = np.clip((band - p2) / (p98 - p2 + 1e-6), 0.0, 1.0) ** 0.90

    # Mask outside AOI
    with rasterio.open(DATA_DIR / f"Kebbi_Landsat_{year}.tif") as src:
        aoi_mask = rasterio.features.geometry_mask([AOI_UNION], transform=out_tr,
                                                   out_shape=(out_img.shape[1], out_img.shape[2]), invert=True)
    stretched[~aoi_mask] = 1.0  # White background outside AOI

    im = ax.imshow(stretched, extent=ext_r, zorder=2, interpolation="bilinear")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    # STRICT DIRECTIVE: NO THEMATIC LEGEND FOR TCC
    # Only place scalebar and north arrow in lower-right void
    scale_ax = ax.inset_axes([0.65, 0.03, 0.32, 0.06])
    draw_scalebar(scale_ax, km=40)

    # Attribution text in lower right corner
    sensor_txt = "Landsat 5 TM (Bands 3, 2, 1)" if year == 2000 else "Landsat 8/9 OLI (Bands 4, 3, 2)"
    ax.text(0.96, 0.12, f"Natural Color Photographic Composite\n{sensor_txt}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.0,
            fontfamily="Times New Roman", style="italic", color="#222",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.85, edgecolor="#ccc"))

    fig.text(0.95, 0.15 / (ax.get_position().height * fig.get_figheight() + M_TOP + M_BOTTOM),
             "USGS / NASA Earth Observation System", fontsize=7.5, color=GREY, ha="right", va="center")

    out_file = MAPS_DIR / f"TCC_{year}.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 6 & 7. NDVI VEGETATION HEALTH MAPS (2000 & 2026)
# ==============================================================================
def render_ndvi_map(year):
    print(f"  [MAPS] Rendering NDVI_{year}.png...")
    title = f"SEASONAL VEGETATION HEALTH & GREENNESS (NDVI) — {year}"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.40)

    with rasterio.open(OUT_R / f"NDVI_{year}.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=np.nan)
        arr = out_img[0]
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * arr.shape[1],
                 out_tr[5] + out_tr[4] * arr.shape[0], out_tr[5])

    valid = np.isfinite(arr)
    rgba = np.zeros((*arr.shape, 4), dtype=np.float32)
    ndvi_bins = [
        (-1.0,  0.12, "#d7191c", 0.75),
        ( 0.12, 0.18, "#fdae61", 0.75),
        ( 0.18, 0.25, "#ffffbf", 0.75),
        ( 0.25, 0.35, "#a6d96a", 0.80),
        ( 0.35, 1.00, "#1a9641", 0.85),
    ]
    for lo, hi, col, a in ndvi_bins:
        m = valid & (arr >= lo) & (arr < hi)
        rgba[m] = mcolors.to_rgba(col, a)

    im = ax.imshow(rgba, extent=ext_r, zorder=2, interpolation="nearest")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#1a9641", "> 0.35  Dense / Vigorous Canopy"),
        ("patch", "#a6d96a", "0.25–0.35  Moderate Green Vegetation"),
        ("patch", "#ffffbf", "0.18–0.25  Sparse / Cultivated Crop"),
        ("patch", "#fdae61", "0.12–0.18  Dry Savanna Grassland"),
        ("patch", "#d7191c", "< 0.12  Bare Soil / Waterbody"),
    ]
    draw_legend(leg_ax, "NDVI Vegetation Density", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / f"NDVI_{year}.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 8. BI-TEMPORAL CANOPY DYNAMICS / NDVI CHANGE MAP
# ==============================================================================
def render_ndvi_change_map():
    print("  [MAPS] Rendering NDVI_Change_2000_2026.png...")
    title = "CANOPY DEGRADATION & NDVI DYNAMICS MAP (2000–2026)"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.40)

    with rasterio.open(OUT_R / "NDVI_drop_2000_2026.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=np.nan)
        arr = out_img[0]
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * arr.shape[1],
                 out_tr[5] + out_tr[4] * arr.shape[0], out_tr[5])

    valid = np.isfinite(arr)
    rgba = np.zeros((*arr.shape, 4), dtype=np.float32)
    change_bins = [
        (-2.0, -0.15, "#1a9641", 0.85), # Substantial greening
        (-0.15, -0.05, "#a6d96a", 0.75), # Moderate greening
        (-0.05,  0.05, "#ffffbf", 0.50), # Stable canopy
        ( 0.05,  0.15, "#fdae61", 0.75), # Moderate canopy loss
        ( 0.15,  2.00, "#d7191c", 0.85), # Severe canopy loss
    ]
    for lo, hi, col, a in change_bins:
        m = valid & (arr >= lo) & (arr < hi)
        rgba[m] = mcolors.to_rgba(col, a)

    im = ax.imshow(rgba, extent=ext_r, zorder=2, interpolation="nearest")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#d7191c", "> +0.15  Severe Canopy Loss"),
        ("patch", "#fdae61", "+0.05–0.15  Moderate Canopy Loss"),
        ("patch", "#ffffbf", "-0.05–0.05  Stable Canopy"),
        ("patch", "#a6d96a", "-0.15– -0.05  Moderate Greening"),
        ("patch", "#1a9641", "< -0.15  Substantial Greening"),
    ]
    draw_legend(leg_ax, "Canopy Dynamics (ΔNDVI)", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / "NDVI_Change_2000_2026.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 9. CATEGORICAL TRANSITION ARCHITECTURE OVERVIEW
# ==============================================================================
def render_transition_overview():
    print("  [MAPS] Rendering Transition_overview.png...")
    title = "LANDSCAPE TRANSITION & DEGRADATION OVERVIEW (2000–2026)"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.40)

    with rasterio.open(OUT_R / "Transition_code.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=0)
        arr = out_img[0]
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * arr.shape[1],
                 out_tr[5] + out_tr[4] * arr.shape[0], out_tr[5])

    rgba = np.zeros((*arr.shape, 4), dtype=np.float32)
    # Background persistent/stable: transparent light grey
    stable = (arr % 11 == 0) & (arr > 0)
    rgba[stable] = mcolors.to_rgba("#e9ecef", 0.35)

    trans_colors = [
        (12, "#ffb703", 0.85), # Forest -> Ag
        (13, "#70e000", 0.80), # Forest -> Grass
        (14, "#d90429", 0.85), # Forest -> Bare
        (32, "#f4a261", 0.70), # Grassland -> Ag
    ]
    for code, col, a in trans_colors:
        rgba[arr == code] = mcolors.to_rgba(col, a)

    im = ax.imshow(rgba, extent=ext_r, zorder=2, interpolation="nearest")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#ffb703", "Forest \u2192 Agriculture (124,497 ha)"),
        ("patch", "#70e000", "Forest \u2192 Grassland (34,628 ha)"),
        ("patch", "#d90429", "Forest \u2192 Bare / Degraded (14,495 ha)"),
        ("patch", "#f4a261", "Savanna \u2192 Agriculture Expansion"),
        ("patch", "#e9ecef", "Persistent Stable Land Cover"),
    ]
    draw_legend(leg_ax, "Dominant Transitions", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / "Transition_overview.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 10, 11, 12. INDIVIDUAL FOOTPRINT MAPS
# ==============================================================================
def render_footprint_map(traj_name, title_desc, col_raw, col_hi):
    print(f"  [MAPS] Rendering Footprint_{traj_name}.png...")
    title = f"SPATIAL FOOTPRINT: {title_desc.upper()}"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.45)

    with rasterio.open(OUT_R / f"{traj_name}.tif") as src:
        out_img, out_tr = mask(src, [AOI_UNION], crop=True, nodata=0)
        arr_raw = out_img[0]
        ext_r = (out_tr[2], out_tr[2] + out_tr[0] * arr_raw.shape[1],
                 out_tr[5] + out_tr[4] * arr_raw.shape[0], out_tr[5])

    with rasterio.open(OUT_R / f"{traj_name}_HiConf.tif") as src:
        out_img_hi, _ = mask(src, [AOI_UNION], crop=True, nodata=0)
        arr_hi = out_img_hi[0]

    rgba = np.zeros((*arr_raw.shape, 4), dtype=np.float32)
    rgba[arr_raw == 1] = mcolors.to_rgba(col_raw, 0.70)
    rgba[arr_hi == 1]  = mcolors.to_rgba(col_hi, 0.90)

    im = ax.imshow(rgba, extent=ext_r, zorder=2, interpolation="nearest")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", col_hi, "Confirmed High-Confidence Core"),
        ("patch", col_raw, "Broad Mapped Conversion Zone"),
    ]
    draw_legend(leg_ax, "Conversion Intensity", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / f"Footprint_{traj_name}.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 13. SPATIAL KERNEL DENSITY DEFORESTATION HOTSPOTS (50m KDE)
# ==============================================================================
def render_hotspot():
    print("  [MAPS] Rendering Hotspot_Forest_Loss_KDE.png...")
    title = "CANOPY DEGRADATION HOTSPOTS & SPATIAL CLUSTERING (50m KDE)"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.35)

    with rasterio.open(OUT_R / "Forest_to_Agriculture_HiConf.tif") as src_ag, \
         rasterio.open(OUT_R / "Forest_to_Grassland_HiConf.tif") as src_gr, \
         rasterio.open(OUT_R / "Forest_to_Bare_HiConf.tif") as src_br:
        loss_comb = (src_ag.read(1) == 1) | (src_gr.read(1) == 1) | (src_br.read(1) == 1)
        bounds = src_ag.bounds

    # Gaussian kernel density filter
    kde = ndi.gaussian_filter(loss_comb.astype(np.float32), sigma=18.0)
    max_k = kde.max()
    kde_norm = kde / (max_k + 1e-6) if max_k > 0 else kde

    # Thermal magma / inferno palette
    colors = ["#ffffff00", "#ffcc00cc", "#ff6600ee", "#cc0000ff", "#660033ff"]
    cmap_hot = LinearSegmentedColormap.from_list("hotspots", colors)

    im = ax.imshow(kde_norm, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top],
                   cmap=cmap_hot, vmin=0.10, vmax=1.0, zorder=3, interpolation="bilinear")
    clip_to_geom(im, ax, AOI_UNION)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#660033", "Extreme Threat Hotspot (Danko/Sakaba)"),
        ("patch", "#cc0000", "High Canopy Degradation"),
        ("patch", "#ff6600", "Moderate Forest Conversion"),
        ("patch", "#ffcc00", "Dispersed Agricultural Frontier"),
    ]
    draw_legend(leg_ax, "Degradation Intensity (KDE)", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / "Hotspot_Forest_Loss_KDE.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# 14. VECTOR TRAJECTORIES MAP (MMU >= 0.45 ha)
# ==============================================================================
def render_vector_trajectories():
    print("  [MAPS] Rendering Forest_Loss_Trajectories_Vector.png...")
    title = "SPATIAL FOOTPRINTS OF FOREST LOSS TRAJECTORIES (2000–2026)"
    fig, ax, ext = new_sheet(title)
    hillshade(ax, AOI_UNION, alpha=0.40, zorder=2)

    shp_ag = OUT_V / "Forest_to_Agriculture.shp"
    shp_gr = OUT_V / "Forest_to_Grassland.shp"
    shp_br = OUT_V / "Forest_to_Bare.shp"

    if shp_gr.exists():
        gpd.read_file(shp_gr).plot(ax=ax, color="#70e000", edgecolor="none", alpha=0.75, zorder=4)
    if shp_ag.exists():
        gpd.read_file(shp_ag).plot(ax=ax, color="#ffb703", edgecolor="none", alpha=0.75, zorder=5)
    if shp_br.exists():
        gpd.read_file(shp_br).plot(ax=ax, color="#d90429", edgecolor="none", alpha=0.85, zorder=6)

    overlay_lgas(ax)
    dms_ticks_4sides(ax)

    leg_ax, scale_ax = place_elements(fig, ax, ext, AOI_UNION)
    entries = [
        ("line", RED, "Southern Kebbi Boundary"),
        ("line", "#1a1a1a", "LGA Boundaries"),
        ("patch", "#ffb703", "Forest \u2192 Agriculture (124,497 ha)"),
        ("patch", "#70e000", "Forest \u2192 Grassland (34,628 ha)"),
        ("patch", "#d90429", "Forest \u2192 Bare / Degraded (14,495 ha)"),
    ]
    draw_legend(leg_ax, "Conversion Trajectories", entries)
    draw_scalebar(scale_ax, km=40)

    out_file = MAPS_DIR / "Forest_Loss_Trajectories_Vector.png"
    fig.savefig(out_file, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"  [OK] Saved: {out_file.name}")

# ==============================================================================
# MASTER RUNNER
# ==============================================================================
def main():
    print("=" * 70)
    print("STEP 8A: 300 DPI CARTOGRAPHIC PRODUCTION (LOHARA TALUKA ATLAS STANDARD)")
    print("=" * 70)
    print(f"Output Directory (Maps Only): {MAPS_DIR}")

    render_dem_map()
    render_lulc_map(2000)
    render_lulc_map(2026)
    render_tcc_map(2000)
    render_tcc_map(2026)
    render_ndvi_map(2000)
    render_ndvi_map(2026)
    render_ndvi_change_map()
    render_transition_overview()
    render_footprint_map("Forest_to_Agriculture", "Forest to Agriculture Conversion", "#FF9F1C", "#C0392B")
    render_footprint_map("Forest_to_Grassland", "Forest to Grassland Degradation", "#70E000", "#007200")
    render_footprint_map("Forest_to_Bare", "Forest to Bare / Degraded Land", "#E63946", "#800F2F")
    render_hotspot()
    render_vector_trajectories()

    print("\n[OK] All 14 Cartographic Plates generated successfully with 4-sided coordinates and NO TCC legends.")

if __name__ == "__main__":
    main()

