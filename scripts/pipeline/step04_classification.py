#!/usr/bin/env python3
"""
Step 4: Balanced Random Forest Supervised Classification.
Trains Random Forest classifiers with 5-fold cross-validation on safe endmember samples.
Classifies full landscape into 6 thematic classes:
1. Woodland / Forest, 2. Cropland / Agriculture, 3. Grassland / Savanna,
4. Bare / Degraded, 5. Waterbody, 6. Settlement.
Outputs outputs/rasters/LULC_2000.tif and LULC_2026.tif.
"""
from pathlib import Path
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

BASE_DIR = Path(__file__).resolve().parents[2]
DATA = BASE_DIR / "data"
OUT = BASE_DIR / "outputs" / "rasters"
OUT_V = BASE_DIR / "outputs" / "vectors"

CLASS_NAMES = {
    1: "Woodland / Forest",
    2: "Cropland / Agriculture",
    3: "Grassland / Savanna",
    4: "Bare / Degraded",
    5: "Waterbody",
    6: "Settlement",
}

def train_and_predict(year, fstack_path, labels_path, out_path, aoi_mask, profile):
    print(f"\n--- Supervised Classification for Epoch {year} ---")
    with rasterio.open(fstack_path) as src:
        features = src.read() # (16, H, W)

    with rasterio.open(labels_path) as src:
        labels = src.read(1)

    c, h, w = features.shape
    valid_px = aoi_mask & np.all(np.isfinite(features), axis=0)

    # Sample 6,000 pixels per class
    N_PER_CLASS = 6000
    rng = np.random.RandomState(42)
    sample_indices = []
    sample_labels = []

    for cl in range(1, 7):
        idx = np.where((labels == cl) & valid_px)[0] if labels.ndim == 1 else np.where(((labels == cl) & valid_px).ravel())[0]
        if len(idx) == 0:
            continue
        n_take = min(len(idx), N_PER_CLASS)
        chosen = rng.choice(idx, size=n_take, replace=False)
        sample_indices.extend(chosen)
        sample_labels.extend([cl] * n_take)

    sample_indices = np.array(sample_indices)
    sample_labels = np.array(sample_labels)

    feat_2d = features.reshape(c, -1).T
    X_train = feat_2d[sample_indices]
    y_train = sample_labels

    print(f"  Training dataset: {len(X_train):,d} samples across 6 classes.")

    rf = RandomForestClassifier(
        n_estimators=120,
        max_depth=22,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(rf, X_train, y_train, cv=cv, scoring="accuracy")
    print(f"  5-Fold Cross-Validation Accuracy: {scores.mean()*100:.2f}% ± {scores.std()*100:.2f}%")

    rf.fit(X_train, y_train)

    # Chunked landscape prediction to optimize memory
    print(f"  Predicting full-resolution {year} landscape...")
    pred_flat = np.zeros(h * w, dtype=np.uint8)
    valid_idx = np.where(valid_px.ravel())[0]

    chunk_size = 250000
    for i in range(0, len(valid_idx), chunk_size):
        c_idx = valid_idx[i:i + chunk_size]
        pred_flat[c_idx] = rf.predict(feat_2d[c_idx])

    pred = pred_flat.reshape(h, w)

    # Spatial post-classification constraint on settlement
    # Any settlement pixel must be near verified built-up core
    settle_mask = (pred == 6)
    if settle_mask.sum() > 0:
        with rasterio.open(DATA / "Kebbi_WorldCover_2021.tif") as s_wc:
            wc_ref = s_wc.read(1)
        esri_ref_p = DATA / "Kebbi_ESRI_LULC_2025.tif"
        if esri_ref_p.exists():
            with rasterio.open(esri_ref_p) as s_es:
                es_ref = s_es.read(1)
            verified_built = (wc_ref == 50) | (es_ref == 7)
        else:
            verified_built = (wc_ref == 50)
        from scipy.ndimage import binary_dilation
        built_corridor = binary_dilation(verified_built, iterations=3)
        false_settle = settle_mask & (~built_corridor)
        # Reallocate isolated false settlements to surrounding majority (cropland or grassland)
        pred[false_settle] = 2

    print(f"  Thematic distribution for {year}:")
    for cl in range(1, 7):
        cnt = (pred == cl).sum()
        ha = cnt * 0.09
        pct = (cnt / valid_px.sum()) * 100
        print(f"    {CLASS_NAMES[cl]:24s}: {ha:11,1f} ha ({pct:5.2f}%)")

    p_out = profile.copy()
    p_out.update(count=1, dtype="uint8", nodata=0, compress="lzw")
    with rasterio.open(out_path, "w", **p_out) as dst:
        dst.write(pred, 1)
    print(f"  [OK] Saved LULC map -> {out_path.name}")
    return pred

def main():
    print("=" * 70)
    print("STEP 4: RANDOM FOREST CLASSIFICATION & SPATIAL CALIBRATION")
    print("=" * 70)
    aoi_gdf = gpd.read_file(OUT_V / "AOI.shp")
    with rasterio.open(OUT / "FeatureStack_2000.tif") as src:
        prof = src.profile.copy()
        h, w = src.height, src.width
        trans = src.transform

    aoi_mask = geometry_mask(aoi_gdf.geometry, transform=trans, out_shape=(h, w), invert=True)

    train_and_predict(2000, OUT / "FeatureStack_2000.tif", OUT / "PseudoLabels_2000.tif", OUT / "LULC_2000.tif", aoi_mask, prof)
    train_and_predict(2026, OUT / "FeatureStack_2026.tif", OUT / "PseudoLabels_2026.tif", OUT / "LULC_2026.tif", aoi_mask, prof)
    print("\n[OK] Step 4 classification complete.")

if __name__ == "__main__":
    main()

