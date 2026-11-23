#!/usr/bin/env bash
# ==============================================================================
# SOUTHERN KEBBI PhD REMOTE SENSING & GIS CARTOGRAPHIC PRODUCTION ENGINE
# Automated One-Click Runner for Linux / macOS / Unix Systems
# Doctoral Advisory Committee / Guide Execution Script
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=============================================================================="
echo "   SOUTHERN KEBBI PhD REMOTE SENSING RESEARCH PIPELINE (2000-2026)"
echo "             Automated One-Click Production & Evaluation Engine"
echo "=============================================================================="
echo "Working Directory: $SCRIPT_DIR"

# Detect Python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 was not found in PATH. Please install Python 3.9+."
    exit 1
fi

echo "Python Executable: $PY_CMD"
echo ""

# Optional dependency check
if [ -f "requirements.txt" ]; then
    if ! $PY_CMD -c "import rasterio, geopandas, matplotlib, seaborn, docx, openpyxl, sklearn" &>/dev/null; then
        echo "[NOTICE] Installing missing Python packages from requirements.txt..."
        $PY_CMD -m pip install -r requirements.txt
    fi
fi

# Execute main pipeline
$PY_CMD main.py "$@"

echo ""
echo "=============================================================================="
echo "Pipeline execution finished successfully."
echo "Outputs generated in:"
echo "  - Interactive HTML: view_results.html (Open in any web browser)"
echo "  - Maps:             outputs/maps/"
echo "  - Plots:            outputs/plots/"
echo "  - Animated GIFs:    outputs/gifs/"
echo "  - Tables:           outputs/tables/"
echo "  - Report:           outputs/reports/"
echo "=============================================================================="

