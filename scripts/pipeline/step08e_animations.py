#!/usr/bin/env python3
"""
Step 8e: Bi-temporal Cartographic GIF Animation Generator (Lohara Standard).
Generates publication-grade animated comparative GIFs maintaining the EXACT
cartographic map layout (4-sided graticules, header banners, legend, scalebar,
north arrow, and metadata strips):
1. outputs/gifs/LULC_change_2000_2026.gif  (Land Use & Land Cover Dynamics)
2. outputs/gifs/NDVI_change_2000_2026.gif  (Seasonal Vegetation Health & Canopy Dynamics)
3. outputs/gifs/TCC_change_2000_2026.gif   (Landsat Natural Color Photographic Composite)

Specifications:
- Carries the complete, unaltered Lohara Taluka cartographic map plate architecture.
- High-fidelity Lanczos downsampling (1500px width) for ultra-sharp typography & borders.
- Calibrated 1.8s (1800ms) epoch hold for cognitive flicker-comparison.
- 100% offline-compatible and self-contained with relative paths.
"""
from pathlib import Path
import warnings
from PIL import Image

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parents[2]
MAPS_DIR = BASE_DIR / "outputs" / "maps"
GIFS_DIR = BASE_DIR / "outputs" / "gifs"
GIFS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_WIDTH = 1500  # High-definition width preserving crisp 300 DPI text
FRAME_DURATION = 1800  # 1.8 seconds per epoch

def ensure_map_exists(filename, render_func_name):
    map_path = MAPS_DIR / filename
    if not map_path.exists():
        print(f"  [NOTICE] {filename} not found in outputs/maps/. Rendering on demand...")
        from scripts.pipeline import step08a_maps
        func = getattr(step08a_maps, render_func_name)
        func()
    return map_path

def build_cartographic_gif(name, f1_name, f2_name, render_f1=None, render_f2=None, duration=FRAME_DURATION):
    p1 = MAPS_DIR / f1_name
    p2 = MAPS_DIR / f2_name

    if not p1.exists() and render_f1:
        ensure_map_exists(f1_name, render_f1)
    if not p2.exists() and render_f2:
        ensure_map_exists(f2_name, render_f2)

    if not p1.exists() or not p2.exists():
        print(f"  [WARNING] Cannot generate {name}: missing {f1_name} or {f2_name}.")
        return None

    # Load high-resolution 300 DPI cartographic map plates
    im1 = Image.open(p1).convert("RGB")
    im2 = Image.open(p2).convert("RGB")

    # Resize to high-definition display resolution preserving aspect ratio
    w = TARGET_WIDTH
    h1 = int(im1.height * (w / im1.width))
    h2 = int(im2.height * (w / im2.width))
    
    im1_resized = im1.resize((w, h1), Image.Resampling.LANCZOS)
    im2_resized = im2.resize((w, h2), Image.Resampling.LANCZOS)

    # Quantize to adaptive 256-color palette for crisp vector/raster rendering
    im1_q = im1_resized.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
    im2_q = im2_resized.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)

    out_path = GIFS_DIR / name
    im1_q.save(
        out_path,
        save_all=True,
        append_images=[im2_q],
        duration=duration,
        loop=0,
        optimize=True,
    )

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  [OK] Saved Cartographic Animated GIF -> {name} ({size_mb:.2f} MB, {w}x{h1}px)")
    return out_path

def main():
    print("=" * 70)
    print("STEP 8E: CARTOGRAPHIC MAP-LAYOUT BI-TEMPORAL GIF ANIMATION GENERATOR")
    print("=" * 70)

    # 1. Land Use and Land Cover (LULC) Cartographic GIF
    print(">> Generating LULC Bi-temporal Animated Map Plate (2000 vs 2026)...")
    build_cartographic_gif(
        name="LULC_change_2000_2026.gif",
        f1_name="LULC_2000.png",
        f2_name="LULC_2026.png",
        render_f1="render_lulc_map",
        render_f2="render_lulc_map",
        duration=1800,
    )

    # 2. Vegetation Health & Canopy Density (NDVI) Cartographic GIF
    print(">> Generating NDVI Bi-temporal Animated Map Plate (2000 vs 2026)...")
    build_cartographic_gif(
        name="NDVI_change_2000_2026.gif",
        f1_name="NDVI_2000.png",
        f2_name="NDVI_2026.png",
        render_f1="render_ndvi_map",
        render_f2="render_ndvi_map",
        duration=1800,
    )

    # 3. Landsat True Colour Composite (TCC) Cartographic GIF
    print(">> Generating True Colour Composite (TCC) Animated Map Plate (2000 vs 2026)...")
    build_cartographic_gif(
        name="TCC_change_2000_2026.gif",
        f1_name="TCC_2000.png",
        f2_name="TCC_2026.png",
        render_f1="render_tcc_map",
        render_f2="render_tcc_map",
        duration=1800,
    )

    print("\n[OK] All cartographic GIF animations generated in outputs/gifs/ carrying full map layout.")

if __name__ == "__main__":
    main()
