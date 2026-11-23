#!/usr/bin/env python3
"""
Step 5: 6-Class Post-Classification Change Detection & Trajectory Vectorization.
Computes 6x6 transition matrix, degradation footprints, bi-temporal High-Confidence confirmation,
sieve-filtered MMU (>= 0.45 ha, 5 connected pixels) polygon vectorization, and per-LGA statistics.
Outputs:
- outputs/rasters/Transition_code.tif
- outputs/rasters/Forest_to_*.tif
- outputs/vectors/Forest_to_*.shp
- outputs/rasters/transition_stats.json
- outputs/rasters/lga_change_stats.json
"""
from pathlib import Path
import json
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import shapes, geometry_mask
from shapely.geometry import shape
from scipy.ndimage import label as ndi_label

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_R = BASE_DIR / "outputs" / "rasters"
OUT_V = BASE_DIR / "outputs" / "vectors"

CLASS_NAMES = {
    1: "Woodland / Forest",
    2: "Cropland / Agriculture",
    3: "Grassland / Savanna",
    4: "Bare / Degraded",
    5: "Waterbody",
    6: "Settlement",
}
PIXEL_HA = 900 / 10000.0
MIN_PATCH_PIXELS = 5

def main():
    print("=" * 70)
    print("STEP 5: CHANGE DETECTION & LANDSCAPE CONVERSION TRAJECTORIES")
    print("=" * 70)

    with rasterio.open(OUT_R / "LULC_2000.tif") as src:
        lulc_0 = src.read(1)
        prof = src.profile.copy()
        trans = src.transform

    with rasterio.open(OUT_R / "LULC_2026.tif") as src:
        lulc_1 = src.read(1)

    with rasterio.open(OUT_R / "NDVI_drop_2000_2026.tif") as src:
        ndvi_drop = src.read(1)

    with rasterio.open(OUT_R / "FeatureStack_2000.tif") as src:
        nbr_0 = src.read(10)

    with rasterio.open(OUT_R / "FeatureStack_2026.tif") as src:
        nbr_1 = src.read(10)

    nbr_drop = nbr_0 - nbr_1

    valid = (lulc_0 > 0) & (lulc_1 > 0)

    # 1. 6x6 Transition Matrix
    matrix = np.zeros((7, 7), dtype=np.int64)
    for c0 in range(1, 7):
        for c1 in range(1, 7):
            matrix[c0, c1] = ((lulc_0 == c0) & (lulc_1 == c1) & valid).sum()

    print("\n--- 6x6 Landscape Transition Matrix (Hectares) ---")
    header = f"{'From \\ To':<22}" + "".join(f"{CLASS_NAMES[c][:10]:>12}" for c in range(1, 7)) + f"{'Total 2000':>14}"
    print(header)
    print("-" * len(header))
    for c0 in range(1, 7):
        row_ha = [matrix[c0, c1] * PIXEL_HA for c1 in range(1, 7)]
        tot_ha = sum(row_ha)
        row_str = f"{CLASS_NAMES[c0]:<22}" + "".join(f"{v:>12,1f}" for v in row_ha) + f"{tot_ha:>14,1f}"
        print(row_str)

    # Transition Code Raster (c0 * 10 + c1)
    trans_code = np.zeros_like(lulc_0, dtype=np.uint8)
    trans_code[valid] = (lulc_0[valid] * 10 + lulc_1[valid]).astype(np.uint8)
    p_trans = prof.copy()
    p_trans.update(count=1, dtype="uint8", nodata=0, compress="lzw")
    with rasterio.open(OUT_R / "Transition_code.tif", "w", **p_trans) as dst:
        dst.write(trans_code, 1)

    # 2. Deforestation & Degradation Pathways
    trajectories = [
        ("Forest_to_Agriculture", 1, 2, "Forest to Agriculture Conversion"),
        ("Forest_to_Grassland",   1, 3, "Forest to Grassland Degradation"),
        ("Forest_to_Bare",        1, 4, "Forest to Bare / Degraded Land"),
    ]

    hiconf_mask_base = (ndvi_drop > 0.15) & (nbr_drop > 0.10)

    traj_summary = {}

    for name, c0, c1, desc in trajectories:
        mask_raw = (lulc_0 == c0) & (lulc_1 == c1) & valid
        mask_hiconf = mask_raw & hiconf_mask_base

        raw_ha = mask_raw.sum() * PIXEL_HA
        hiconf_ha = mask_hiconf.sum() * PIXEL_HA

        traj_summary[name] = {
            "description": desc,
            "raw_ha": float(raw_ha),
            "hiconf_ha": float(hiconf_ha),
        }
        print(f"\n{desc}:")
        print(f"  Gross Mapped Area:     {raw_ha:>10,1f} ha")
        print(f"  High-Confidence Loss:  {hiconf_ha:>10,1f} ha (ΔNDVI > 0.15 & ΔNBR > 0.10)")

        # Save rasters
        with rasterio.open(OUT_R / f"{name}.tif", "w", **p_trans) as dst:
            dst.write(mask_raw.astype(np.uint8), 1)
        with rasterio.open(OUT_R / f"{name}_HiConf.tif", "w", **p_trans) as dst:
            dst.write(mask_hiconf.astype(np.uint8), 1)

        # Vectorization with Minimum Mapping Unit (MMU >= 0.45 ha, 5 connected pixels)
        structure = np.ones((3, 3), dtype=np.int32)
        labeled, num_features = ndi_label(mask_raw, structure=structure)
        sizes = np.bincount(labeled.ravel())
        keep_labels = np.where(sizes >= MIN_PATCH_PIXELS)[0]
        keep_labels = keep_labels[keep_labels != 0]

        sieved_mask = np.isin(labeled, keep_labels).astype(np.uint8)

        geom_list = []
        area_list = []
        for geom_dict, val in shapes(sieved_mask, mask=(sieved_mask == 1), transform=trans):
            poly = shape(geom_dict)
            if poly.is_valid and poly.area >= (MIN_PATCH_PIXELS * 900):
                geom_list.append(poly)
                area_list.append(poly.area / 10000.0)

        if geom_list:
            gdf_traj = gpd.GeoDataFrame({
                "geometry": geom_list,
                "area_ha": area_list,
                "type": desc,
            }, crs="EPSG:32631")
            shp_path = OUT_V / f"{name}.shp"
            gdf_traj.to_file(shp_path)
            print(f"  [OK] Exported {len(gdf_traj):,d} polygon features (MMU >= 0.45 ha) -> {shp_path.name}")

    with open(OUT_R / "transition_stats.json", "w") as f:
        json.dump(traj_summary, f, indent=2)

    # 3. Per-LGA Disaggregated Statistics
    print("\n--- Per-LGA Forest Loss & Conversion Statistics ---")
    lgas_gdf = gpd.read_file(OUT_V / "LGAs.shp")
    lga_stats = []

    for _, r in lgas_gdf.iterrows():
        lga_name = str(r.get("ADM2_NAME", "")).strip()
        geom = r.geometry
        l_mask = geometry_mask([geom], transform=trans, out_shape=lulc_0.shape, invert=True)

        row = {"LGA": lga_name}
        for name, c0, c1, _ in trajectories:
            m_raw = (lulc_0 == c0) & (lulc_1 == c1) & valid & l_mask
            m_hi  = m_raw & hiconf_mask_base
            row[f"{name}_raw_ha"] = float(m_raw.sum() * PIXEL_HA)
            row[f"{name}_hiconf_ha"] = float(m_hi.sum() * PIXEL_HA)

        lga_stats.append(row)
        print(f"  {lga_name:<16}: Ag = {row['Forest_to_Agriculture_raw_ha']:>8,1f} ha (HiConf: {row['Forest_to_Agriculture_hiconf_ha']:>6,1f} ha) | Grass = {row['Forest_to_Grassland_raw_ha']:>7,1f} ha")

    with open(OUT_R / "lga_change_stats.json", "w") as f:
        json.dump(lga_stats, f, indent=2)

    print("\n[OK] Step 5 change detection complete.")

if __name__ == "__main__":
    main()

