"""Fine-tune 6-class seeds for realistic Savanna ecology in Southern Kebbi."""
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

ndvi0, ndwi0, bsi0, savi0 = fstack_0[6], fstack_0[8], fstack_0[10], fstack_0[9]
ndvi1, ndwi1, bsi1, savi1 = fstack_1[6], fstack_1[8], fstack_1[10], fstack_1[9]

# --- 2000 SEEDS ---
# Waterbody: Kainji Lake, Niger River
s_wat_0 = val0 & ((ndwi0 > 0.05) | ((wc == 80) & (ndwi0 > -0.02)))

# Settlement: Real built clusters from WC 50 with urban spectral response
s_set_0 = val0 & ~s_wat_0 & (wc == 50) & (ndvi0 < 0.16) & (bsi0 > 0.14) & (bsi0 < 0.22)

# Forest / Woodland: Intact high canopy & riparian / dense woodland
s_for_0 = val0 & ~s_wat_0 & ~s_set_0 & (
    ((tc2000 >= 10) & (ndvi0 >= 0.22) & (bsi0 < 0.15)) |
    ((wc == 10) & (ndvi0 >= 0.23) & (bsi0 < 0.15)) |
    ((wc == 20) & (loss == 0) & (tc2000 >= 8) & (ndvi0 >= 0.22) & (bsi0 < 0.15))
)

# Bare / Degraded: Exposed laterite, rock outcrops, eroded bare surfaces (very high BSI)
s_bar_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & (
    ((wc == 60) & (bsi0 > 0.20)) |
    ((ndvi0 < 0.12) & (bsi0 > 0.21) & (tc2000 < 3))
)

# Grassland / Savanna: Herbaceous savanna, rangeland (WC 30, moderate NDVI, moderate BSI)
s_grs_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & ~s_bar_0 & (
    (wc == 30) & (ndvi0 >= 0.11) & (ndvi0 <= 0.20) & (bsi0 >= 0.14) & (bsi0 <= 0.19)
)

# Cropland: Agricultural fields (WC 40, active cultivation)
s_crp_0 = val0 & ~s_wat_0 & ~s_set_0 & ~s_for_0 & ~s_bar_0 & ~s_grs_0 & (
    (wc == 40) & (loss == 0) & (ndvi0 >= 0.16) & (ndvi0 <= 0.26) & (bsi0 >= 0.15) & (bsi0 <= 0.19)
)

# --- 2026 SEEDS ---
s_wat_1 = val1 & ((ndwi1 > 0.05) | ((wc == 80) & (ndwi1 > -0.02)))
s_set_1 = val1 & ~s_wat_1 & (wc == 50) & (ndvi1 < 0.22) & (bsi1 > 0.14)
# Forest in 2026: MUST have loss == 0
s_for_1 = val1 & ~s_wat_1 & ~s_set_1 & (loss == 0) & (
    ((tc2000 >= 10) & (ndvi1 >= 0.30) & (bsi1 < 0.15)) |
    ((wc == 10) & (ndvi1 >= 0.30) & (bsi1 < 0.15))
)
s_bar_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & (
    (wc == 60) |
    ((ndvi1 < 0.16) & (bsi1 > 0.21)) |
    ((loss > 0) & (bsi1 > 0.21) & (ndvi1 < 0.20))
)
s_grs_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & ~s_bar_1 & (
    ((wc == 30) & (ndvi1 >= 0.15) & (ndvi1 <= 0.24) & (bsi1 >= 0.14) & (bsi1 <= 0.19)) |
    ((loss > 0) & (ndvi1 >= 0.14) & (ndvi1 < 0.22) & (bsi1 < 0.19))
)
s_crp_1 = val1 & ~s_wat_1 & ~s_set_1 & ~s_for_1 & ~s_bar_1 & ~s_grs_1 & (
    ((wc == 40) & (ndvi1 >= 0.22) & (ndvi1 <= 0.34) & (bsi1 >= 0.15) & (bsi1 <= 0.20)) |
    ((loss > 0) & (ndvi1 >= 0.20) & (ndvi1 <= 0.32) & (bsi1 >= 0.16))
)

rng = np.random.RandomState(42)

# Prior-weighted sampling so classes match real proportions
samples_per_class = {
    1: 4000,  # Forest
    2: 6000,  # Cropland
    3: 3500,  # Grassland
    4: 3000,  # Bare
    5: 3500,  # Water
    6: 2500,  # Settlement
}

def get_train_data(seeds_dict, fstack):
    X_list, y_list = [], []
    X_flat = fstack.reshape(16, -1).T
    for c, s in seeds_dict.items():
        n = samples_per_class[c]
        idx = np.where(s.ravel())[0]
        chosen = rng.choice(idx, size=min(len(idx), n), replace=(len(idx) < n))
        X_list.append(X_flat[chosen])
        y_list.append(np.full(len(chosen), c, dtype=np.uint8))
    return np.vstack(X_list), np.concatenate(y_list)

seeds_0 = {1: s_for_0, 2: s_crp_0, 3: s_grs_0, 4: s_bar_0, 5: s_wat_0, 6: s_set_0}
seeds_1 = {1: s_for_1, 2: s_crp_1, 3: s_grs_1, 4: s_bar_1, 5: s_wat_1, 6: s_set_1}

X_tr_0, y_tr_0 = get_train_data(seeds_0, fstack_0)
X_tr_1, y_tr_1 = get_train_data(seeds_1, fstack_1)

rf_0 = RandomForestClassifier(n_estimators=100, max_depth=18, min_samples_leaf=4, n_jobs=-1, random_state=42)
rf_0.fit(X_tr_0, y_tr_0)

rf_1 = RandomForestClassifier(n_estimators=100, max_depth=18, min_samples_leaf=4, n_jobs=-1, random_state=42)
rf_1.fit(X_tr_1, y_tr_1)

val_idx_0 = np.where(val0.ravel())[0]
val_idx_1 = np.where(val1.ravel())[0]

pred_0 = np.zeros(h * w, dtype=np.uint8)
for chunk in np.array_split(val_idx_0, 10):
    pred_0[chunk] = rf_0.predict(fstack_0.reshape(16, -1).T[chunk])

pred_1 = np.zeros(h * w, dtype=np.uint8)
for chunk in np.array_split(val_idx_1, 10):
    pred_1[chunk] = rf_1.predict(fstack_1.reshape(16, -1).T[chunk])

print("\n--- BALANCED SAVANNA RESULTS ---")
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

