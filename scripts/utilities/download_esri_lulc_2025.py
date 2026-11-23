#!/usr/bin/env python3
"""
Download and Mosaic ESRI Sentinel-2 10m Land Use / Land Cover (2025)
Service: https://ic.imagery1.arcgis.com/arcgis/rest/services/Sentinel2_10m_LandCover/ImageServer
Target AOI: Southern Kebbi Senatorial District (EPSG:32631, 30m resolution)
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import Resampling, reproject

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs" / "rasters"
TEMP_DIR = DATA_DIR / "temp_esri_2025"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Reference raster properties
REF_PATH = OUT_DIR / "LULC_2026.tif"
with rasterio.open(REF_PATH) as ref:
    REF_META = ref.meta.copy()
    REF_BOUNDS = ref.bounds
    REF_SHAPE = ref.shape
    REF_TRANSFORM = ref.transform
    REF_CRS = ref.crs

print(f"Target bounds: {REF_BOUNDS}")
print(f"Target shape: {REF_SHAPE}, CRS: {REF_CRS}")

# Grid partition: 2x2 grid
xmin, ymin, xmax, ymax = REF_BOUNDS.left, REF_BOUNDS.bottom, REF_BOUNDS.right, REF_BOUNDS.top
x_mid = (xmin + xmax) / 2.0
y_mid = (ymin + ymax) / 2.0

tiles = [
    ("tl", xmin, y_mid, x_mid, ymax),
    ("tr", x_mid, y_mid, xmax, ymax),
    ("bl", xmin, ymin, x_mid, y_mid),
    ("br", x_mid, ymin, xmax, y_mid),
]

SERVICE_URL = "https://ic.imagery1.arcgis.com/arcgis/rest/services/Sentinel2_10m_LandCover/ImageServer/exportImage?"
downloaded_files = []

for name, t_xmin, t_ymin, t_xmax, t_ymax in tiles:
    out_tile = TEMP_DIR / f"esri_2025_{name}.tif"
    if out_tile.exists() and out_tile.stat().st_size > 10000:
        print(f"Tile {name} already exists ({out_tile.stat().st_size / 1e6:.2f} MB). Skipping download.")
        downloaded_files.append(out_tile)
        continue

    # Calculate pixel width and height at 30m
    w = int(round((t_xmax - t_xmin) / 30.0))
    h = int(round((t_ymax - t_ymin) / 30.0))

    params = {
        "bbox": f"{t_xmin},{t_ymin},{t_xmax},{t_ymax}",
        "bboxSR": "32631",
        "imageSR": "32631",
        "size": f"{w},{h}",
        "format": "tiff",
        "pixelType": "U8",
        "noDataInterpretation": "esriNoDataMatchAny",
        "interpolation": "RSP_NearestNeighbor",
        "mosaicRule": json.dumps({
            "mosaicMethod": "esriMosaicAttribute",
            "sortField": "Year",
            "sortValue": "2025",
            "where": "Year = 2025"
        }),
        "f": "json"
    }

    req_url = SERVICE_URL + urllib.parse.urlencode(params)
    print(f"Requesting tile {name} ({w}x{h})...")
    req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
    
    success = False
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "href" in data:
                href = data["href"]
                print(f"  Downloading from {href[:80]}...")
                urllib.request.urlretrieve(href, out_tile)
                print(f"  Saved {out_tile.name} ({out_tile.stat().st_size / 1e6:.2f} MB)")
                downloaded_files.append(out_tile)
                success = True
                break
            else:
                print(f"  API response error: {data}")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(3)
            
    if not success:
        print(f"ERROR: Failed to download tile {name}")
        sys.exit(1)

# Stitch and align directly onto reference grid
print("\nMosaicing and aligning tiles to Southern Kebbi grid...")
final_path = DATA_DIR / "Kebbi_ESRI_LULC_2025.tif"

mosaic_arr = np.zeros(REF_SHAPE, dtype=np.uint8)

for tile_path in downloaded_files:
    with rasterio.open(tile_path) as src:
        tile_data = src.read(1)
        reproject(
            source=tile_data,
            destination=mosaic_arr,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=REF_TRANSFORM,
            dst_crs=REF_CRS,
            resampling=Resampling.nearest
        )

# Apply AOI boundary mask
import geopandas as gpd
from rasterio.mask import mask
aoi_gdf = gpd.read_file(BASE_DIR / "outputs" / "vectors" / "AOI.shp")
aoi_geom = aoi_gdf.geometry.unary_union

# Save unmasked mosaic first
REF_META.update({
    "driver": "GTiff",
    "height": REF_SHAPE[0],
    "width": REF_SHAPE[1],
    "count": 1,
    "dtype": "uint8",
    "nodata": 0,
    "compress": "lzw"
})

with rasterio.open(final_path, "w", **REF_META) as dst:
    dst.write(mosaic_arr, 1)

print(f"[OK] Saved mosaic: {final_path}")

# Inspect statistics within AOI
with rasterio.open(final_path) as src:
    masked_data, _ = mask(src, [aoi_geom], crop=False, nodata=0)
    arr = masked_data[0]

valid = arr[arr > 0]
vals, counts = np.unique(valid, return_counts=True)

class_names = {
    1: "Water",
    2: "Trees (Woodland/Forest)",
    4: "Flooded Vegetation",
    5: "Crops (Agriculture)",
    7: "Built Area (Settlement)",
    8: "Bare Ground",
    11: "Rangeland (Grassland/Savanna)"
}

print("\n========================================================")
print("ESRI SENTINEL-2 10m LULC (2025) IN SOUTHERN KEBBI AOI")
print("========================================================")
total_ha = len(valid) * 900.0 / 10000.0
print(f"Total classified area: {total_ha:,.1f} ha")
for v, c in zip(vals, counts):
    ha = c * 900.0 / 10000.0
    pct = c / len(valid) * 100.0
    name = class_names.get(v, f"Class {v}")
    print(f"  [{v:2d}] {name:30s}: {ha:10,.1f} ha ({pct:5.2f}%)")
print("========================================================")

