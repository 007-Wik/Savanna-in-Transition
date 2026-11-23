#!/usr/bin/env python3
"""
Step 2: Derive 16-Dimensional Spectral & Topographic Feature Stacks.
Applies Crist (1985) Tasseled Cap coefficients to Landsat 5 TM (2000)
and Baig et al. (2014) coefficients to Landsat 8/9 OLI (2026).
Computes NDVI, EVI, NDWI, NBR, BSI, DEM elevation, and topographic slope.
Outputs FeatureStack_2000.tif and FeatureStack_2026.tif.
"""
from pathlib import Path
import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask

BASE_DIR = Path(__file__).resolve().parents[2]
DATA = BASE_DIR / "data"
OUT = BASE_DIR / "outputs" / "rasters"
OUT_V = BASE_DIR / "outputs" / "vectors"
OUT.mkdir(parents=True, exist_ok=True)

# Sensor-specific Tasseled Cap Coefficients (Surface Reflectance)
# Crist (1985) for Landsat 5 TM (Blue, Green, Red, NIR, SWIR1, SWIR2)
TC_TM = {
    "brightness": np.array([0.3037, 0.2793, 0.4743, 0.5585, 0.5082, 0.1863], dtype=np.float32),
    "greenness":  np.array([-0.2848, -0.2435, -0.5436, 0.7243, 0.0840, -0.1800], dtype=np.float32),
    "wetness":    np.array([0.1509, 0.1973, 0.3279, 0.3406, -0.7112, -0.4572], dtype=np.float32),
}

# Baig et al. (2014) for Landsat 8/9 OLI (B2, B3, B4, B5, B6, B7)
TC_OLI = {
    "brightness": np.array([0.3029, 0.2786, 0.4733, 0.5599, 0.5080, 0.1872], dtype=np.float32),
    "greenness":  np.array([-0.2941, -0.2430, -0.5424, 0.7276, 0.0713, -0.1608], dtype=np.float32),
    "wetness":    np.array([0.1511, 0.1973, 0.3283, 0.3407, -0.7117, -0.4559], dtype=np.float32),
}

def compute_slope(elev, transform):
    res_x = abs(transform[0])
    res_y = abs(transform[4])
    padded = np.pad(elev, 1, mode="edge")
    dy, dx = np.gradient(padded, res_y, res_x)
    dy, dx = dy[1:-1, 1:-1], dx[1:-1, 1:-1]
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
    return slope.astype(np.float32)

def build_feature_stack(landsat_path, srtm_path, aoi_gdf, year, out_path):
    print(f"\n--- Building feature stack for {year} ---")
    with rasterio.open(landsat_path) as src:
        bands = src.read().astype(np.float32)
        profile = src.profile.copy()
        transform = src.transform
        shape = (src.height, src.width)

    aoi_mask = geometry_mask(aoi_gdf.geometry, transform=transform, out_shape=shape, invert=True)
    valid_data = aoi_mask & np.isfinite(bands).all(axis=0)

    clamped_bands = np.clip(bands, 0.0, 1.0)
    blue, green, red, nir, swir1, swir2 = clamped_bands

    eps = 1e-10
    ndvi = (nir - red) / (nir + red + eps)
    nbr  = (nir - swir2) / (nir + swir2 + eps)
    ndwi = (green - nir) / (green + nir + eps)
    evi  = 2.5 * (nir - red) / (nir + 6.0 * red - 7.5 * blue + 1.0 + eps)
    bsi  = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + eps)

    tc = TC_TM if year == 2000 else TC_OLI
    tc_bright = sum(tc["brightness"][i] * clamped_bands[i] for i in range(6))
    tc_green  = sum(tc["greenness"][i] * clamped_bands[i] for i in range(6))
    tc_wet    = sum(tc["wetness"][i] * clamped_bands[i] for i in range(6))

    with rasterio.open(srtm_path) as src_srtm:
        elev = src_srtm.read(1).astype(np.float32)
        if (src_srtm.height, src_srtm.width) != shape:
            from rasterio.warp import reproject, Resampling
            elev_resamp = np.zeros(shape, dtype=np.float32)
            reproject(
                source=elev,
                destination=elev_resamp,
                src_transform=src_srtm.transform,
                src_crs=src_srtm.crs,
                dst_transform=transform,
                dst_crs=profile["crs"],
                resampling=Resampling.bilinear,
            )
            elev = elev_resamp

    elev[~aoi_mask] = np.nan
    slope = compute_slope(elev, transform)

    # Save isolated NDVI raster for direct mapping
    ndvi_out = OUT / f"NDVI_{year}.tif"
    p_ndvi = profile.copy()
    p_ndvi.update(count=1, dtype="float32", nodata=np.nan)
    with rasterio.open(ndvi_out, "w", **p_ndvi) as dst:
        ndvi_write = ndvi.copy()
        ndvi_write[~valid_data] = np.nan
        dst.write(ndvi_write, 1)
    print(f"  [OK] Saved isolated NDVI raster -> {ndvi_out.name}")

    features = [
        blue, green, red, nir, swir1, swir2,
        ndvi, evi, ndwi, nbr, bsi,
        tc_bright, tc_green, tc_wet,
        elev, slope,
    ]

    stack = np.stack(features, axis=0)
    stack[:, ~valid_data] = np.nan

    profile.update(count=16, dtype="float32", nodata=np.nan, compress="lzw")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(stack)
        dst.descriptions = (
            "Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2",
            "NDVI", "EVI", "NDWI", "NBR", "BSI",
            "TC_Brightness", "TC_Greenness", "TC_Wetness",
            "DEM_Elevation", "Slope_Deg",
        )
    print(f"  [OK] Saved 16-band feature stack -> {out_path.name}")
    return ndvi, valid_data

def main():
    print("=" * 70)
    print("STEP 2: SPECTRAL FEATURE EXTRACTION & TASSELED CAP TRANSFORM")
    print("=" * 70)
    aoi_gdf = gpd.read_file(OUT_V / "AOI.shp")
    srtm = DATA / "Kebbi_SRTM.tif"

    ndvi_00, val_00 = build_feature_stack(DATA / "Kebbi_Landsat_2000.tif", srtm, aoi_gdf, 2000, OUT / "FeatureStack_2000.tif")
    ndvi_26, val_26 = build_feature_stack(DATA / "Kebbi_Landsat_2026.tif", srtm, aoi_gdf, 2026, OUT / "FeatureStack_2026.tif")

    # Compute Bi-temporal Canopy Drop (NDVI 2000 - NDVI 2026)
    ndvi_drop = ndvi_00 - ndvi_26
    both_valid = val_00 & val_26
    ndvi_drop[~both_valid] = np.nan

    with rasterio.open(OUT / "FeatureStack_2026.tif") as src:
        prof = src.profile.copy()
    prof.update(count=1, dtype="float32", nodata=np.nan)
    drop_path = OUT / "NDVI_drop_2000_2026.tif"
    with rasterio.open(drop_path, "w", **prof) as dst:
        dst.write(ndvi_drop, 1)
    print(f"\n  [OK] Saved Bi-Temporal Canopy Drop raster -> {drop_path.name}")
    print("\n[OK] Step 2 feature extraction complete.")

if __name__ == "__main__":
    main()

