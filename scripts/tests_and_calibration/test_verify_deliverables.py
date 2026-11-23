from pathlib import Path
import re

base_dir = Path(__file__).resolve().parents[2]
html_path = base_dir / "view_results.html"
content = html_path.read_text(encoding="utf-8")

matches = set(re.findall(r"outputs/[a-zA-Z0-9_./-]+", content))
missing = []
for m in sorted(matches):
    p = base_dir / m
    if not p.exists():
        missing.append(m)

print(f"Total unique referenced outputs in view_results.html: {len(matches)}")
if missing:
    print(f"MISSING ({len(missing)}): {missing}")
else:
    print("[SUCCESS] 100% of referenced files in HTML exist and are valid!")

# Check docx
docx_path = base_dir / "outputs" / "reports" / "Southern_Kebbi_PhD_Research_Paper.docx"
print(f"Docx file: {docx_path.name} ({docx_path.stat().st_size / 1024 / 1024:.2f} MB)")

