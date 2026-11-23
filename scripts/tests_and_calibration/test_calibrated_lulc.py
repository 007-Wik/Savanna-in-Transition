"""Test scientifically calibrated pseudo-labels and classification for Southern Kebbi."""
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

with rasterio.open(DATA / "Kebbi_Hansen.tif") as src:
    tc2000 = src.read(1)
    loss = src.read(2)
    h, w = src.height, src.width
    trans = src.transform

with rasterio.open(DATA / "Kebbi_WorldCover_2021.tif") as src:
    wc = src.read(1)

with rasterio.open(OUT / "FeatureStack_2000.tif") as src:
    fstack_0 = src.read()
with rasterio.open(OUT / "FeatureStack_2026.tif") as src:
    fstack_1 = src.read()

mask = geometry_mask(aoi_gdf.geometry, out_shape=(h, w), transform=trans, invert=True)
val0 = mask & np.isfinite(fstack_0[6]) & np.isfinite(fstack_0[10])
val1 = mask & np.isfinite(fstack_1[6]) & np.isfinite(fstack_1[10])

ndvi0, ndwi0, bsi0 = fstack_0[6], fstack_0[8], fstack_0[10]
ndvi1, ndwi1, bsi1 = fstack_1[6], fstack_1[8], fstack_1[10]

# --- 2000 SEEDS ---
# Water
s_wat_0 = val0 & ((ndwi0 > 0.05) | ((wc == 80) & (ndwi0 > -0.02)))
# Settlement
s_set_0 = val0 & ~s_wat_0 & ((wc == 50) & (ndvi0 < 0.16) & (bsi0 > 0.16))
# Forest / Woodland (high canopy, high ndvi, lowest bsi)
s_for_0 = val0 & ~s_wat_0 & ~s_set_0 & (
    ((tc2000 >= 10) & (ndvi0 >= 0.23) & (bsi0 < 0.14)) |
    ((wc == 10) & (ndvi0 >= 0.24) & (bsi0 < 0.14))
)
# Bare / Degraded (highest BSI, lowest NDVI)
s_bar_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & (
    ((wc == 60) & (bsi0 > 0.19)) |
    ((ndvi0 < 0.12) & (bsi0 > 0.21) & (tc2000 < 3))
)
# Cropland (farmland, moderate NDVI, moderate BSI)
s_crp_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & ~s_bar_0 & (
    (wc == 40) & (loss == 0) & (ndvi0 >= 0.16) & (ndvi0 <= 0.24) & (bsi0 >= 0.15) & (bsi0 <= 0.19)
)
# Grassland / Savanna
s_grs_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & ~s_bar_0 & ~s_crp_0 & (
    ((wc == 30) & (ndvi0 >= 0.12) & (ndvi0 <= 0.18) & (bsi0 >= 0.13) & (bsi0 <= 0.18)) |
    ((tc2000 < 5) & (ndvi0 >= 0.11) & (ndvi0 < 0.16) & (bsi0 < 0.17))
)

# --- 2026 SEEDS ---
s_wat_1 = val1 & ((ndwi1 > 0.05) | ((wc == 80) & (ndwi1 > -0.02)))
s_set_1 = val1 & ~s_wat_1 & ((wc == 50) & (ndvi1 < 0.22) & (bsi1 > 0.16))
# Forest in 2026: MUST have loss == 0
s_for_1 = val1 & ~s_wat_1 & ~s_set_1 & (loss == 0) & (
    ((tc2000 >= 10) & (ndvi1 >= 0.30) & (bsi1 < 0.14)) |
    ((wc == 10) & (ndvi1 >= 0.32) & (bsi1 < 0.14))
)
s_bar_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & (
    (wc == 60) |
    ((ndvi1 < 0.16) & (bsi1 > 0.21)) |
    ((loss > 0) & (bsi1 > 0.20) & (ndvi1 < 0.20))
)
s_crp_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & ~s_bar_1 & (
    ((wc == 40) & (ndvi1 >= 0.22) & (ndvi1 <= 0.32) & (bsi1 >= 0.15) & (bsi1 <= 0.19)) |
    ((loss > 0) & (ndvi1 >= 0.20) & (ndvi1 <= 0.30) & (bsi1 >= 0.16))
)
s_grs_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & ~s_bar_1 & ~s_crp_1 & (
    ((wc == 30) & (ndvi1 >= 0.16) & (ndvi1 <= 0.23) & (bsi1 >= 0.14) & (bsi1 <= 0.18)) |
    ((loss > 0) & (ndvi1 >= 0.14) & (ndvi1 < 0.22) & (bsi1 < 0.18))
)

print("2000 Seed counts:", [m.sum() for m in [s_for_0, s_crp_0, s_grs_0, s_bar_0, s_wat_0, s_set_0]])
print("2026 Seed counts:", [m.sum() for m in [s_for_1, s_crp_1, s_grs_1, s_bar_1, s_wat_1, s_set_1]])

rng = np.random.RandomState(42)
N_SAMPLE = 3000

def get_train_data(seeds, fstack):
    X_list, y_list = [], []
    X_flat = fstack.reshape(16, -1).T
    for c_idx, s in enumerate(seeds, 1):
        idx = np.where(s.ravel())[0]
        chosen = rng.choice(idx, size=min(len(idx), N_SAMPLE), replace=(len(idx) < N_SAMPLE))
        X_list.append(X_flat[chosen])
        y_list.append(np.full(len(chosen), c_idx, dtype=np.uint8))
    return np.vstack(X_list), np.concatenate(y_list)

X_tr_0, y_tr_0 = get_train_data([s_for_0, s_crp_0, s_grs_0, s_bar_0, s_wat_0, s_set_0], fstack_0)
X_tr_1, y_tr_1 = get_train_data([s_for_1, s_crp_1, s_grs_1, s_bar_1, s_wat_1, s_set_1], fstack_1)

rf_0 = RandomForestClassifier(n_estimators=100, max_depth=18, min_samples_leaf=3, n_jobs=-1, random_state=42)
rf_0.fit(X_tr_0, y_tr_0)

rf_1 = RandomForestClassifier(n_estimators=100, max_depth=18, min_samples_leaf=3, n_jobs=-1, random_state=42)
rf_1.fit(X_tr_1, y_tr_1)

val_idx_0 = np.where(val0.ravel())[0]
val_idx_1 = np.where(val1.ravel())[0]

pred_0 = np.zeros(h * w, dtype=np.uint8)
for chunk in np.array_split(val_idx_0, 10):
    pred_0[chunk] = rf_0.predict(fstack_0.reshape(16, -1).T[chunk])

pred_1 = np.zeros(h * w, dtype=np.uint8)
for chunk in np.array_split(val_idx_1, 10):
    pred_1[chunk] = rf_1.predict(fstack_1.reshape(16, -1).T[chunk])

print("\n--- RESULTS ---")
names = ["Woodland/Forest", "Cropland", "Grassland", "Bare/Degraded", "Waterbody", "Settlement"]
print(f"{'Class':<18} | {'2000 ha':>12} {'2000 %':>8} | {'2026 ha':>12} {'2026 %':>8} | {'Change ha':>12}")
print("-" * 75)
for c in range(1, 7):
    cnt0 = (pred_0[val_idx_0] == c).sum()
    cnt1 = (pred_1[val_idx_1] == c).sum()
    ha0 = cnt0 * 0.09
    ha1 = cnt1 * 0.09
    pct0 = cnt0 / len(val_idx_0) * 100
    pct1 = cnt1 / len(val_idx_1) * 100
    diff = ha1 - ha0
    print(f"{names[c-1]:<18} | {ha0:>12,.1f} {pct0:7.2f}% | {ha1:>12,.1f} {pct1:7.2f}% | {diff:>+12,.1f}")

