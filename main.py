#!/usr/bin/env python3
"""
========================================================================================
SOUTHERN KEBBI REMOTE SENSING RESEARCH PIPELINE — MASTER ORCHESTRATOR
========================================================================================
Doctoral Dissertation Earth Observation Pipeline:
"Multi-Decadal Land Use and Land Cover Dynamics, Canopy Degradation Trajectories,
and Multi-Sensor Ground-Truthing in the Sudan-Guinea Savanna Transition Zone (2000–2026)"

Developed by: Satwik K Udupi (JRF, CCCSS, SUK; PravahaTattva Solutions, Karad)
In collaboration with: Yazid Abubakar Fakai (PhD Scholar)
Copyright (c) 2026 Yazid Abubakar Fakai. All rights reserved. See LICENSE.
Target: Southern Kebbi Senatorial District, Kebbi State, Nigeria (12,294 km²)
Advisory Committee / Guide Automated Execution Engine
========================================================================================
"""
import sys
import os
import time
import argparse
import subprocess
from pathlib import Path

# Force UTF-8 stdout if supported, or ASCII fallback
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts" / "pipeline"

STEPS = [
    ("1",  "step01_integrity_check.py",  "Integrity Check & Pre-Flight Harmonization"),
    ("2",  "step02_spectral_features.py","16-Band Spectral & Topographic Stack Extraction"),
    ("3",  "step03_pseudo_labels.py",    "Safe ESRI 2025 & ESA WorldCover Pseudo-Labels"),
    ("4",  "step04_classification.py",   "Balanced Random Forest 5-Fold Cross-Validation"),
    ("5",  "step05_change_detection.py", "6-Class Transition Dynamics & MMU Vectorization"),
    ("6",  "step06_olofsson_accuracy.py","Olofsson (2014) Design-Based Accuracy Assessment"),
    ("7",  "step07_benchmarks.py",       "Multi-Sensor Benchmarks (Hansen GFC & MOD44B)"),
    ("8a", "step08a_maps.py",            "Cartographic Production: 14 Atlas Maps (300 DPI)"),
    ("8b", "step08b_plots.py",           "Scientific Plots: Multi-Sensor Seaborn Figures"),
    ("8c", "step08c_tables.py",          "Statistical Compilation: Excel Workbook"),
    ("8d", "step08d_report.py",          "Doctoral Research Paper (.docx) in Times New Roman"),
    ("8e", "step08e_animations.py",      "Bi-Temporal Animated GIF Generation"),
    ("8f", "step08f_html_dashboard.py",  "Interactive HTML Research Dashboard"),
]

BANNER = r"""
================================================================================
   SOUTHERN KEBBI PhD REMOTE SENSING & GIS CARTOGRAPHIC PRODUCTION ENGINE
                 Kebbi State, Federal Republic of Nigeria
================================================================================
"""

def print_banner():
    print(BANNER)
    print(f"Project Working Directory: {BASE_DIR}")
    print(f"Python Environment:        {sys.executable}")
    print(f"Active Scripts Directory:  {SCRIPTS_DIR}")
    print("=" * 80 + "\n")

def run_step(step_id, script_name, description):
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"\n[ERROR] Pipeline script not found: {script_path}")
        return False

    print(f"\n{'=' * 80}")
    print(f">> [STEP {step_id.upper()}] {description.upper()}")
    print(f"  Script: scripts/pipeline/{script_name}")
    print(f"{'=' * 80}")

    t0 = time.time()
    cmd = [sys.executable, str(script_path)]
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"\n[FAILED] Step {step_id} failed with exit code {result.returncode} ({elapsed:.1f}s)")
        return False
    else:
        print(f"[SUCCESS] Step {step_id} finished in {elapsed:.1f}s")
        return True

def preflight_check():
    print("\n--- Performing Pre-Flight Environment & Data Verification ---")
    data_dir = BASE_DIR / "data"
    required_files = [
        "Kebbi_Landsat_2000.tif",
        "Kebbi_Landsat_2026.tif",
        "Kebbi_Hansen.tif",
        "Kebbi_WorldCover_2021.tif",
        "Kebbi_SRTM.tif",
        "Kebbi_LGAs.shp",
    ]
    missing = []
    for f in required_files:
        p = data_dir / f
        if not p.exists():
            missing.append(f)

    if missing:
        print(f"  [WARNING] Missing required input files in {data_dir}: {missing}")
        return False
    else:
        print(f"  [OK] All {len(required_files)} baseline core dataset files found in {data_dir.name}/.")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Southern Kebbi PhD Remote Sensing Master Pipeline Runner",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--all", action="store_true", help="Execute all pipeline steps sequentially (default)")
    parser.add_argument("--step", type=str, help="Execute a specific step (e.g. 1, 4, 8a, 8b, 8d)")
    parser.add_argument("--maps", action="store_true", help="Generate all 14 cartographic map plates (Step 8a)")
    parser.add_argument("--plots", action="store_true", help="Generate all scientific validation plots (Step 8b)")
    parser.add_argument("--tables", action="store_true", help="Generate Excel statistics workbook (Step 8c)")
    parser.add_argument("--report", action="store_true", help="Compile Word Dissertation Document (Step 8d)")
    parser.add_argument("--animations", "--gifs", dest="animations", action="store_true", help="Generate bi-temporal cartographic GIF animations (Step 8e)")
    parser.add_argument("--html", action="store_true", help="Compile Interactive HTML Research Dashboard (Step 8f)")
    parser.add_argument("--check", action="store_true", help="Pre-flight data and environment verification only")

    args = parser.parse_args()

    print_banner()

    if args.check:
        preflight_check()
        return

    # If no flags provided, default to running all steps
    if not (args.step or args.maps or args.plots or args.tables or args.report or args.animations or args.html or args.all):
        args.all = True

    preflight_check()

    t_start = time.time()

    if args.maps:
        success = run_step("8a", "step08a_maps.py", "Cartographic Production: 14 Atlas Maps")
    elif args.plots:
        success = run_step("8b", "step08b_plots.py", "Scientific Plots: Multi-Sensor Seaborn Figures")
    elif args.tables:
        success = run_step("8c", "step08c_tables.py", "Statistical Compilation: Excel Workbook")
    elif args.report:
        success = run_step("8d", "step08d_report.py", "Doctoral Research Paper (.docx) in Times New Roman")
    elif args.animations:
        success = run_step("8e", "step08e_animations.py", "Bi-Temporal Animated GIF Generation")
    elif args.html:
        success = run_step("8f", "step08f_html_dashboard.py", "Interactive HTML Research Dashboard")
    elif args.step:
        target = args.step.lower()
        matched = False
        for sid, sfile, sdesc in STEPS:
            if sid.lower() == target:
                success = run_step(sid, sfile, sdesc)
                matched = True
                break
        if not matched:
            print(f"Unknown step: {args.step}. Available steps: {[s[0] for s in STEPS]}")
            sys.exit(1)
    else: # Run all
        print("\nStarting full sequential execution of Southern Kebbi Research Pipeline...")
        for sid, sfile, sdesc in STEPS:
            ok = run_step(sid, sfile, sdesc)
            if not ok:
                print(f"\nPipeline halted due to error in Step {sid}.")
                sys.exit(1)
        success = True

    total_time = time.time() - t_start

    print("\n" + "=" * 80)
    print(">> ALL REQUESTED PROCESSING COMPLETE!")
    print(f"   Total Execution Time: {total_time/60.0:.2f} minutes ({total_time:.1f}s)")
    print("\nKey Deliverable Directories:")
    print(f"  - Cartographic Maps:  {BASE_DIR / 'outputs' / 'maps'}")
    print(f"  - Scientific Plots:   {BASE_DIR / 'outputs' / 'plots'}")
    print(f"  - Animated GIFs:      {BASE_DIR / 'outputs' / 'gifs'}")
    print(f"  - Master Statistics:  {BASE_DIR / 'outputs' / 'tables' / 'SouthernKebbi_statistics.xlsx'}")
    print(f"  - Word Dissertation:  {BASE_DIR / 'outputs' / 'reports' / 'Southern_Kebbi_PhD_Research_Paper.docx'}")
    print(f"  - Master HTML Viewer: {BASE_DIR / 'view_results.html'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
