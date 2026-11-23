# Input data

The input rasters (~1.3 GB) are too large for git and are **not** included in this repository. Place these files in this folder before running the pipeline:

| File | Contents | Approx. size |
| :--- | :--- | ---: |
| `Kebbi_Landsat_2000.tif` | Landsat 5 TM surface reflectance, 30 m | 427 MB |
| `Kebbi_Landsat_2026.tif` | Landsat 8/9 OLI surface reflectance, 30 m | 484 MB |
| `Kebbi_ESRI_LULC_2025.tif` | Esri Sentinel-2 10 m LULC 2025, resampled to 30 m | 2 MB |
| `Kebbi_WorldCover_2021.tif` | ESA WorldCover 2021 v200 | 2.5 MB |
| `Kebbi_Hansen.tif` | Hansen GFC v1.11 tree cover 2000 and loss year | 40 MB |
| `Kebbi_SRTM.tif` | SRTM 30 m DEM | 30 MB |
| `Kebbi_VCF_annual_2000_2024.tif` | MODIS MOD44B annual tree cover, 2000–2024 | 26 MB |
| `Kebbi_LGAs.shp` (+ `.dbf .prj .shx .cpg`) | Kebbi State LGA boundaries | <1 MB |

All rasters use **EPSG:32631 (WGS 84 / UTM zone 31N)**. Check them with:

```bash
python main.py --check
```

To regenerate `Kebbi_ESRI_LULC_2025.tif`, run [`scripts/utilities/download_esri_lulc_2025.py`](../scripts/utilities/download_esri_lulc_2025.py).

Dataset provenance and licences are in [`docs/DATA_SOURCES.md`](../docs/DATA_SOURCES.md). To get the exact prepared inputs, contact **Satwik K Udupi** (PravahaTattva Solutions, Karad) or **Yazid Abubakar Fakai**.
