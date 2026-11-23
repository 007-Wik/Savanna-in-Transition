"""Calibrate 6-Class Pseudo-Labels and Classification for 2000 and 2026.
Ensuring:
- Woodland/Forest decreases over time due to deforestation
- Cropland and Bare Land expand
- Settlements expand
- Water remains stable
"""
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # repository root

DATA = ROOT / "data"
OUT = ROOT / "outputs" / "rasters"
OUT_V = ROOT / "outputs" / "vectors"

aoi_gdf = gpd.read_file(OUT_V / "AOI.shp")

# Load Hansen
with rasterio.open(DATA / "Kebbi_Hansen.tif") as src:
    tc2000 = src.read(1)
    loss = src.read(2)
    lossyear = src.read(3)
    h, w = src.height, src.width
    trans = src.transform

# Load WorldCover
with rasterio.open(DATA / "Kebbi_WorldCover_2021.tif") as src:
    wc = src.read(1)

# Load Features 2000
with rasterio.open(OUT / "FeatureStack_2000.tif") as src:
    b_blue_0 = src.read(1)
    b_green_0 = src.read(2)
    b_red_0 = src.read(3)
    b_nir_0 = src.read(4)
    b_swir1_0 = src.read(5)
    b_swir2_0 = src.read(6)
    ndvi_0 = src.read(7)
    nbr_0 = src.read(8)
    ndwi_0 = src.read(9)
    savi_0 = src.read(10)
    bsi_0 = src.read(11)
    elev = src.read(15)
    slope = src.read(16)

# Load Features 2026
with rasterio.open(OUT / "FeatureStack_2026.tif") as src:
    b_blue_1 = src.read(1)
    b_green_1 = src.read(2)
    b_red_1 = src.read(3)
    b_nir_1 = src.read(4)
    b_swir1_1 = src.read(5)
    b_swir2_1 = src.read(6)
    ndvi_1 = src.read(7)
    nbr_1 = src.read(8)
    ndwi_1 = src.read(9)
    savi_1 = src.read(10)
    bsi_1 = src.read(11)

mask = geometry_mask(aoi_gdf.geometry, out_shape=(h, w), transform=trans, invert=True)
val0 = mask & np.isfinite(ndvi_0) & np.isfinite(bsi_0)
val1 = mask & np.isfinite(ndvi_1) & np.isfinite(bsi_1)

print(f"Total valid AOI pixels: {val0.sum():,}")

# 1. Define 2000 Training Samples
# In 2000, Southern Kebbi had extensive wooded savanna & dense woodland
# Forest/Woodland: tc2000 >= 8 or (wc in [10, 20] & loss == 0 & ndvi_0 >= 0.20)
f_0 = val0 & (
    ((tc2000 >= 8) & (ndvi_0 >= 0.20) & (bsi_0 < 0.02)) |
    ((wc == 10) & (ndvi_0 >= 0.22) & (bsi_0 < 0.0)) |
    ((wc == 20) & (loss == 0) & (tc2000 >= 5) & (ndvi_0 >= 0.22) & (bsi_0 < 0.0))
)

# Water
wat_0 = val0 & ~f_0 & (
    (ndwi_0 > 0.05) | ((wc == 80) & (ndwi_0 > -0.02))
)

# Settlement (Built)
built_0 = val0 & ~f_0 & ~wat_0 & (
    (wc == 50) & (bsi_0 > 0.04) & (ndvi_0 < 0.16)
)

# Bare / Degraded (low ndvi, high bsi, rock/bare)
bare_0 = val0 & ~f_0 & ~wat_0 & ~built_0 & (
    ((wc == 60) & (bsi_0 > 0.04)) |
    ((ndvi_0 < 0.10) & (bsi_0 > 0.08) & (tc2000 < 3))
)

# Cropland (Agriculture)
crop_0 = val0 & ~f_0 & ~wat_0 & ~built_0 & ~bare_0 & (
    (wc == 40) & (loss == 0) & (ndvi_0 >= 0.14) & (ndvi_0 <= 0.32) & (bsi_0 > -0.04) & (bsi_0 < 0.08)
)

# Grassland / Savanna
grass_0 = val0 & ~f_0 & ~wat_0 & ~built_0 & ~bare_0 & ~crop_0 & (
    ((wc == 30) & (ndvi_0 >= 0.08) & (ndvi_0 <= 0.22)) |
    ((tc2000 < 5) & (ndvi_0 >= 0.08) & (ndvi_0 < 0.16) & (bsi_0 <= 0.04))
)

print("\n--- 2000 Candidate Samples ---")
print(f"  Forest:     {f_0.sum():>10,}")
print(f"  Cropland:   {crop_0.sum():>10,}")
print(f"  Grassland:  {grass_0.sum():>10,}")
print(f"  Bare:       {bare_0.sum():>10,}")
print(f"  Water:      {wat_0.sum():>10,}")
print(f"  Settlement: {built_0.sum():>10,}")

# 2. Define 2026 Training Samples
# In 2026, Forest has decreased. Any loss > 0 CANNOT be forest!
f_1 = val1 & (loss == 0) & (
    ((wc == 10) & (ndvi_1 >= 0.26) & (bsi_1 < 0.0)) |
    ((wc == 20) & (tc2000 >= 8) & (ndvi_1 >= 0.28) & (nbr_1 >= 0.12) & (bsi_1 < 0.0))
)

wat_1 = val1 & ~f_1 & (
    (ndwi_1 > 0.05) | ((wc == 80) & (ndwi_1 > -0.02))
)

built_1 = val1 & ~f_1 & ~wat_1 & (
    (wc == 50) & (ndvi_1 < 0.22) & (bsi_1 > 0.02)
)

# Bare land in 2026: high BSI, low NDVI, or loss > 0 with high BSI
bare_1 = val1 & ~f_1 & ~wat_1 & ~built_1 & (
    (wc == 60) |
    ((ndvi_1 < 0.12) & (bsi_1 > 0.08)) |
    ((loss > 0) & (bsi_1 > 0.08) & (ndvi_1 < 0.16))
)

crop_1 = val1 & ~f_1 & ~wat_1 & ~built_1 & ~bare_1 & (
    ((wc == 40) & (ndvi_1 >= 0.14) & (ndvi_1 <= 0.38)) |
    ((loss > 0) & (ndvi_1 >= 0.16) & (ndvi_1 <= 0.32) & (bsi_1 >= -0.02))
)

grass_1 = val1 & ~f_1 & ~wat_1 & ~built_1 & ~bare_1 & ~crop_1 & (
    ((wc == 30) & (ndvi_1 >= 0.10) & (ndvi_1 <= 0.25)) |
    ((loss > 0) & (ndvi_1 >= 0.10) & (ndvi_1 < 0.18) & (bsi_1 < 0.05))
)

print("\n--- 2026 Candidate Samples ---")
print(f"  Forest:     {f_1.sum():>10,}")
print(f"  Cropland:   {crop_1.sum():>10,}")
print(f"  Grassland:  {grass_1.sum():>10,}")
print(f"  Bare:       {bare_1.sum():>10,}")
print(f"  Water:      {wat_1.sum():>10,}")
print(f"  Settlement: {built_1.sum():>10,}")

