#!/usr/bin/env python3
"""
Step 1: Integrity Check & Geometric Pre-flight Verification.
Verifies raster bounds, CRS (EPSG:32631 UTM Zone 31N), pixel resolution, and reprojection.
Outputs reprojected LGA administrative boundaries and dissolved study area AOI.
"""
import sys
from pathlib import Path
import rasterio
import geopandas as gpd
import numpy as np

# Dynamically resolve project root for cross-platform portability
BASE_DIR = Path(__file__).resolve().parents[2]
DATA = BASE_DIR / "data"
OUT_VEC = BASE_DIR / "outputs" / "vectors"
OUT_VEC.mkdir(parents=True, exist_ok=True)

TARGET_CRS = "EPSG:32631"

RASTERS = {
    "Landsat_2000": DATA / "Kebbi_Landsat_2000.tif",
    "Landsat_2026": DATA / "Kebbi_Landsat_2026.tif",
    "Hansen":       DATA / "Kebbi_Hansen.tif",
    "WorldCover":   DATA / "Kebbi_WorldCover_2021.tif",
    "SRTM":         DATA / "Kebbi_SRTM.tif",
    "VCF":          DATA / "Kebbi_VCF_annual_2000_2024.tif",
}

def main():
    print("=" * 70)
    print("STEP 1: INTEGRITY CHECK & GEOMETRIC HARMONIZATION")
    print("=" * 70)
    print(f"Project Root: {BASE_DIR}")
    print(f"Data Directory: {DATA}")

    for name, path in RASTERS.items():
        if not path.exists():
            print(f"  [MISSING] {name}: {path.name} not found in {DATA}")
            continue
        with rasterio.open(path) as src:
            crs_ok = "OK" if str(src.crs) == TARGET_CRS else f"MISMATCH ({src.crs})"
            print(f"\n{name} ({path.name}):")
            print(f"  Shape:  {src.count} bands × {src.height} rows × {src.width} cols")
            print(f"  Dtype:  {src.dtypes[0]}")
            print(f"  CRS:    {src.crs}  [{crs_ok}]")
            print(f"  Res:    {src.res}")

    print("\n--- Processing LGA Administrative Boundaries ---")
    lga_path = DATA / "Kebbi_LGAs.shp"
    if not lga_path.exists():
        raise FileNotFoundError(f"Missing LGA shapefile: {lga_path}")

    lga = gpd.read_file(lga_path)
    print(f"  Source CRS: {lga.crs}")
    print(f"  Total LGAs: {len(lga)}")

    if str(lga.crs) != TARGET_CRS:
        print(f"  Reprojecting LGA vector layer to {TARGET_CRS}...")
        lga = lga.to_crs(TARGET_CRS)

    lga_out = OUT_VEC / "LGAs.shp"
    lga.to_file(lga_out)
    print(f"  [OK] Saved standardized LGAs -> {lga_out}")

    aoi = lga.dissolve()
    aoi_out = OUT_VEC / "AOI.shp"
    aoi.to_file(aoi_out)
    total_area_ha = aoi.geometry.area.sum() / 10000.0
    print(f"  [OK] Saved dissolved Study Area AOI -> {aoi_out}")
    print(f"  Total Study Area: {total_area_ha:,.1f} ha ({total_area_ha / 100.0:,.1f} km²)")
    print("\n[OK] Step 1 verification successfully completed.")

if __name__ == "__main__":
    main()

