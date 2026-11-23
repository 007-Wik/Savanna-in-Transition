"""Verify ESRI/WorldCover benchmarked 6-class LULC for Southern Kebbi."""
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask
from scipy.ndimage import binary_dilation
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

# Settlement footprint mask from ESA WorldCover (Class 50)
struct = np.ones((3, 3), dtype=bool)
# In 2026: WorldCover built dilated by 1 pixel (30m) to allow 2021-2026 suburban expansion
settlement_zone_2026 = binary_dilation(wc == 50, structure=struct, iterations=1)
# In 2000: Strictly within the core built footprint
settlement_zone_2000 = (wc == 50)

# 1. WATERBODY (Kainji Lake / Niger River)
wat_0 = val0 & ((ndwi0 > 0.05) | ((wc == 80) & (ndwi0 > -0.02)))
wat_1 = val1 & ((ndwi1 > 0.05) | ((wc == 80) & (ndwi1 > -0.02)))

# 2. SETTLEMENT (Within human settlement zone with urban reflectance)
set_0 = val0 & ~wat_0 & settlement_zone_2000 & (ndvi0 < 0.20) & (bsi0 > 0.12)
set_1 = val1 & ~wat_1 & settlement_zone_2026 & (ndvi1 < 0.24) & (bsi1 > 0.12)

# 3. WOODLAND / FOREST
# In 2000: High canopy (tc2000 >= 10) or dense trees/shrubs (wc 10/20) with high NDVI & low BSI
for_0 = val0 & ~wat_0 & ~set_0 & (
    ((tc2000 >= 10) & (ndvi0 >= 0.22) & (bsi0 < 0.16)) |
    ((wc == 10) & (ndvi0 >= 0.22) & (bsi0 < 0.16)) |
    ((wc == 20) & (loss == 0) & (tc2000 >= 6) & (ndvi0 >= 0.22) & (bsi0 < 0.16))
)

# In 2026: MUST have loss == 0
for_1 = val1 & ~wat_1 & ~set_1 & (loss == 0) & (
    ((tc2000 >= 10) & (ndvi1 >= 0.28) & (bsi1 < 0.16)) |
    ((wc == 10) & (ndvi1 >= 0.28) & (bsi1 < 0.16)) |
    ((wc == 20) & (tc2000 >= 8) & (ndvi1 >= 0.28) & (bsi1 < 0.16))
)

# 4. BARE / DEGRADED (High BSI, low NDVI, rocky ridges, eroded crusts, cleared ground)
bar_0 = val0 & ~wat_0 & ~set_0 & ~for_0 & (
    (wc == 60) |
    ((ndvi0 < 0.14) & (bsi0 > 0.19) & (tc2000 < 3))
)
bar_1 = val1 & ~wat_1 & ~set_1 & ~for_1 & (
    (wc == 60) |
    ((ndvi1 < 0.18) & (bsi1 > 0.19)) |
    ((loss > 0) & (bsi1 > 0.19) & (ndvi1 < 0.22))
)

# 5. CROPLAND (Active farmland, cultivated fields)
crp_0 = val0 & ~wat_0 & ~set_0 & ~for_0 & ~bar_0 & (
    (wc == 40) & (loss == 0) & (ndvi0 >= 0.16) & (ndvi0 <= 0.28) & (bsi0 >= 0.14) & (bsi0 <= 0.19)
)
crp_1 = val1 & ~wat_1 & ~set_1 & ~for_1 & ~bar_1 & (
    ((wc == 40) & (ndvi1 >= 0.22) & (ndvi1 <= 0.36) & (bsi1 >= 0.14) & (bsi1 <= 0.20)) |
    ((loss > 0) & (ndvi1 >= 0.20) & (ndvi1 <= 0.34) & (bsi1 >= 0.15))
)

# 6. GRASSLAND / SAVANNA (Herbaceous savanna, rangeland)
grs_0 = val0 & ~wat_0 & ~set_0 & ~for_0 & ~bar_0 & ~crp_0 & (
    ((wc == 30) & (ndvi0 >= 0.11) & (ndvi0 <= 0.20)) |
    ((tc2000 < 6) & (ndvi0 >= 0.10) & (ndvi0 < 0.16) & (bsi0 < 0.18))
)
grs_1 = val1 & ~wat_1 & ~set_1 & ~for_1 & ~bar_1 & ~crp_1 & (
    ((wc == 30) & (ndvi1 >= 0.15) & (ndvi1 <= 0.24)) |
    ((loss > 0) & (ndvi1 >= 0.14) & (ndvi1 < 0.22) & (bsi1 < 0.18))
)

rng = np.random.RandomState(42)
N_SAMP = 4000

def train_and_predict(seeds_list, fstack, val_mask):
    X_flat = fstack.reshape(16, -1).T
    X_tr, y_tr = [], []
    for c_id, s in enumerate(seeds_list, 1):
        idx = np.where(s.ravel())[0]
        chosen = rng.choice(idx, size=min(len(idx), N_SAMP), replace=(len(idx) < N_SAMP))
        X_tr.append(X_flat[chosen])
        y_tr.append(np.full(len(chosen), c_id, dtype=np.uint8))
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=18, min_samples_leaf=4, n_jobs=-1, random_state=42)
    rf.fit(np.vstack(X_tr), np.concatenate(y_tr))
    
    val_idx = np.where(val_mask.ravel())[0]
    pred = np.zeros(h * w, dtype=np.uint8)
    for chunk in np.array_split(val_idx, 10):
        pred[chunk] = rf.predict(X_flat[chunk])
    return pred, val_idx

print("Running 2000 classification...")
pred_0, val_idx_0 = train_and_predict([for_0, crp_0, grs_0, bar_0, wat_0, set_0], fstack_0, val0)

print("Running 2026 classification...")
pred_1, val_idx_1 = train_and_predict([for_1, crp_1, grs_1, bar_1, wat_1, set_1], fstack_1, val1)

# Post-processing spatial integrity:
# Settlement (Class 6) can ONLY occur within settlement zones (WC 50 buffered).
# Any pixel predicted as Class 6 outside the settlement zone is reclassified to Bare/Degraded (Class 4) or Cropland (Class 2)
sz_0_flat = settlement_zone_2000.ravel()
sz_1_flat = settlement_zone_2026.ravel()

false_built_0 = (pred_0 == 6) & ~sz_0_flat
pred_0[false_built_0] = np.where(bsi0.ravel()[false_built_0] > 0.18, 4, 2)

false_built_1 = (pred_1 == 6) & ~sz_1_flat
pred_1[false_built_1] = np.where(bsi1.ravel()[false_built_1] > 0.18, 4, 2)

print("\n" + "=" * 75)
print("ESRI / WORLDCOVER BENCHMARKED 6-CLASS LULC BREAKDOWN")
print("=" * 75)
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
