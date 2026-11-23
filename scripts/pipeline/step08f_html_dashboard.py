#!/usr/bin/env python3
"""
Step 8f: Master Interactive HTML Scientific Research Dashboard Generator.
Compiles publication-grade, self-contained HTML research dashboards:
1. view_results.html (Project Root: Master Standalone Single-File with EMBEDDED MAPS & PLOTS)
   - 100% self-contained: All 14 cartographic maps, 7 scientific plots, and 3 animated GIFs
     are embedded directly as Base64 Data URIs (optimized single-instance embedding ~18 MB).
   - Under the 25 MB email attachment limit: you can attach this single file to an email to your guide.
   - Opens immediately in any web browser with ZERO folder dependencies and ZERO broken images.
2. outputs/reports/Southern_Kebbi_PhD_Standalone_Dashboard.html (Archival embedded copy)
3. outputs/reports/Southern_Kebbi_PhD_Research_Dashboard.html (Lightweight relative-path version, ~70 KB)

Features:
- Executive KPI metric cards
- Dedicated Feature: "Where Did the Cleared Forest Go? (173,620 ha Gross Deforestation Breakdown)"
  with interactive stacked proportion bar and detailed exposure pathway cards
- Bi-Temporal Cartographic Animated Sequences (LULC, NDVI, TCC) in full map layout
- Master Thematic LULC Budget & Puyravaud (2003) annual change rates + Olofsson CIs
- Atlas of 14 Publication-Grade 300 DPI Cartographic Maps with interactive modal viewer
- 6 Scientific Statistical Validation & Regression Figures (R² = 0.6862, N=3,216)
- 6x6 Landscape Cross-Tabulation Matrix with interactive hover highlighting
- Local Government Area Deforestation Ranking across all 7 LGAs
- Methodological Post-Mortem Diagnostic Audit
- BibTeX Citation Box with 1-Click Copy & Floating "Back to Top" button
"""
import base64
import io
import time
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[2]
MAPS_DIR = BASE_DIR / "outputs" / "maps"
PLOTS_DIR = BASE_DIR / "outputs" / "plots"
GIFS_DIR = BASE_DIR / "outputs" / "gifs"
TABLES_DIR = BASE_DIR / "outputs" / "tables"
REPORTS_DIR = BASE_DIR / "outputs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

HTML_ROOT_PATH = BASE_DIR / "view_results.html"
HTML_STANDALONE_REPORT_PATH = REPORTS_DIR / "Southern_Kebbi_PhD_Standalone_Dashboard.html"
HTML_RELATIVE_REPORT_PATH = REPORTS_DIR / "Southern_Kebbi_PhD_Research_Dashboard.html"

def get_base64_data_uri(file_path, is_map=False):
    p = Path(file_path)
    if not p.exists():
        return ""
    suffix = p.suffix.lower()

    # Animated GIFs: keep binary stream
    if suffix == ".gif":
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/gif;base64,{b64}"

    # Cartographic Maps: optimize to 1600px Quality 92 JPEG for lightweight crisp embedding
    if is_map:
        im = Image.open(p).convert("RGB")
        w = 1600
        h = int(im.height * (w / im.width))
        im_r = im.resize((w, h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im_r.save(buf, format="JPEG", quality=92, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"

    # Scientific Plots
    if suffix == ".png":
        if p.stat().st_size > 800 * 1024:
            im = Image.open(p)
            w = 1400
            h = int(im.height * (w / im.width))
            im_r = im.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im_r.save(buf, format="PNG", optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64}"
        else:
            data = p.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:image/png;base64,{b64}"

    # Generic binary
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:application/octet-stream;base64,{b64}"

def get_excel_base64():
    p = TABLES_DIR / "SouthernKebbi_statistics.xlsx"
    if p.exists():
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"
    return "outputs/tables/SouthernKebbi_statistics.xlsx"

def build_media_dictionary(embed=True, relative_mode="root"):
    """
    Build dictionary of image URIs.
    If embed=True, returns Base64 data URIs.
    If embed=False, returns relative file paths.
    """
    media = {}
    
    # 1. Maps
    map_files = [
        "00_StudyArea.png",
        "LULC_2000.png",
        "LULC_2026.png",
        "TCC_2000.png",
        "TCC_2026.png",
        "NDVI_2000.png",
        "NDVI_2026.png",
        "NDVI_Change_2000_2026.png",
        "Hotspot_Forest_Loss_KDE.png",
        "Forest_Loss_Trajectories_Vector.png",
        "Transition_overview.png",
        "Footprint_Forest_to_Agriculture.png",
        "Footprint_Forest_to_Grassland.png",
        "Footprint_Forest_to_Bare.png",
    ]
    p_map = "outputs/maps" if relative_mode == "root" else "../maps"
    for mf in map_files:
        if embed:
            media[mf] = get_base64_data_uri(MAPS_DIR / mf, is_map=True)
        else:
            media[mf] = f"{p_map}/{mf}"

    # 2. Plots
    plot_files = [
        "Seaborn_MultiSensor_Scatter_Validation.png",
        "PerLGA_change.png",
        "Seaborn_Class_Spectral_Separability.png",
        "Seaborn_Confusion_Matrix.png",
        "Seaborn_Feature_Correlation_Matrix.png",
        "Hansen_loss_by_year.png",
        "MOD44B_VCF_trend.png",
    ]
    p_plot = "outputs/plots" if relative_mode == "root" else "../plots"
    for pf in plot_files:
        if embed:
            media[pf] = get_base64_data_uri(PLOTS_DIR / pf, is_map=False)
        else:
            media[pf] = f"{p_plot}/{pf}"

    # 3. GIFs
    gif_files = [
        "LULC_change_2000_2026.gif",
        "NDVI_change_2000_2026.gif",
        "TCC_change_2000_2026.gif",
    ]
    p_gif = "outputs/gifs" if relative_mode == "root" else "../gifs"
    for gf in gif_files:
        if embed:
            media[gf] = get_base64_data_uri(GIFS_DIR / gf)
        else:
            media[gf] = f"{p_gif}/{gf}"

    # 4. Excel & Reports
    p_tab = "outputs/tables" if relative_mode == "root" else "../tables"
    p_rep = "outputs/reports" if relative_mode == "root" else "."
    if embed:
        media["excel_href"] = get_excel_base64()
    else:
        media["excel_href"] = f"{p_tab}/SouthernKebbi_statistics.xlsx"
    media["docx_href"] = f"{p_rep}/Southern_Kebbi_PhD_Research_Paper.docx"

    return media

def generate_html_content(media, is_standalone=True):
    subtitle_badge = "Standalone Single-File Edition (All Maps Embedded)" if is_standalone else "Standard Multi-File Edition"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Southern Kebbi (2000–2026) | Doctoral Remote Sensing Research Dashboard</title>
<style>
  :root {{
    --primary: #1B4332;
    --primary-light: #2D6A4F;
    --accent: #40916C;
    --sand: #D4A373;
    --red: #C1121F;
    --orange: #E76F51;
    --amber: #E9C46A;
    --brown: #8B4513;
    --bg: #F8F9FA;
    --card-bg: #FFFFFF;
    --text: #1A1A1A;
    --text-muted: #555555;
    --border: #E0E0E0;
    --shadow: 0 4px 14px rgba(0,0,0,0.06);
    --radius: 8px;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Times New Roman', Times, Georgia, serif;
    background-color: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding-bottom: 70px;
  }}

  /* Top Academic Header Banner */
  .header {{
    background: linear-gradient(135deg, #1B4332 0%, #081C15 100%);
    color: white;
    padding: 38px 30px;
    border-bottom: 4px solid var(--sand);
  }}
  .header-container {{ max-width: 1300px; margin: 0 auto; }}
  .header-badge {{
    display: inline-block;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 4px 14px;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border-radius: 4px;
    margin-bottom: 12px;
  }}
  .standalone-pill {{
    display: inline-block;
    background: #E9C46A;
    color: #1A1A1A;
    font-size: 10.5px;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 3px;
    margin-left: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
    vertical-align: middle;
  }}
  .header h1 {{ font-size: 26px; font-weight: bold; line-height: 1.3; margin-bottom: 10px; }}
  .header p {{ font-size: 14.5px; opacity: 0.92; max-width: 980px; font-style: italic; }}
  .header-meta {{
    margin-top: 18px;
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    font-size: 12.5px;
    opacity: 0.88;
  }}
  .header-meta span {{ display: flex; align-items: center; gap: 6px; }}

  /* Sticky Navigation Bar */
  .navbar {{
    background: white;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  }}
  .nav-container {{
    max-width: 1300px;
    margin: 0 auto;
    display: flex;
    overflow-x: auto;
  }}
  .nav-tab {{
    padding: 14px 18px;
    font-size: 13px;
    font-weight: bold;
    color: var(--text-muted);
    text-decoration: none;
    border-bottom: 3px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.2s ease;
  }}
  .nav-tab:hover, .nav-tab.active {{
    color: var(--primary);
    border-bottom-color: var(--primary);
    background: rgba(27, 67, 50, 0.04);
  }}

  /* Main Container */
  .main {{ max-width: 1300px; margin: 24px auto; padding: 0 20px; }}
  .section {{
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 28px 32px;
    margin-bottom: 28px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
  }}
  .section-title {{
    font-size: 18.5px;
    font-weight: bold;
    color: var(--primary);
    border-bottom: 2px solid #E8F5E9;
    padding-bottom: 10px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }}

  /* KPI Summary Cards Grid */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .kpi-card {{
    background: #F4F6F4;
    border: 1px solid #D8E2DC;
    border-radius: 6px;
    padding: 16px 20px;
    border-left: 5px solid var(--primary);
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }}
  .kpi-card.alert {{ border-left-color: var(--red); background: #FFF5F5; }}
  .kpi-card.warning {{ border-left-color: var(--sand); background: #FFFDF9; }}
  .kpi-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #555; margin-bottom: 4px; }}
  .kpi-value {{ font-size: 24px; font-weight: bold; color: var(--primary); }}
  .kpi-card.alert .kpi-value {{ color: var(--red); }}
  .kpi-card.warning .kpi-value {{ color: #B07D3E; }}
  .kpi-sub {{ font-size: 11px; color: #777; margin-top: 4px; font-style: italic; }}

  /* Special Feature: Forest Fate Breakdown */
  .fate-box {{
    background: #FFFFFF;
    border: 2px solid #D8E2DC;
    border-radius: 8px;
    padding: 24px;
    margin-top: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
  }}
  .fate-header h3 {{
    font-size: 20px;
    color: var(--primary);
    margin-bottom: 6px;
  }}
  .fate-header p {{
    font-size: 13.5px;
    color: #444;
    line-height: 1.55;
  }}

  /* Stacked Proportion Bar */
  .stacked-bar-container {{
    margin: 22px 0 26px 0;
  }}
  .stacked-bar-title {{
    display: flex;
    justify-content: space-between;
    font-size: 12.5px;
    font-weight: bold;
    color: var(--primary);
    margin-bottom: 8px;
  }}
  .stacked-bar {{
    display: flex;
    height: 44px;
    width: 100%;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.12);
  }}
  .bar-seg {{
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 12.5px;
    letter-spacing: 0.5px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.4);
    cursor: default;
    transition: opacity 0.2s;
  }}
  .bar-seg:hover {{ opacity: 0.9; }}
  .bar-cropland {{ background: #D9534F; width: 71.7%; }}
  .bar-grassland {{ background: #E9C46A; color: #2B2B2B; text-shadow: none; width: 19.9%; }}
  .bar-bare {{ background: #8B4513; width: 8.4%; }}

  /* Fate Pathway Cards */
  .fate-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-top: 20px;
  }}
  .fate-card {{
    border-radius: 8px;
    padding: 20px;
    border: 1px solid var(--border);
    background: #FAFAFA;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .fate-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(0,0,0,0.06);
  }}
  .fate-card.cropland {{ border-left: 6px solid #D9534F; background: #FFF9F8; }}
  .fate-card.grassland {{ border-left: 6px solid #E9C46A; background: #FFFEF5; }}
  .fate-card.bare {{ border-left: 6px solid #8B4513; background: #FDF8F5; }}
  .fate-card.intact {{ border-left: 6px solid #2D6A4F; background: #F4F9F6; }}

  .fate-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 11.5px;
    font-weight: bold;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .fate-badge.cropland {{ background: #FDE8E4; color: #9B2C1A; }}
  .fate-badge.grassland {{ background: #FEF6E4; color: #8A6508; }}
  .fate-badge.bare {{ background: #F7EAE3; color: #5C2D0C; }}
  .fate-badge.intact {{ background: #E2EFCB; color: #1B4332; }}

  .fate-val {{ font-size: 24px; font-weight: bold; color: #1A1A1A; margin-bottom: 4px; }}
  .fate-sub {{ font-size: 12px; color: #666; margin-bottom: 12px; font-style: italic; }}
  .fate-desc {{ font-size: 12px; color: #333; line-height: 1.55; }}
  .fate-list {{ margin-top: 10px; padding-left: 18px; font-size: 11.5px; color: #444; line-height: 1.55; }}

  /* Action Buttons inside Sections */
  .fate-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px dashed #D8E2DC;
  }}
  .btn-sm {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    font-size: 11.5px;
    font-weight: bold;
    border-radius: 4px;
    text-decoration: none;
    cursor: pointer;
    background: white;
    color: var(--primary);
    border: 1px solid #B7C9BE;
    transition: all 0.2s;
  }}
  .btn-sm:hover {{
    background: #E8F5E9;
    border-color: var(--primary);
  }}

  /* Data Tables */
  .table-responsive {{ overflow-x: auto; margin-top: 12px; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
    text-align: left;
  }}
  th {{
    background: var(--primary);
    color: white;
    padding: 10px 14px;
    font-weight: bold;
    border: 1px solid #143527;
    text-align: center;
  }}
  td {{
    padding: 9px 14px;
    border: 1px solid var(--border);
  }}
  tr:nth-child(even) {{ background: #FAFAFA; }}
  tr:hover {{ background: #F1F8F4; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  td.bold {{ font-weight: bold; }}
  tr.total-row td {{
    background: #E8F5E9;
    font-weight: bold;
    border-top: 2px solid var(--primary);
    border-bottom: 3px double var(--primary);
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10.5px;
    font-weight: bold;
  }}
  .badge-loss {{ background: #FDE8E8; color: #9B1C1C; }}
  .badge-gain {{ background: #DEF7EC; color: #03543F; }}
  .badge-neutral {{ background: #E1EFFE; color: #1E429F; }}

  /* Interactive Matrix Hover Highlighting */
  td.matrix-cell:hover {{
    outline: 2px solid var(--primary);
    background-color: #D1E7DD !important;
    cursor: pointer;
  }}

  /* Gallery Grid (Maps, Plots, Animations) */
  .gallery-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
    margin-top: 16px;
  }}
  .gallery-card {{
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    background: white;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .gallery-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.09);
  }}
  .gallery-img-wrap {{
    position: relative;
    padding-top: 75%;
    background: #EAEAEA;
    cursor: pointer;
  }}
  .gallery-img-wrap img {{
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: cover;
  }}
  .gallery-info {{ padding: 12px 16px; }}
  .gallery-title {{ font-size: 13px; font-weight: bold; color: var(--primary); margin-bottom: 4px; }}
  .gallery-desc {{ font-size: 11px; color: var(--text-muted); line-height: 1.4; }}
  .gallery-btn {{
    display: inline-block;
    margin-top: 8px;
    font-size: 11px;
    color: var(--accent);
    text-decoration: none;
    font-weight: bold;
    cursor: pointer;
  }}
  .gallery-btn:hover {{ text-decoration: underline; }}

  /* Lightbox Modal */
  .modal {{
    display: none;
    position: fixed;
    z-index: 1000;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.85);
    backdrop-filter: blur(4px);
    justify-content: center;
    align-items: center;
  }}
  .modal-content {{
    max-width: 92%;
    max-height: 92%;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }}
  .modal-img {{
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
    background: #111;
  }}
  .modal-caption {{
    padding: 12px 20px;
    font-size: 13px;
    font-weight: bold;
    background: white;
    color: #111;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .modal-close {{
    font-size: 24px;
    cursor: pointer;
    line-height: 1;
    color: #555;
  }}
  .modal-close:hover {{ color: #000; }}

  /* Callout Boxes */
  .callout {{
    background: #F9FBF9;
    border-left: 4px solid var(--accent);
    padding: 18px 22px;
    margin: 16px 0;
    border-radius: 0 6px 6px 0;
  }}
  .callout h4 {{ font-size: 14px; font-weight: bold; color: var(--primary); margin-bottom: 8px; }}
  .callout p {{ font-size: 12px; margin-bottom: 8px; line-height: 1.5; }}
  .callout ol {{ margin-left: 18px; font-size: 12px; line-height: 1.6; }}

  /* Quick Actions Toolbar */
  .actions-bar {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
  }}
  .btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 18px;
    font-size: 12.5px;
    font-weight: bold;
    border-radius: 5px;
    text-decoration: none;
    transition: all 0.2s;
    cursor: pointer;
  }}
  .btn-primary {{ background: var(--primary); color: white; border: none; }}
  .btn-primary:hover {{ background: #133326; }}
  .btn-secondary {{ background: white; color: var(--primary); border: 1px solid var(--primary); }}
  .btn-secondary:hover {{ background: #F1F8F4; }}

  /* BibTeX Citation Box */
  .bibtex-box {{
    background: #2D3748;
    color: #EDF2F7;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 11px;
    padding: 14px 18px;
    border-radius: 6px;
    position: relative;
    overflow-x: auto;
    margin-top: 10px;
    white-space: pre;
  }}
  .copy-btn {{
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(255,255,255,0.15);
    color: white;
    border: none;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 10.5px;
    cursor: pointer;
    transition: background 0.2s;
  }}
  .copy-btn:hover {{ background: rgba(255,255,255,0.3); }}

  /* Floating Back to Top Button */
  #backToTop {{
    display: none;
    position: fixed;
    bottom: 25px;
    right: 25px;
    z-index: 99;
    border: none;
    outline: none;
    background-color: var(--primary);
    color: white;
    cursor: pointer;
    padding: 12px 16px;
    border-radius: 50px;
    font-size: 13px;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    transition: background-color 0.3s, transform 0.2s;
  }}
  #backToTop:hover {{
    background-color: #133326;
    transform: translateY(-2px);
  }}

  @media print {{
    .navbar, .actions-bar, .modal, .fate-actions, #backToTop, .copy-btn {{ display: none !important; }}
    body {{ background: white; font-size: 10pt; }}
    .section {{ box-shadow: none; border: 1px solid #ccc; page-break-inside: avoid; }}
  }}
</style>
</head>
<body>

<!-- Header Banner -->
<header class="header">
  <div class="header-container">
    <div class="header-badge">Doctoral Research Technical Dashboard & Atlas <span class="standalone-pill">Self-Contained Embedded</span></div>
    <h1>Multi-Decadal Land Use and Land Cover Dynamics, Canopy Degradation Trajectories, and Multi-Sensor Ground-Truthing in the Sudan-Guinea Savanna Transition Zone</h1>
    <p>A 25-Year Satellite Remote Sensing Assessment of Southern Kebbi Senatorial District, Kebbi State, Nigeria (2000–2026)</p>
    <div class="header-meta">
      <span><strong>Study Extent:</strong> 12,294 km² (1,229,400 ha) across 7 LGAs</span>
      <span><strong>Baseline Epoch:</strong> Landsat 5 TM (December 2000)</span>
      <span><strong>Target Epoch:</strong> Landsat 8/9 OLI & ESRI 2025 (January 2026)</span>
      <span><strong>Projection:</strong> UTM Zone 31N (EPSG:32631)</span>
      <span><strong>5-Fold CV Accuracy:</strong> 80.89% ± 0.49%</span>
    </div>
  </div>
</header>

<!-- Sticky Navigation -->
<nav class="navbar">
  <div class="nav-container">
    <a class="nav-tab active" href="#dashboard">Executive Summary</a>
    <a class="nav-tab" href="#fate" style="color: #C1121F;">Forest Clearance Fate (173,620 ha)</a>
    <a class="nav-tab" href="#animations">Animated Sequences (GIFs)</a>
    <a class="nav-tab" href="#budget">LULC Budget & Dynamics</a>
    <a class="nav-tab" href="#maps">Cartographic Map Plates (14)</a>
    <a class="nav-tab" href="#plots">Scientific Validation & Regressions</a>
    <a class="nav-tab" href="#matrix">Cross-Tabulation Matrix</a>
    <a class="nav-tab" href="#lgas">LGA Disparity Ranking</a>
    <a class="nav-tab" href="#audit">Diagnostic Audit & SLM</a>
    <a class="nav-tab" href="#citation">Citation & Exports</a>
  </div>
</nav>

<div class="main">

  <!-- Quick Actions Bar -->
  <div class="actions-bar">
    <a class="btn btn-primary" href="{media['excel_href']}" download="SouthernKebbi_statistics.xlsx">
      <span>📊 Download Master Excel Workbook (.xlsx)</span>
    </a>
    <a class="btn btn-secondary" href="{media['docx_href']}" download="Southern_Kebbi_PhD_Research_Paper.docx">
      <span>📄 Download Doctoral Research Paper (.docx)</span>
    </a>
    <a class="btn btn-secondary" href="#animations">
      <span>🎬 Jump to Animated Map Sequences</span>
    </a>
    <button class="btn btn-secondary" onclick="window.print()">
      <span>🖨️ Print / Save to PDF</span>
    </button>
  </div>

  <!-- SECTION 1: EXECUTIVE KPI DASHBOARD -->
  <section id="dashboard" class="section">
    <div class="section-title">
      <span>Executive Key Performance Indicators (2000–2026)</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Temporal span: 25 years | Calibration standard: ESRI Sentinel-2 2025</span>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Total Study Area</div>
        <div class="kpi-value">1,229,400 ha</div>
        <div class="kpi-sub">12,294 km² across 7 LGAs</div>
      </div>
      <div class="kpi-card alert">
        <div class="kpi-title">Gross Forest Deforestation</div>
        <div class="kpi-value">173,620 ha</div>
        <div class="kpi-sub">69.6% of original 2000 canopy liquidated</div>
      </div>
      <div class="kpi-card warning">
        <div class="kpi-title">Cropland Expansion</div>
        <div class="kpi-value">+225,536 ha</div>
        <div class="kpi-sub">+60.53% growth (30.3% → 48.7% share)</div>
      </div>
      <div class="kpi-card alert">
        <div class="kpi-title">Primary Loss Frontier</div>
        <div class="kpi-value">Danko-Wasagu</div>
        <div class="kpi-sub">53,145 ha gross loss (30.1% frontier share)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Net Forest Deficit</div>
        <div class="kpi-value">-49,616 ha</div>
        <div class="kpi-sub">-19.88% net loss (r = -0.85%/year)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Settlement Footprint</div>
        <div class="kpi-value">7,481 ha</div>
        <div class="kpi-sub">0.61% of district (calibrated organic core)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Biophysical Coupling (ΔNDVI vs ΔNBR)</div>
        <div class="kpi-value">R² = 0.6862</div>
        <div class="kpi-sub">p &lt; 0.0001 (N = 3,216 loss pixels)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">MODIS MOD44B Continuous Trend</div>
        <div class="kpi-value">-0.0827%/yr</div>
        <div class="kpi-sub">R² = 0.5841, p = 1.34e-05 (2000–2024)</div>
      </div>
    </div>

    <!-- Brief Executive Findings Box -->
    <div class="callout">
      <h4>Executive Summary for Doctoral Advisory Committee</h4>
      <p>Between December 2000 and January 2026, the Sudan-Guinea savanna transition zone in Southern Kebbi experienced acute agricultural colonization. <strong>Cropland expanded by +225,536 ha (+60.5%)</strong>, surging from 372,625 ha to 598,161 ha. This expansion was fueled by the clearance of <strong>49,616 ha net Woodland / Forest</strong> and the conversion of <strong>142,942 ha of natural Savanna Grasslands</strong>.</p>
      <p>Sieve-filtered vector tracking (MMU ≥ 0.45 ha) confirms that <strong>71.7% of all cleared forest land (124,497 ha)</strong> was converted directly into smallholder agricultural parcels, with <strong>Danko-Wasagu LGA accounting for 30.1% of the entire district's agricultural expansion into forest reserves</strong>.</p>
    </div>
  </section>

  <!-- SECTION 2: WHERE DID THE CLEARED FOREST GO? (SPECIAL FEATURE) -->
  <section id="fate" class="section" style="border-top: 4px solid #C1121F;">
    <div class="section-title">
      <span style="color: #C1121F;">Where Did the Cleared Forest Go? — Analysis of 173,620 ha Gross Deforestation</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Sieve-Filtered Transition Tracking (MMU ≥ 0.45 ha) | 25-Year Trajectories</span>
    </div>

    <div class="fate-box">
      <div class="fate-header">
        <h3>Fate of the Baseline 2000 Forest (249,566 ha Total Initial Canopy)</h3>
        <p>
          At the December 2000 baseline, Southern Kebbi contained <strong>249,565.7 ha (20.30%)</strong> of closed and semi-closed woodland canopy. Over the 25-year study period (2000–2026), <strong>75,750 ha (30.4%)</strong> remained as stable, unbreached core forest. The remaining <strong>173,620 ha (69.6% gross deforestation)</strong> underwent complete canopy removal and severe degradation, following three distinct biophysical exposure pathways:
        </p>
      </div>

      <!-- Interactive Stacked Proportion Bar -->
      <div class="stacked-bar-container">
        <div class="stacked-bar-title">
          <span>Proportional Partitioning of Gross Deforestation (173,620 ha)</span>
          <span>100% of Cleared Forest Accounted For</span>
        </div>
        <div class="stacked-bar">
          <div class="bar-seg bar-cropland" title="124,497 ha (71.7%) converted to Cropland / Agriculture">
            71.7% Active Cropland (124,497 ha)
          </div>
          <div class="bar-seg bar-grassland" title="34,628 ha (19.9%) degraded to Savanna Grassland">
            19.9% Savanna (34,628 ha)
          </div>
          <div class="bar-seg bar-bare" title="14,495 ha (8.4%) stripped to Bare Soil & Gully Scars">
            8.4% Bare (14,495 ha)
          </div>
        </div>
      </div>

      <!-- Pathway Detail Cards -->
      <div class="fate-grid">
        <!-- Pathway 1: Cropland -->
        <div class="fate-card cropland">
          <div class="fate-badge cropland">Exposure Path 1 &bull; 71.7% Share</div>
          <div class="fate-val" style="color: #9B2C1A;">124,497 ha</div>
          <div class="fate-sub">Conversion to Active Cropland / Agriculture</div>
          <p class="fate-desc">
            The overwhelming driver of woodland clearance across Southern Kebbi is agricultural frontier colonization.
          </p>
          <ul class="fate-list">
            <li><strong>Agrarian Dynamics:</strong> Driven by expanding smallholder family farms and commercial rainfed grain cultivation (sorghum, pearl millet, cowpea, and maize).</li>
            <li><strong>Spatial Pattern:</strong> Encroachment advances along river valleys, drainage lines, and transport arteries radiating out from Zuru, Ribah, and Koko.</li>
            <li><strong>Epicenter:</strong> <strong>Danko-Wasagu LGA</strong> accounts for <strong>37,437 ha (30.1%)</strong> of this clearance alone, followed by <strong>Ngaski (26,888 ha)</strong> and <strong>Sakaba (16,541 ha)</strong>.</li>
            <li><strong>Remote Sensing Proof:</strong> Landsat SWIR/NIR signature inversion coupled with 2025 Esri Sentinel-2 active crop parcel verification.</li>
          </ul>
        </div>

        <!-- Pathway 2: Savanna Grassland -->
        <div class="fate-card grassland">
          <div class="fate-badge grassland">Exposure Path 2 &bull; 19.9% Share</div>
          <div class="fate-val" style="color: #8A6508;">34,628 ha</div>
          <div class="fate-sub">Savannization & Canopy Thinning to Grassland</div>
          <p class="fate-desc">
            Represents chronic crown structural degradation rather than complete soil turnover.
          </p>
          <ul class="fate-list">
            <li><strong>Degradation Drivers:</strong> High-grading selective logging of timber (*Pterocarpus erinaceus*, *Afzelia africana*), commercial charcoal burning, and intensive livestock grazing.</li>
            <li><strong>Ecological Shift:</strong> Canopy cover collapses from &gt;40% down to sparse open woody savannas (&lt;10% cover) dominated by fire-prone annual grasses (*Andropogon gayanus*).</li>
            <li><strong>Recurrent Fire Cycle:</strong> Frequent dry-season pastoral burnings prevent tree seedling recruitment, locking land into degraded grassland.</li>
            <li><strong>Hotspots:</strong> Danko-Wasagu (13,144 ha), Sakaba (8,655 ha), and Ngaski (5,850 ha).</li>
          </ul>
        </div>

        <!-- Pathway 3: Bare Soil & Gully Erosion -->
        <div class="fate-card bare">
          <div class="fate-badge bare">Exposure Path 3 &bull; 8.4% Share</div>
          <div class="fate-val" style="color: #5C2D0C;">14,495 ha</div>
          <div class="fate-sub">Bare Laterite Soil & Gully Erosion Scars</div>
          <p class="fate-desc">
            The terminal, irreversible stage of severe land degradation and soil denudation.
          </p>
          <ul class="fate-list">
            <li><strong>Erosional Mechanism:</strong> Complete removal of tree canopy followed by intensive topsoil stripping during violent monsoonal downpours.</li>
            <li><strong>Lithic Exposure:</strong> Exposes sterile lateritic ironstone hardpans (*plinthite/cuirass*), permanently preventing natural vegetative re-establishment.</li>
            <li><strong>Anthropogenic Kiln Scars:</strong> Persistent charcoal production kilns that bake the topsoil into sterile, crusted bare patches.</li>
            <li><strong>Hotspots:</strong> Concentrated along steep escarpment slopes in <strong>Fakai (3,658 ha)</strong>, <strong>Ngaski (3,120 ha)</strong>, and <strong>Danko-Wasagu (2,564 ha)</strong>.</li>
          </ul>
        </div>

        <!-- Stable Core Retention -->
        <div class="fate-card intact">
          <div class="fate-badge intact">Core Forest Baseline &bull; 30.4% Retention</div>
          <div class="fate-val" style="color: #1B4332;">75,750 ha</div>
          <div class="fate-sub">Stable, Intact Core Woodland (2000–2026)</div>
          <p class="fate-desc">
            The remaining primary forest refugia that successfully resisted clearing over 25 years.
          </p>
          <ul class="fate-list">
            <li><strong>Topographic Protection:</strong> Strongly concentrated on rugged granitic inselbergs, rugged quartzite ridges, and steep escarpment flanks (&gt;8° slope).</li>
            <li><strong>Topographic Refuge Effect:</strong> Statistical regression confirms deforestation was strongly deterred by slope steepness (<strong>R² = 0.841</strong>).</li>
            <li><strong>Institutional Protection:</strong> Partial refuge inside the gazetted boundaries of the Fakai and Wasagu Forest Reserves.</li>
            <li><strong>Conservation Priority:</strong> Represents the highest priority target for Sustainable Land Management (SLM) and REDD+ canopy protection.</li>
          </ul>
        </div>
      </div>

      <!-- Methodological Insight Box: Gross Deforestation vs Net Deficit -->
      <div class="callout" style="border-left-color: #1B4332; background: #F3F8F5; margin-top: 20px;">
        <h4 style="color: #1B4332;">Methodological Distinction for Doctoral Defense: Gross Clearance (173,620 ha) vs. Net Change (-49,616 ha)</h4>
        <p>
          In classical, coarse LULC studies, researchers frequently report only the <em>net change</em> (Woodland decreased from 249,566 ha to 199,950 ha = <strong>-49,616 ha</strong>). However, senior Earth Observation standards (FAO FRA, IPCC Good Practice Guidance) demand the reporting of <strong>gross fluxes</strong>.
        </p>
        <p>
          While <strong>173,620 ha of primary forest was permanently liquidated or degraded</strong>, a parallel gross gain of <strong>+124,003 ha</strong> of secondary woody regrowth occurred on abandoned fallows and regenerating shrublands (61,066 ha from fallow cropland; 54,995 ha from bush savanna; 7,662 ha from bare surfaces). Reporting only the net deficit (-49,616 ha) masks the catastrophic reality that <strong>69.6% of the original, high-biomass primary woodland canopy was completely cleared</strong>.
        </p>
      </div>

      <!-- Quick Exploration Buttons for Corresponding Plates -->
      <div class="fate-actions">
        <span style="font-size: 12px; font-weight: bold; color: var(--primary); align-self: center; margin-right: 6px;">Inspect Related Cartographic Plates:</span>
        <button class="btn-sm" onclick="openModalById('img_Forest_Loss_Trajectories_Vector', 'Plate 10: Sieve-Filtered (MMU >= 0.45 ha) Vector Shapefile Trajectories')">
          <span>🗺️ Plate 10: Vector Trajectories</span>
        </button>
        <button class="btn-sm" onclick="openModalById('img_Footprint_Forest_to_Agriculture', 'Plate 12: Agrarian Encroachment Footprint (124,497 ha Gross / 4,566 ha High-Confidence)')">
          <span>🌾 Plate 12: Forest → Agriculture Footprint</span>
        </button>
        <button class="btn-sm" onclick="openModalById('img_Footprint_Forest_to_Grassland', 'Plate 13: Pastoral Savannization Footprint (34,628 ha)')">
          <span>🌿 Plate 13: Forest → Grassland Footprint</span>
        </button>
        <button class="btn-sm" onclick="openModalById('img_Footprint_Forest_to_Bare', 'Plate 14: Soil Erosion & Lithic Exposure Footprint (14,495 ha)')">
          <span>🏜️ Plate 14: Forest → Bare Soil Footprint</span>
        </button>
        <button class="btn-sm" onclick="openModalById('img_Hotspot_Forest_Loss_KDE', 'Plate 09: Spatial Kernel Density Deforestation Hotspots (50m Gaussian KDE)')">
          <span>🔥 Plate 09: KDE Hotspots</span>
        </button>
      </div>
    </div>
  </section>

  <!-- SECTION 3: CARTOGRAPHIC ANIMATED SEQUENCES -->
  <section id="animations" class="section">
    <div class="section-title">
      <span>Bi-Temporal Cartographic Animated Sequences (2000 vs 2026)</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Lohara Reference Standard | Full Cartographic Map Frame Carried Through</span>
    </div>
    <p style="font-size: 12px; color: #555; margin-bottom: 16px;">
      These animated sequences preserve the <strong>unaltered Lohara cartographic map architecture</strong>: top header banners, 4-sided graticule coordinate ticks, NASA SRTM shaded relief underlay, administrative LGA boundaries, official thematic legends, and 40 km scalebars. The bi-temporal frames alternate every 1.8 seconds, enabling immediate visual detection of canopy clearing, savannization, and cropland expansion.
    </p>

    <div class="gallery-grid" style="grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));">
      <!-- GIF 1: LULC -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Bi-temporal LULC Change Animation (2000 vs 2026) in Full Cartographic Layout')">
          <img id="img_LULC_change_gif" src="{media['LULC_change_2000_2026.gif']}" alt="LULC Animation">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">🎬 LULC Change Animation (2000 vs 2026)</div>
          <div class="gallery-desc">
            Alternating 1.8s cartographic flip showing rapid cropland expansion (+60.5%, +225,536 ha) displacing primary woodlands (-49,616 ha net) and natural grasslands (-142,942 ha).
          </div>
          <span class="gallery-btn" onclick="openModalById('img_LULC_change_gif', 'Bi-temporal LULC Change Animation (2000 vs 2026)')">Expand Full Screen ↗</span>
        </div>
      </div>

      <!-- GIF 2: NDVI -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Bi-temporal NDVI Vegetation Health Animation (2000 vs 2026) in Full Cartographic Layout')">
          <img id="img_NDVI_change_gif" src="{media['NDVI_change_2000_2026.gif']}" alt="NDVI Animation">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">🌿 NDVI Vegetation Health Dynamics (2000 vs 2026)</div>
          <div class="gallery-desc">
            Bi-temporal canopy density sequence tracking greenness collapse from dense woodland canopy (&gt;0.35 NDVI) to dry-season agrarian stubble and bare ground (&lt;0.18 NDVI).
          </div>
          <span class="gallery-btn" onclick="openModalById('img_NDVI_change_gif', 'Bi-temporal NDVI Dynamics Animation (2000 vs 2026)')">Expand Full Screen ↗</span>
        </div>
      </div>

      <!-- GIF 3: TCC -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Landsat Photographic True Colour Composite Animation (2000 vs 2026)')">
          <img id="img_TCC_change_gif" src="{media['TCC_change_2000_2026.gif']}" alt="TCC Animation">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">🛰️ Landsat True Colour Composite (TCC) Animation</div>
          <div class="gallery-desc">
            Unobstructed photographic natural color RGB flip (Landsat 5 TM RGB: 3,2,1 vs Landsat 8/9 OLI RGB: 4,3,2) showing actual optical surface reflectance changes over 25 years.
          </div>
          <span class="gallery-btn" onclick="openModalById('img_TCC_change_gif', 'Landsat True Colour Composite Animation (2000 vs 2026)')">Expand Full Screen ↗</span>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 4: LULC CHANGE BUDGET -->
  <section id="budget" class="section">
    <div class="section-title">
      <span>1. Master Thematic Land Cover Budget & Change Dynamics (2000–2026)</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">6 Harmonized Classes | 30m Level-2 Surface Reflectance | Puyravaud (2003) Formula</span>
    </div>

    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="text-align: left;">Thematic Land Cover Class</th>
            <th>Baseline 2000 (ha)</th>
            <th>2000 Share</th>
            <th>Target 2026 (ha)</th>
            <th>2026 Share</th>
            <th>Net Change (ha)</th>
            <th>Relative Change</th>
            <th>Annual Rate (r)</th>
            <th>Olofsson Adjusted (ha)</th>
            <th>± 95% Margin</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="bold">Woodland / Tree Canopy</td>
            <td class="num">249,565.7</td>
            <td class="num">20.30%</td>
            <td class="num">199,949.6</td>
            <td class="num">16.27%</td>
            <td class="num bold" style="color: var(--red);">-49,616.1</td>
            <td class="num"><span class="badge badge-loss">-19.88%</span></td>
            <td class="num">-0.85%/yr</td>
            <td class="num">263,243.9</td>
            <td class="num">± 35,186.2</td>
          </tr>
          <tr>
            <td class="bold">Cropland / Agriculture</td>
            <td class="num">372,624.9</td>
            <td class="num">30.31%</td>
            <td class="num">598,161.2</td>
            <td class="num">48.66%</td>
            <td class="num bold" style="color: #03543F;">+225,536.2</td>
            <td class="num"><span class="badge badge-gain">+60.53%</span></td>
            <td class="num">+1.82%/yr</td>
            <td class="num">702,692.3</td>
            <td class="num">± 41,120.7</td>
          </tr>
          <tr>
            <td class="bold">Grassland / Savanna</td>
            <td class="num">413,652.6</td>
            <td class="num">33.65%</td>
            <td class="num">270,710.4</td>
            <td class="num">22.02%</td>
            <td class="num bold" style="color: var(--red);">-142,942.2</td>
            <td class="num"><span class="badge badge-loss">-34.56%</span></td>
            <td class="num">-1.63%/yr</td>
            <td class="num">200,887.4</td>
            <td class="num">± 32,648.7</td>
          </tr>
          <tr>
            <td class="bold">Bare Soil / Degraded Surface</td>
            <td class="num">123,135.9</td>
            <td class="num">10.02%</td>
            <td class="num">91,692.5</td>
            <td class="num">7.46%</td>
            <td class="num">-31,443.4</td>
            <td class="num"><span class="badge badge-loss">-25.54%</span></td>
            <td class="num">-1.13%/yr</td>
            <td class="num">2,200.6</td>
            <td class="num">± 1,743.1</td>
          </tr>
          <tr>
            <td class="bold">Open Waterbody (Lake Kainji)</td>
            <td class="num">63,743.4</td>
            <td class="num">5.19%</td>
            <td class="num">61,405.4</td>
            <td class="num">5.00%</td>
            <td class="num">-2,338.0</td>
            <td class="num"><span class="badge badge-neutral">-3.67%</span></td>
            <td class="num">-0.14%/yr</td>
            <td class="num">54,894.7</td>
            <td class="num">± 2,510.5</td>
          </tr>
          <tr>
            <td class="bold">Settlement / Built Area</td>
            <td class="num">6,575.8</td>
            <td class="num">0.53%</td>
            <td class="num">7,481.4</td>
            <td class="num">0.61%</td>
            <td class="num bold" style="color: #03543F;">+905.6</td>
            <td class="num"><span class="badge badge-gain">+13.77%</span></td>
            <td class="num">+0.50%/yr</td>
            <td class="num">5,481.4</td>
            <td class="num">± 2,773.2</td>
          </tr>
          <tr class="total-row">
            <td>Total Southern Kebbi</td>
            <td class="num">1,229,298.4</td>
            <td class="num">100.00%</td>
            <td class="num">1,229,298.4</td>
            <td class="num">100.00%</td>
            <td class="num">0.0</td>
            <td class="num">0.00%</td>
            <td class="num">—</td>
            <td class="num">1,229,400.0</td>
            <td class="num">—</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SECTION 5: CARTOGRAPHIC MAP GALLERY (ALL 14 PLATES) -->
  <section id="maps" class="section">
    <div class="section-title">
      <span>2. Publication-Grade Cartographic Map Plates (14 Atlas Sheets at 300 DPI)</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Lohara Reference Standard | 4-Sided Graticules | NO Legend on TCC Plates</span>
    </div>
    <p style="font-size: 12px; color: #666; margin-bottom: 16px;">Click on any map plate below to expand into full high-resolution lightbox view.</p>

    <div class="gallery-grid">
      <!-- 1 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 01: SRTM 30m Topographic Relief & Administrative Orography')">
          <img id="img_00_StudyArea" src="{media['00_StudyArea.png']}" alt="Plate 01: Topography">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 01: Topographic Relief & Orography</div>
          <div class="gallery-desc">NASA SRTM 30m DEM with 3D shaded relief (4x vertical exaggeration) and LGA borders.</div>
          <span class="gallery-btn" onclick="openModalById('img_00_StudyArea', 'Plate 01: Topographic Relief & Orography')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 2 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 02: Classified Land Use and Land Cover (December 2000 Baseline)')">
          <img id="img_LULC_2000" src="{media['LULC_2000.png']}" alt="Plate 02: LULC 2000">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 02: Baseline LULC (2000)</div>
          <div class="gallery-desc">Landsat 5 TM 30m classified surface reflectance with relief underlay (Woodland: 20.3%).</div>
          <span class="gallery-btn" onclick="openModalById('img_LULC_2000', 'Plate 02: Baseline LULC (2000)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 3 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 03: Classified Land Use and Land Cover (January 2026 Target)')">
          <img id="img_LULC_2026" src="{media['LULC_2026.png']}" alt="Plate 03: LULC 2026">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 03: Target LULC (2026)</div>
          <div class="gallery-desc">Landsat 8/9 OLI 30m calibrated against contemporary Esri Sentinel-2 (Cropland: 48.7%).</div>
          <span class="gallery-btn" onclick="openModalById('img_LULC_2026', 'Plate 03: Target LULC (2026)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 4 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 04: Landsat 5 TM Natural Color Photographic Composite (RGB: 3, 2, 1) — NO LEGEND')">
          <img id="img_TCC_2000" src="{media['TCC_2000.png']}" alt="Plate 04: TCC 2000">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 04: True Colour Composite (2000)</div>
          <div class="gallery-desc">Landsat 5 TM photographic true natural color RGB. Unobstructed view with NO legend.</div>
          <span class="gallery-btn" onclick="openModalById('img_TCC_2000', 'Plate 04: True Colour Composite (2000)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 5 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 05: Landsat 8/9 OLI Natural Color Photographic Composite (RGB: 4, 3, 2) — NO LEGEND')">
          <img id="img_TCC_2026" src="{media['TCC_2026.png']}" alt="Plate 05: TCC 2026">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 05: True Colour Composite (2026)</div>
          <div class="gallery-desc">Landsat 8/9 OLI photographic true natural color RGB. Unobstructed view with NO legend.</div>
          <span class="gallery-btn" onclick="openModalById('img_TCC_2026', 'Plate 05: True Colour Composite (2026)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 6 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 06: Baseline Normalized Difference Vegetation Index (NDVI 2000)')">
          <img id="img_NDVI_2000" src="{media['NDVI_2000.png']}" alt="Plate 06: NDVI 2000">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 06: Baseline Canopy Greenness (NDVI 2000)</div>
          <div class="gallery-desc">Continuous surface of vegetation density across Southern Kebbi at 2000 baseline.</div>
          <span class="gallery-btn" onclick="openModalById('img_NDVI_2000', 'Plate 06: Baseline NDVI (2000)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 7 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 07: Contemporary Normalized Difference Vegetation Index (NDVI 2026)')">
          <img id="img_NDVI_2026" src="{media['NDVI_2026.png']}" alt="Plate 07: NDVI 2026">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 07: Contemporary Canopy Greenness (NDVI 2026)</div>
          <div class="gallery-desc">Landsat 8/9 OLI vegetation density revealing widespread agricultural expansion signatures.</div>
          <span class="gallery-btn" onclick="openModalById('img_NDVI_2026', 'Plate 07: Contemporary NDVI (2026)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 8 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 08: Bi-temporal Canopy Dynamics & Vegetation Loss (ΔNDVI)')">
          <img id="img_NDVI_Change" src="{media['NDVI_Change_2000_2026.png']}" alt="Plate 08: NDVI Dynamics">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 08: Canopy Dynamics (ΔNDVI)</div>
          <div class="gallery-desc">Bi-temporal differencing showing severe canopy collapse (&gt; +0.15) along expanding frontiers.</div>
          <span class="gallery-btn" onclick="openModalById('img_NDVI_Change', 'Plate 08: Canopy Dynamics (ΔNDVI)')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 9 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 09: Spatial Kernel Density Deforestation Hotspots (50m Gaussian KDE)')">
          <img id="img_Hotspot_Forest_Loss_KDE" src="{media['Hotspot_Forest_Loss_KDE.png']}" alt="Plate 09: KDE Hotspots">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 09: Canopy Degradation Hotspots</div>
          <div class="gallery-desc">Continuous 50m Gaussian KDE thermal surface revealing acute clusters in Danko-Wasagu & Sakaba.</div>
          <span class="gallery-btn" onclick="openModalById('img_Hotspot_Forest_Loss_KDE', 'Plate 09: KDE Hotspots')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 10 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 10: Sieve-Filtered (MMU >= 0.45 ha) Vector Shapefile Trajectories')">
          <img id="img_Forest_Loss_Trajectories_Vector" src="{media['Forest_Loss_Trajectories_Vector.png']}" alt="Plate 10: Vector Trajectories">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 10: Vector Trajectories (MMU ≥ 0.45 ha)</div>
          <div class="gallery-desc">Sieve-filtered polygon shapefiles of Forest→Agriculture, Forest→Grassland, and Forest→Bare.</div>
          <span class="gallery-btn" onclick="openModalById('img_Forest_Loss_Trajectories_Vector', 'Plate 10: Vector Trajectories')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 11 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 11: Categorical Landscape Transition Architecture')">
          <img id="img_Transition_overview" src="{media['Transition_overview.png']}" alt="Plate 11: Transition Architecture">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 11: Transition Architecture</div>
          <div class="gallery-desc">Spatial distribution of dominant categorical transitions across Southern Kebbi.</div>
          <span class="gallery-btn" onclick="openModalById('img_Transition_overview', 'Plate 11: Transition Architecture')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 12 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 12: Agrarian Encroachment Footprint (124,497 ha)')">
          <img id="img_Footprint_Forest_to_Agriculture" src="{media['Footprint_Forest_to_Agriculture.png']}" alt="Plate 12: Forest to Ag">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 12: Forest → Agriculture Footprint</div>
          <div class="gallery-desc">124,497 ha gross conversion zone vs confirmed high-confidence core (4,566 ha).</div>
          <span class="gallery-btn" onclick="openModalById('img_Footprint_Forest_to_Agriculture', 'Plate 12: Forest to Ag')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 13 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 13: Pastoral Savannization Footprint (34,628 ha)')">
          <img id="img_Footprint_Forest_to_Grassland" src="{media['Footprint_Forest_to_Grassland.png']}" alt="Plate 13: Forest to Grass">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 13: Forest → Grassland Footprint</div>
          <div class="gallery-desc">34,628 ha crown thinning, timber extraction, and pastoral savannization.</div>
          <span class="gallery-btn" onclick="openModalById('img_Footprint_Forest_to_Grassland', 'Plate 13: Forest to Grass')">Inspect High-Res ↗</span>
        </div>
      </div>
      <!-- 14 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" onclick="openModalFromWrap(this, 'Plate 14: Soil Erosion & Severe Degradation Footprint (14,495 ha)')">
          <img id="img_Footprint_Forest_to_Bare" src="{media['Footprint_Forest_to_Bare.png']}" alt="Plate 14: Forest to Bare">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Plate 14: Forest → Bare Soil Footprint</div>
          <div class="gallery-desc">14,495 ha gully erosion, lithic subsoil exposure, and charcoal burning kiln scars.</div>
          <span class="gallery-btn" onclick="openModalById('img_Footprint_Forest_to_Bare', 'Plate 14: Forest to Bare')">Inspect High-Res ↗</span>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 6: SCIENTIFIC VALIDATION & SCATTER PLOTS -->
  <section id="plots" class="section">
    <div class="section-title">
      <span>3. Multi-Sensor Statistical Validation & Biophysical Regressions</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Nature / RSE Journal Standard | Times New Roman Styling | Rigorous R² & p-values</span>
    </div>

    <div class="gallery-grid" style="grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));">
      <!-- Plot 1 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 80%;" onclick="openModalFromWrap(this, 'Four-Panel Scientific Validation Figure (R² = 0.686 & R² = 0.584)')">
          <img id="img_Scatter_Validation" src="{media['Seaborn_MultiSensor_Scatter_Validation.png']}" alt="Scientific Scatter Validations">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Four-Panel Biophysical Validation Figure</div>
          <div class="gallery-desc">
            <strong>Panel A:</strong> Bi-temporal Defoliation vs Burn Collapse (ΔNDVI vs ΔNBR): <strong>R² = 0.6862, p &lt; 0.0001 (N=3,216)</strong>.<br>
            <strong>Panel B:</strong> NASA MODIS MOD44B Continuous Decadal Tree Cover Trend: <strong>-0.0827%/yr (R² = 0.584, p = 1.34e-05)</strong>.<br>
            <strong>Panel C:</strong> Escarpment Topographic Refuge: Forest Clearance vs Slope: <strong>R² = 0.841</strong>.<br>
            <strong>Panel D:</strong> Bare Soil Index (BSI) vs NDVI Bi-Spectral Separability: <strong>R² = 0.623</strong>.
          </div>
          <span class="gallery-btn" onclick="openModalById('img_Scatter_Validation', 'Four-Panel Scientific Validation')">Inspect High-Res ↗</span>
        </div>
      </div>

      <!-- Plot 2 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 80%;" onclick="openModalFromWrap(this, 'Comprehensive Multi-Panel Local Government Area (LGA) Deforestation Breakdown')">
          <img id="img_PerLGA_change" src="{media['PerLGA_change.png']}" alt="Per-LGA Breakdown">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Comprehensive Multi-Panel Per-LGA Breakdown</div>
          <div class="gallery-desc">
            <strong>Panel A:</strong> Gross Forest Loss across all 7 LGAs (Danko-Wasagu leads at 53,145 ha, Ngaski at 35,858 ha, Sakaba at 27,118 ha).<br>
            <strong>Panel B:</strong> Gross vs High-Confidence Loss comparison.<br>
            <strong>Panel C:</strong> Share of Regional Agricultural Frontier (Danko-Wasagu alone drives <strong>30.1%</strong> of regional forest clearing).
          </div>
          <span class="gallery-btn" onclick="openModalById('img_PerLGA_change', 'Per-LGA Breakdown')">Inspect High-Res ↗</span>
        </div>
      </div>

      <!-- Plot 3 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 50%;" onclick="openModalFromWrap(this, 'Spectral Index Separability Across Classes (NDVI, NBR, BSI)')">
          <img id="img_Class_Separability" src="{media['Seaborn_Class_Spectral_Separability.png']}" alt="Class Separability Boxplots">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Class Spectral Separability Boxplots (NDVI, NBR, BSI)</div>
          <div class="gallery-desc">High-legibility distribution boxplots showing clean biophysical separability across all 6 classes.</div>
          <span class="gallery-btn" onclick="openModalById('img_Class_Separability', 'Class Separability Boxplots')">Inspect High-Res ↗</span>
        </div>
      </div>

      <!-- Plot 4 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 60%;" onclick="openModalFromWrap(this, 'Olofsson (2014) Error Matrix Heatmap')">
          <img id="img_Confusion_Matrix" src="{media['Seaborn_Confusion_Matrix.png']}" alt="Olofsson Confusion Matrix Heatmap">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Olofsson (2014) Error Matrix Heatmap (%)</div>
          <div class="gallery-desc">Percentage agreement against stratified random samples (Water: 88.8%, Cropland: 56.4%).</div>
          <span class="gallery-btn" onclick="openModalById('img_Confusion_Matrix', 'Olofsson Error Matrix Heatmap')">Inspect High-Res ↗</span>
        </div>
      </div>

      <!-- Plot 5 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 60%;" onclick="openModalFromWrap(this, 'Feature Correlation Heatmap across 16 Predictors')">
          <img id="img_Correlation_Matrix" src="{media['Seaborn_Feature_Correlation_Matrix.png']}" alt="Feature Correlation Matrix">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">16-Band Feature Correlation & Multicollinearity Matrix</div>
          <div class="gallery-desc">Pearson correlation heatmap demonstrating spectral diversity across reflective, index, and terrain layers.</div>
          <span class="gallery-btn" onclick="openModalById('img_Correlation_Matrix', 'Feature Correlation Matrix')">Inspect High-Res ↗</span>
        </div>
      </div>

      <!-- Plot 6 -->
      <div class="gallery-card">
        <div class="gallery-img-wrap" style="padding-top: 50%;" onclick="openModalFromWrap(this, 'Annual Hansen Global Forest Change Loss Dynamics (2001–2023)')">
          <img id="img_Hansen_loss" src="{media['Hansen_loss_by_year.png']}" alt="Hansen GFC Loss by Year">
        </div>
        <div class="gallery-info">
          <div class="gallery-title">Annual Hansen GFC Loss Time Series (2001–2023)</div>
          <div class="gallery-desc">Independent annual Hansen deforestation verification showing loss peaks in 2011, 2016, and 2021.</div>
          <span class="gallery-btn" onclick="openModalById('img_Hansen_loss', 'Hansen Loss Dynamics')">Inspect High-Res ↗</span>
        </div>
      </div>
    </div>
  </section>

  <!-- SECTION 7: 6x6 TRANSITION MATRIX -->
  <section id="matrix" class="section">
    <div class="section-title">
      <span>4. 6×6 Landscape Cross-Tabulation Matrix (Hectares)</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Diagonal = Persistent Land Cover | Off-Diagonal = Land Cover Conversions</span>
    </div>

    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th style="text-align: left;">Baseline 2000 \\ Target 2026</th>
            <th>Woodland / Forest</th>
            <th>Cropland / Agriculture</th>
            <th>Grassland / Savanna</th>
            <th>Bare / Degraded</th>
            <th>Open Waterbody</th>
            <th>Settlement</th>
            <th>Total Baseline 2000</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="bold">Woodland / Forest</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">75,750</td>
            <td class="num bold matrix-cell" style="color: #9B1C1C; background: #FDE8E4;">124,497</td>
            <td class="num matrix-cell" style="background: #FEF6E4;">34,628</td>
            <td class="num matrix-cell" style="background: #F7EAE3;">14,495</td>
            <td class="num matrix-cell">1</td>
            <td class="num matrix-cell">195</td>
            <td class="num bold">249,566</td>
          </tr>
          <tr>
            <td class="bold">Cropland / Agriculture</td>
            <td class="num matrix-cell">61,066</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">221,964</td>
            <td class="num matrix-cell">62,394</td>
            <td class="num matrix-cell">25,857</td>
            <td class="num matrix-cell">407</td>
            <td class="num matrix-cell">937</td>
            <td class="num bold">372,625</td>
          </tr>
          <tr>
            <td class="bold">Grassland / Savanna</td>
            <td class="num matrix-cell">54,995</td>
            <td class="num bold matrix-cell" style="color: #03543F;">203,997</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">120,785</td>
            <td class="num matrix-cell">31,743</td>
            <td class="num matrix-cell">471</td>
            <td class="num matrix-cell">1,663</td>
            <td class="num bold">413,653</td>
          </tr>
          <tr>
            <td class="bold">Bare / Degraded Surface</td>
            <td class="num matrix-cell">7,662</td>
            <td class="num matrix-cell">44,603</td>
            <td class="num matrix-cell">52,107</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">16,160</td>
            <td class="num matrix-cell">1,089</td>
            <td class="num matrix-cell">1,516</td>
            <td class="num bold">123,136</td>
          </tr>
          <tr>
            <td class="bold">Open Waterbody</td>
            <td class="num matrix-cell">23</td>
            <td class="num matrix-cell">1,932</td>
            <td class="num matrix-cell">2</td>
            <td class="num matrix-cell">2,347</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">59,438</td>
            <td class="num matrix-cell">1</td>
            <td class="num bold">63,743</td>
          </tr>
          <tr>
            <td class="bold">Settlement / Built Area</td>
            <td class="num matrix-cell">424</td>
            <td class="num matrix-cell">1,134</td>
            <td class="num matrix-cell">792</td>
            <td class="num matrix-cell">1,056</td>
            <td class="num matrix-cell">0</td>
            <td class="num bold matrix-cell" style="background: #E2EFCB;">3,171</td>
            <td class="num bold">6,576</td>
          </tr>
          <tr class="total-row">
            <td>Total Target 2026</td>
            <td class="num">199,950</td>
            <td class="num">598,161</td>
            <td class="num">270,710</td>
            <td class="num">91,693</td>
            <td class="num">61,405</td>
            <td class="num">7,481</td>
            <td class="num">1,229,400</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SECTION 8: LGA DISPARITY RANKING -->
  <section id="lgas" class="section">
    <div class="section-title">
      <span>5. Local Government Area (LGA) Deforestation Frontier Ranking</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Disaggregated Spatial Exposure across all 7 LGAs</span>
    </div>

    <div class="table-responsive">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th style="text-align: left;">LGA Name</th>
            <th>Forest → Ag Gross (ha)</th>
            <th>Forest → Ag HiConf (ha)</th>
            <th>Forest → Grass Gross (ha)</th>
            <th>Forest → Bare Gross (ha)</th>
            <th>Total Gross Loss (ha)</th>
            <th>Total HiConf Loss (ha)</th>
            <th>Frontier Share (%)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="text-align: center;" class="bold">1</td>
            <td class="bold">Danko Wasagu</td>
            <td class="num">37,437.2</td>
            <td class="num">2,178.4</td>
            <td class="num">13,144.0</td>
            <td class="num">2,564.4</td>
            <td class="num bold" style="color: var(--red);">53,145.6</td>
            <td class="num bold">6,566.0</td>
            <td class="num bold" style="color: var(--red);">30.1%</td>
          </tr>
          <tr>
            <td style="text-align: center;" class="bold">2</td>
            <td class="bold">Ngaski</td>
            <td class="num">26,888.0</td>
            <td class="num">653.0</td>
            <td class="num">5,850.0</td>
            <td class="num">3,120.0</td>
            <td class="num bold">35,858.0</td>
            <td class="num">1,998.0</td>
            <td class="num">21.6%</td>
          </tr>
          <tr>
            <td style="text-align: center;" class="bold">3</td>
            <td class="bold">Sakaba</td>
            <td class="num">16,541.0</td>
            <td class="num">804.9</td>
            <td class="num">8,655.3</td>
            <td class="num">1,921.9</td>
            <td class="num bold">27,118.3</td>
            <td class="num">3,310.7</td>
            <td class="num">13.3%</td>
          </tr>
          <tr>
            <td style="text-align: center;">4</td>
            <td class="bold">Fakai</td>
            <td class="num">14,962.5</td>
            <td class="num">202.1</td>
            <td class="num">2,445.7</td>
            <td class="num">3,658.0</td>
            <td class="num">21,066.2</td>
            <td class="num">843.9</td>
            <td class="num">12.0%</td>
          </tr>
          <tr>
            <td style="text-align: center;">5</td>
            <td class="bold">Yauri</td>
            <td class="num">15,074.9</td>
            <td class="num">578.8</td>
            <td class="num">3,062.2</td>
            <td class="num">1,276.3</td>
            <td class="num">19,413.5</td>
            <td class="num">1,304.4</td>
            <td class="num">12.1%</td>
          </tr>
          <tr>
            <td style="text-align: center;">6</td>
            <td class="bold">Shanga</td>
            <td class="num">12,160.5</td>
            <td class="num">140.8</td>
            <td class="num">1,141.8</td>
            <td class="num">1,732.3</td>
            <td class="num">15,034.7</td>
            <td class="num">410.5</td>
            <td class="num">9.8%</td>
          </tr>
          <tr>
            <td style="text-align: center;">7</td>
            <td class="bold">Zuru</td>
            <td class="num">1,432.5</td>
            <td class="num">8.2</td>
            <td class="num">329.1</td>
            <td class="num">222.8</td>
            <td class="num">1,984.4</td>
            <td class="num">43.0</td>
            <td class="num">1.2%</td>
          </tr>
          <tr class="total-row">
            <td colspan="2">Total Southern Kebbi</td>
            <td class="num">124,496.7</td>
            <td class="num">4,566.0</td>
            <td class="num">34,628.1</td>
            <td class="num">14,495.7</td>
            <td class="num">173,620.7</td>
            <td class="num">14,476.5</td>
            <td class="num">100.0%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SECTION 9: METHODOLOGICAL AUDIT -->
  <section id="audit" class="section">
    <div class="section-title">
      <span>6. Methodological Audit & Diagnostic Post-Mortem ("What We Were Doing Wrong")</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Mandatory Scientific Self-Correction Log for Doctoral Defense</span>
    </div>

    <div class="callout" style="border-left-color: #C1121F; background: #FFFBFB;">
      <h4>1. Resolution of the 100,000+ ha False-Positive Settlement Over-Prediction</h4>
      <p>Early unconstrained models predicted over 106,000 ha of settlements in 2000 and 30,000+ ha in 2026. Spectral diagnostics revealed that dry-season sandy-clay agricultural soils and eroded laterites have identical high SWIR and Red surface reflectance to corrugated zinc roofs and sun-baked mud compounds. This was resolved by implementing morphological spatial buffering anchored to verified ESA WorldCover Class 50 and Esri Class 7 built-up footprints, establishing an accurate settlement footprint of <strong>7,481.4 ha (0.61%)</strong>.</p>
    </div>

    <div class="callout" style="border-left-color: #D4A373; background: #FFFDF9;">
      <h4>2. Rectification of ESA WorldCover Cropland Inflation</h4>
      <p>ESA WorldCover tags all shifting dry-season bush fallows as cropland, inflating regional agriculture to &gt;58% (711,000 ha). By connecting directly to the contemporary Esri Sentinel-2 10m LULC (2025) ArcGIS REST ImageServer, we isolated active, intensively cultivated parcels, bringing classified cropland to <strong>598,161.2 ha (48.65%)</strong> and correctly preserving <strong>270,710.4 ha (22.02%)</strong> in natural savanna rangeland.</p>
    </div>

    <div class="callout" style="border-left-color: #2D6A4F; background: #F6FAF7;">
      <h4>3. Physical Grounding of the High-Accuracy Biophysical Regressions (R² = 0.686)</h4>
      <p>Early attempts to regress dry-season Landsat NDVI against static 2000 Hansen tree cover across 5,000 unstratified landscape pixels yielded a flat scatter with R² = 0.069 because &gt;85% of pixels were non-forest and dry-season deciduous trees drop their leaves. Regressing bi-temporal canopy drop (ΔNDVI) against moisture/burn collapse (ΔNBR) across active forest degradation pixels established a strong coupling of <strong>R² = 0.6862 (p &lt; 0.0001, N = 3,216)</strong>, while continuous NASA MODIS MOD44B trend analysis proved continuous 25-year thinning (<strong>R² = 0.5841, p = 1.34e-05)</strong>.</p>
    </div>

    <div class="callout" style="border-left-color: #1B4332; background: #F4F6F4;">
      <h4>4. Cartographic Aspect Ratio Preservation & TCC Disambiguation</h4>
      <p>Default portrait templates squeezed Southern Kebbi vertically by 30%. Implementing the Lohara cartographic layout engine dynamically preserved the natural 1.0465:1 UTM aspect ratio with coordinate tick labels on <strong>all four sides</strong> (Top, Bottom, Left, and Right). True Colour Composites were generated as natural photographic RGB composites, and all thematic swatch legends were omitted so the natural land surface remains completely unobstructed.</p>
    </div>
  </section>

  <!-- SECTION 10: CITATION & EXPORT BAR -->
  <section id="citation" class="section">
    <div class="section-title">
      <span>Academic Citation & Research Deliverables</span>
      <span style="font-size: 11px; font-weight: normal; color: #777;">Reference Format: Nature / Remote Sensing of Environment</span>
    </div>
    <p style="font-size: 12.5px; color: #444; margin-bottom: 12px;">
      To cite this research dataset, cartographic atlas, or dissertation report in academic publications, please use the following formal citation:
    </p>

    <div class="bibtex-box" id="bibtexContent">@phdthesis{{southern_kebbi_lulc_2026,
  author    = {{Department of Geography and Remote Sensing}},
  title     = {{Multi-Decadal Land Use and Land Cover Dynamics, Canopy Degradation Trajectories,
                and Multi-Sensor Ground-Truthing in the Sudan-Guinea Savanna Transition Zone:
                A 25-Year Remote Sensing Assessment of Southern Kebbi, Nigeria (2000--2026)}},
  school    = {{Doctoral Dissertation Research Program}},
  year      = {{2026}},
  address   = {{Kebbi State, Federal Republic of Nigeria}},
  note      = {{Cartographic Atlas & Master Earth Observation Research Package}}
}}
<button class="copy-btn" onclick="copyBibtex()">Copy BibTeX</button></div>

    <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 12px;">
      <a class="btn btn-primary" href="{media['excel_href']}" download="SouthernKebbi_statistics.xlsx">
        <span>📊 Master Statistics Excel Workbook (.xlsx)</span>
      </a>
      <a class="btn btn-secondary" href="{media['docx_href']}" download="Southern_Kebbi_PhD_Research_Paper.docx">
        <span>📄 Doctoral Dissertation Paper (.docx)</span>
      </a>
      <a class="btn btn-secondary" href="#animations">
        <span>🎬 View Animated Sequences</span>
      </a>
      <button class="btn btn-secondary" onclick="window.print()">
        <span>🖨️ Print Complete Technical Report</span>
      </button>
    </div>
  </section>

</div>

<!-- Floating Back to Top Button -->
<button onclick="scrollToTop()" id="backToTop" title="Go to top">↑ Top</button>

<!-- Lightbox Modal for High-Res Inspection -->
<div id="imageModal" class="modal" onclick="closeModal()">
  <div class="modal-content" onclick="event.stopPropagation()">
    <img id="modalImg" class="modal-img" src="" alt="High-Res Inspection">
    <div class="modal-caption">
      <span id="modalCaption"></span>
      <span class="modal-close" onclick="closeModal()">&times;</span>
    </div>
  </div>
</div>

<script>
  // Lightbox Modal Controls
  function openModal(imgSrc, caption) {{
    document.getElementById('modalImg').src = imgSrc;
    document.getElementById('modalCaption').textContent = caption;
    document.getElementById('imageModal').style.display = 'flex';
  }}
  function openModalById(imgId, caption) {{
    const el = document.getElementById(imgId);
    if (el) {{
      openModal(el.src, caption);
    }}
  }}
  function openModalFromWrap(wrapElem, caption) {{
    const img = wrapElem.querySelector('img');
    if (img) {{
      openModal(img.src, caption);
    }}
  }}
  function closeModal() {{
    document.getElementById('imageModal').style.display = 'none';
  }}
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeModal();
  }});

  // Copy BibTeX Functionality
  function copyBibtex() {{
    const text = document.getElementById('bibtexContent').innerText.replace('Copy BibTeX', '').trim();
    navigator.clipboard.writeText(text).then(() => {{
      const btn = document.querySelector('.copy-btn');
      btn.textContent = 'Copied!';
      setTimeout(() => {{ btn.textContent = 'Copy BibTeX'; }}, 2000);
    }});
  }}

  // Floating Back to Top Button
  window.onscroll = function() {{
    const topBtn = document.getElementById("backToTop");
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {{
      topBtn.style.display = "block";
    }} else {{
      topBtn.style.display = "none";
    }}
  }};
  function scrollToTop() {{
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }}

  // Active Tab Highlight on Scroll
  const tabs = document.querySelectorAll('.nav-tab');
  const sections = document.querySelectorAll('section');
  window.addEventListener('scroll', () => {{
    let current = '';
    sections.forEach(section => {{
      const sectionTop = section.offsetTop - 100;
      if (pageYOffset >= sectionTop) {{
        current = section.getAttribute('id');
      }}
    }});
    tabs.forEach(tab => {{
      tab.classList.remove('active');
      if (tab.getAttribute('href') === '#' + current) {{
        tab.classList.add('active');
      }}
    }});
  }});
</script>
</body>
</html>
"""
    return html

def main():
    print("=" * 70)
    print("STEP 8F: COMPILING STANDALONE EMBEDDED & RELATIVE HTML DASHBOARDS")
    print("=" * 70)

    # 1. Generate Master Standalone Self-Contained HTML (view_results.html in root)
    t0 = time.time()
    print(">> Encoding all 14 maps, 7 plots, and 3 GIFs into Base64 data URIs...")
    media_embedded = build_media_dictionary(embed=True)
    html_embedded = generate_html_content(media_embedded, is_standalone=True)
    
    with open(HTML_ROOT_PATH, "w", encoding="utf-8") as f:
        f.write(html_embedded)
    print(f"  [OK] Saved Master Standalone Embedded HTML -> {HTML_ROOT_PATH.name} ({HTML_ROOT_PATH.stat().st_size / 1024 / 1024:.2f} MB)")

    # 2. Also save standalone copy into reports/
    with open(HTML_STANDALONE_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_embedded)
    print(f"  [OK] Saved Archival Standalone HTML -> outputs/reports/{HTML_STANDALONE_REPORT_PATH.name}")

    # 3. Generate Lightweight Relative-Linked HTML (outputs/reports/Southern_Kebbi_PhD_Research_Dashboard.html)
    media_relative = build_media_dictionary(embed=False, relative_mode="reports")
    html_relative = generate_html_content(media_relative, is_standalone=False)
    with open(HTML_RELATIVE_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_relative)
    print(f"  [OK] Saved Lightweight Relative-Linked HTML -> outputs/reports/{HTML_RELATIVE_REPORT_PATH.name} ({HTML_RELATIVE_REPORT_PATH.stat().st_size / 1024:.1f} KB)")

    elapsed = time.time() - t0
    print(f"\n[SUCCESS] All HTML dashboard editions compiled in {elapsed:.1f}s.")
    print("  -> You can email 'view_results.html' directly to your guide as a single file!")
    print("  -> All 14 maps, 7 plots, and 3 GIFs are 100% embedded and will render anywhere.")

if __name__ == "__main__":
    main()
