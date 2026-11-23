# Data sources and attribution

This research by **Satwik K Udupi** in collaboration with **Yazid Abubakar Fakai** combines the public Earth-observation datasets below. When you reuse any derived product, cite the original dataset alongside this work. BibTeX entries for every item are in [`references.bib`](references.bib).

| # | Dataset | File in `data/` | Role in the pipeline |
| :-: | :--- | :--- | :--- |
| 1 | Landsat 5 TM Collection 2 Level-2 Surface Reflectance | `Kebbi_Landsat_2000.tif` | Baseline epoch (dry season, Dec 2000 – Feb 2001) |
| 2 | Landsat 8/9 OLI Collection 2 Level-2 Surface Reflectance | `Kebbi_Landsat_2026.tif` | Target epoch (dry season, Dec 2025 – Feb 2026) |
| 3 | Esri Sentinel-2 10 m Annual Land Use/Land Cover (2025) | `Kebbi_ESRI_LULC_2025.tif` | Pseudo-label benchmark; cropland calibration |
| 4 | ESA WorldCover 10 m 2021 v200 | `Kebbi_WorldCover_2021.tif` | Pseudo-label benchmark; built-up (class 50) anchor |
| 5 | Hansen Global Forest Change v1.11 (2000–2023) | `Kebbi_Hansen.tif` | Tree-cover 2000 and annual loss benchmark |
| 6 | NASA SRTM 1 arc-second DEM | `Kebbi_SRTM.tif` | Elevation, slope and hillshade |
| 7 | MODIS/Terra MOD44B Vegetation Continuous Fields v061 | `Kebbi_VCF_annual_2000_2024.tif` | Annual tree-canopy trend, 2000–2024 |
| 8 | Kebbi State LGA administrative boundaries | `Kebbi_LGAs.shp` | Study-area mask and per-LGA statistics |

---

### 1–2. Landsat Collection 2 Level-2 (USGS)

- **Provider:** U.S. Geological Survey and NASA.
- **Citation:** U.S. Geological Survey (2020). *Landsat 4-5 TM Level-2, Collection 2.* https://doi.org/10.5066/P9IAXOVV, and *Landsat 8-9 OLI/TIRS Level-2, Collection 2.* https://doi.org/10.5066/P9OGBGM6
- **Licence:** Public domain (US Government work). Requested credit: "Landsat imagery courtesy of the U.S. Geological Survey."
- **Access:** https://earthexplorer.usgs.gov/ or Google Earth Engine (`LANDSAT/LT05/C02/T1_L2`, `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`).

### 3. Esri Sentinel-2 10 m Land Use/Land Cover

- **Provider:** Esri, Impact Observatory and Microsoft, derived from ESA Sentinel-2 imagery.
- **Citation:** Karra, K., et al. (2021). Global land use/land cover with Sentinel 2 and deep learning. *IGARSS 2021*, 4704–4707. https://doi.org/10.1109/IGARSS47720.2021.9553499
- **Licence:** CC BY 4.0.
- **Access:** ArcGIS ImageServer `Sentinel2_10m_LandCover`, fetched by [`scripts/utilities/download_esri_lulc_2025.py`](../scripts/utilities/download_esri_lulc_2025.py). The UTM tiles 31P and 32P are also downloadable from https://livingatlas.arcgis.com/landcover/.

### 4. ESA WorldCover 2021 v200

- **Provider:** European Space Agency (ESA) and the WorldCover consortium.
- **Citation:** Zanaga, D., et al. (2022). *ESA WorldCover 10 m 2021 v200.* Zenodo. https://doi.org/10.5281/zenodo.7254221
- **Licence:** CC BY 4.0. Requested credit: "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."
- **Access:** https://esa-worldcover.org/ or Google Earth Engine (`ESA/WorldCover/v200`).

### 5. Hansen Global Forest Change v1.11

- **Provider:** University of Maryland, Global Land Analysis and Discovery (GLAD) lab.
- **Citation:** Hansen, M. C., et al. (2013). High-resolution global maps of 21st-century forest cover change. *Science, 342*(6160), 850–853. https://doi.org/10.1126/science.1244693
- **Licence:** CC BY 4.0.
- **Access:** https://glad.earthengine.app/view/global-forest-change or Google Earth Engine (`UMD/hansen/global_forest_change_2023_v1_11`).

### 6. SRTM DEM

- **Provider:** NASA Jet Propulsion Laboratory.
- **Citation:** Farr, T. G., et al. (2007). The Shuttle Radar Topography Mission. *Reviews of Geophysics, 45*(2), RG2004. https://doi.org/10.1029/2005RG000183. Dataset: NASA JPL (2013), *NASA SRTM Global 1 arc second V003*, https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL1.003
- **Licence:** Public domain.
- **Access:** NASA Earthdata or Google Earth Engine (`USGS/SRTMGL1_003`).

### 7. MODIS MOD44B Vegetation Continuous Fields

- **Provider:** NASA Land Processes DAAC.
- **Citation:** DiMiceli, C., Townshend, J., Carroll, M., & Sohlberg, R. (2021). *MODIS/Terra Vegetation Continuous Fields Yearly L3 Global 250m SIN Grid V061.* https://doi.org/10.5067/MODIS/MOD44B.061
- **Licence:** No restrictions on reuse (NASA EOSDIS data policy). Citation is requested.
- **Access:** NASA Earthdata or Google Earth Engine (`MODIS/061/MOD44B`).

### 8. LGA administrative boundaries

- Local Government Area polygons for Kebbi State, used to define the seven-LGA Southern Kebbi Senatorial District (Danko-Wasagu, Fakai, Ngaski, Sakaba, Shanga, Yauri, Zuru).
- **Provenance:** supplied with the author's project data. *Author: please record the original publisher and licence here (for example GRID3 Nigeria, OCHA/HDX COD-AB or the Office of the Surveyor-General of the Federation).*

---

Derived maps carry the credit line "USGS / NASA" or the relevant provider. The classification, change detection, validation, cartography and interpretation are the original work of Satwik K Udupi in collaboration with Yazid Abubakar Fakai.
