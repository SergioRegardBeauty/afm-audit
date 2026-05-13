"""
A partir de manifest.json, produit un fichier texte par (pays, flux) listant
les chemins absolus a auditer + URL relatives, pret a etre embedded dans le
prompt d'un subagent.
"""
import json
from pathlib import Path

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
MANIFEST = ROOT / "pipeline" / "manifest.json"
OUT_DIR = ROOT / "pipeline" / "subagent_inputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

with MANIFEST.open(encoding="utf-8") as f:
    manifest = json.load(f)

for country, flows in manifest["sample"].items():
    for flow, files in flows.items():
        if not files:
            continue
        lines = []
        for i, info in enumerate(files, 1):
            full_path = ROOT / info["path"].replace("/", "\\")
            lines.append(f"{i}. {full_path}")
        out_file = OUT_DIR / f"{country}_{flow}.txt"
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"{country} {flow}: {len(files)} -> {out_file.name}")
