"""Test balanced Random Forest classification on 2000 and 2026."""
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # repository root

DATA = ROOT / "data"
OUT = ROOT / "outputs" / "rasters"
OUT_V = ROOT / "outputs" / "vectors"

aoi_gdf = gpd.read_file(OUT_V / "AOI.shp")

# 1. Load Data
with rasterio.open(DATA / "Kebbi_Hansen.tif") as src:
    tc2000 = src.read(1)
    loss = src.read(2)
    h, w = src.height, src.width
    trans = src.transform

with rasterio.open(DATA / "Kebbi_WorldCover_2021.tif") as src:
    wc = src.read(1)

with rasterio.open(OUT / "FeatureStack_2000.tif") as src:
    fstack_0 = src.read()  # (16, H, W)
with rasterio.open(OUT / "FeatureStack_2026.tif") as src:
    fstack_1 = src.read()  # (16, H, W)

mask = geometry_mask(aoi_gdf.geometry, out_shape=(h, w), transform=trans, invert=True)
val0 = mask & np.isfinite(fstack_0[6]) & np.isfinite(fstack_0[10])
val1 = mask & np.isfinite(fstack_1[6]) & np.isfinite(fstack_1[10])

ndvi0, nbr0, ndwi0, savi0, bsi0 = fstack_0[6], fstack_0[7], fstack_0[8], fstack_0[9], fstack_0[10]
ndvi1, nbr1, ndwi1, savi1, bsi1 = fstack_1[6], fstack_1[7], fstack_1[8], fstack_1[9], fstack_1[10]

# High confidence seed masks for 2000:
# Class 1: Forest/Woodland (intact high canopy or dense riparian/wooded)
c1_0 = val0 & (
    ((tc2000 >= 12) & (ndvi0 >= 0.22) & (bsi0 < 0.0)) |
    ((wc == 10) & (ndvi0 >= 0.24) & (bsi0 < -0.02)) |
    ((wc == 20) & (loss == 0) & (tc2000 >= 8) & (ndvi0 >= 0.22) & (nbr0 >= 0.12))
)
# Class 5: Waterbody
c5_0 = val0 & ~c1_0 & ((ndwi0 > 0.08) | ((wc == 80) & (ndwi0 > 0.0)))
# Class 6: Settlement (built-up core)
c6_0 = val0 & ~c1_0 & ~c5_0 & ((wc == 50) & (bsi0 > 0.04) & (ndvi0 < 0.16))
# Class 4: Bare / Degraded (cleared, laterite, bare soil)
c4_0 = val0 & ~c1_0 & ~c5_0 & ~c6_0 & (
    ((wc == 60) & (bsi0 > 0.04)) |
    ((ndvi0 < 0.10) & (bsi0 > 0.08) & (tc2000 < 2))
)
# Class 2: Cropland (agricultural fields)
c2_0 = val0 & ~c1_0 & ~c5_0 & ~c6_0 & ~c4_0 & (
    ((wc == 40) & (loss == 0) & (ndvi0 >= 0.14) & (ndvi0 <= 0.30) & (bsi0 >= -0.06) & (bsi0 <= 0.06))
)
# Class 3: Grassland / Savanna (herbaceous rangeland)
c3_0 = val0 & ~c1_0 & ~c5_0 & ~c6_0 & ~c4_0 & ~c2_0 & (
    ((wc == 30) & (ndvi0 >= 0.08) & (ndvi0 <= 0.20)) |
    ((tc2000 < 5) & (ndvi0 >= 0.08) & (ndvi0 < 0.16) & (bsi0 < 0.04))
)

rng = np.random.RandomState(42)
N_SAMPLE = 4000

def sample_indices(mask, n):
    idx = np.where(mask.ravel())[0]
    if len(idx) < n:
        return rng.choice(idx, size=n, replace=True)
    return rng.choice(idx, size=n, replace=False)

idx1_0 = sample_indices(c1_0, N_SAMPLE)
idx2_0 = sample_indices(c2_0, N_SAMPLE)
idx3_0 = sample_indices(c3_0, N_SAMPLE)
idx4_0 = sample_indices(c4_0, N_SAMPLE)
idx5_0 = sample_indices(c5_0, N_SAMPLE)
idx6_0 = sample_indices(c6_0, N_SAMPLE)

train_idx_0 = np.concatenate([idx1_0, idx2_0, idx3_0, idx4_0, idx5_0, idx6_0])
train_y_0 = np.repeat([1, 2, 3, 4, 5, 6], N_SAMPLE)

# Feature matrix (16 features)
X_all_0 = fstack_0.reshape(16, -1).T  # (H*W, 16)
X_train_0 = X_all_0[train_idx_0]

print("Fitting Balanced RF for 2000...")
rf_0 = RandomForestClassifier(n_estimators=100, max_depth=20, n_jobs=-1, random_state=42)
rf_0.fit(X_train_0, train_y_0)

val_idx_0 = np.where(val0.ravel())[0]
pred_0 = np.zeros(h * w, dtype=np.uint8)
# Predict in chunks
for chunk in np.array_split(val_idx_0, 10):
    pred_0[chunk] = rf_0.predict(X_all_0[chunk])

print("\n2000 Class Breakdown:")
for c in range(1, 7):
    cnt = (pred_0[val_idx_0] == c).sum()
    pct = cnt / len(val_idx_0) * 100
    ha = cnt * 0.09
    print(f"  Class {c}: {cnt:>10,} ({pct:5.2f}%) = {ha:>10,.1f} ha")

# High confidence seed masks for 2026:
# Deforested loss pixels CANNOT be forest!
c1_1 = val1 & (loss == 0) & (
    ((tc2000 >= 12) & (ndvi1 >= 0.28) & (bsi1 < 0.0)) |
    ((wc == 10) & (ndvi1 >= 0.28) & (bsi1 < -0.02)) |
    ((wc == 20) & (tc2000 >= 8) & (ndvi1 >= 0.28) & (nbr1 >= 0.14) & (bsi1 < 0.0))
)
c5_1 = val1 & ~c1_1 & ((ndwi1 > 0.08) | ((wc == 80) & (ndwi1 > 0.0)))
c6_1 = val1 & ~c1_1 & ~c5_1 & ((wc == 50) & (ndvi1 < 0.22) & (bsi1 > 0.02))
c4_1 = val1 & ~c1_1 & ~c5_1 & ~c6_1 & (
    (wc == 60) |
    ((ndvi1 < 0.12) & (bsi1 > 0.08)) |
    ((loss > 0) & (bsi1 > 0.08) & (ndvi1 < 0.16))
)
c2_1 = val1 & ~c1_1 & ~c5_1 & ~c6_1 & ~c4_1 & (
    ((wc == 40) & (ndvi1 >= 0.16) & (ndvi1 <= 0.38)) |
    ((loss > 0) & (ndvi1 >= 0.16) & (ndvi1 <= 0.32) & (bsi1 >= -0.02))
)
c3_1 = val1 & ~c1_1 & ~c5_1 & ~c6_1 & ~c4_1 & ~c2_1 & (
    ((wc == 30) & (ndvi1 >= 0.10) & (ndvi1 <= 0.26)) |
    ((loss > 0) & (ndvi1 >= 0.10) & (ndvi1 < 0.18) & (bsi1 < 0.05))
)

idx1_1 = sample_indices(c1_1, N_SAMPLE)
idx2_1 = sample_indices(c2_1, N_SAMPLE)
idx3_1 = sample_indices(c3_1, N_SAMPLE)
idx4_1 = sample_indices(c4_1, N_SAMPLE)
idx5_1 = sample_indices(c5_1, N_SAMPLE)
idx6_1 = sample_indices(c6_1, N_SAMPLE)

train_idx_1 = np.concatenate([idx1_1, idx2_1, idx3_1, idx4_1, idx5_1, idx6_1])
train_y_1 = np.repeat([1, 2, 3, 4, 5, 6], N_SAMPLE)

X_all_1 = fstack_1.reshape(16, -1).T
X_train_1 = X_all_1[train_idx_1]

print("\nFitting Balanced RF for 2026...")
rf_1 = RandomForestClassifier(n_estimators=100, max_depth=20, n_jobs=-1, random_state=42)
rf_1.fit(X_train_1, train_y_1)

val_idx_1 = np.where(val1.ravel())[0]
pred_1 = np.zeros(h * w, dtype=np.uint8)
for chunk in np.array_split(val_idx_1, 10):
    pred_1[chunk] = rf_1.predict(X_all_1[chunk])

print("\n2026 Class Breakdown:")
for c in range(1, 7):
    cnt = (pred_1[val_idx_1] == c).sum()
    pct = cnt / len(val_idx_1) * 100
    ha = cnt * 0.09
    print(f"  Class {c}: {cnt:>10,} ({pct:5.2f}%) = {ha:>10,.1f} ha")

