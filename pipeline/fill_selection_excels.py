"""
Fill BQ Excel templates with the 20 selected calls per pays × flux.

Reads output/_selection/SELECTION_MANIFEST.csv, joins to existing audit JSONs in
audits_ia/v1/<PAYS>/<flow>/<call_id>.json, and writes one Excel per (pays, flow)
in output/_selection/<PAYS>/<CdesTel|SAV>/.

For calls without an existing audit JSON, an empty "placeholder" audit is built
from the CSV filename metadata so the row still appears (notes left blank for
manual review).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

# Reuse the proven helpers from fill_excel.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fill_excel import (  # type: ignore
    CDE_TEL_COLS,
    SAV_COLS,
    LANG_FROM_COUNTRY,
    fill_one_template,
)

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
SELECTION_DIR = ROOT / "output" / "_selection"
MANIFEST_CSV = SELECTION_DIR / "SELECTION_MANIFEST.csv"
AUDITS_DIR = ROOT / "audits_ia" / "v1"
TEMPLATE_CDE = ROOT / "BQ_1_CdesTel_10 (2).xlsx"
TEMPLATE_SAV = ROOT / "BQ_4_Sav_10_ (2).xlsx"

FLOW_MAP = {"CdesTel": ("cde_tel", TEMPLATE_CDE, CDE_TEL_COLS, "Cde tél"),
            "SAV":     ("sav",     TEMPLATE_SAV, SAV_COLS,     "SAV")}


def empty_audit(call_id: str, country: str, flow_key: str) -> dict:
    """Build a minimal audit dict for a call without an existing audit JSON."""
    m = re.match(r"^(\d+)_(\d{14})$", call_id)
    phone = m.group(1) if m else ""
    return {
        "metadata": {
            "n_appel": call_id,
            "agent": "",
            "n_client": "",
            "pays": country,
            "langue_appel": LANG_FROM_COUNTRY.get(country, ""),
            "n_cde_req": "",
            "n_tel": phone,
            "DMT_DMC": "",
            "type_cde": "non audité",
            "demande_client": "(audit non encore réalisé)",
        },
        "criteres": {},
        "totaux": {},
        "SI_detectees": [],
        "commentaire_global": "Audit à compléter manuellement ou par le pipeline IA.",
    }


def load_audits_for_selection(country: str, flow_key: str, call_ids: list[str]) -> list[dict]:
    folder = AUDITS_DIR / country / flow_key
    audits = []
    n_existing = 0
    n_placeholder = 0
    for cid in call_ids:
        json_path = folder / f"{cid}.json"
        if json_path.exists():
            try:
                audit = json.loads(json_path.read_text(encoding="utf-8"))
                n_existing += 1
            except Exception as e:
                print(f"  WARN: {json_path.name} unreadable ({e}); using empty")
                audit = empty_audit(cid, country, flow_key)
                n_placeholder += 1
        else:
            audit = empty_audit(cid, country, flow_key)
            n_placeholder += 1
        audits.append(audit)
    return audits, n_existing, n_placeholder


def main():
    # 1) Read manifest → call_ids by (country, flow_label)
    sel: dict[tuple[str, str], list[str]] = {}
    with MANIFEST_CSV.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            country = row["country"]
            flow_label = row["flow"]  # "CdesTel" or "SAV"
            call_id = row["mp3_file"].removesuffix(".mp3")
            sel.setdefault((country, flow_label), []).append(call_id)

    # 2) For each (country, flow_label), build audits + fill Excel
    for (country, flow_label), call_ids in sorted(sel.items()):
        flow_key, template, cols, sheet_name = FLOW_MAP[flow_label]
        out_dir = SELECTION_DIR / country / flow_label
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = "BQ_1_CdesTel" if flow_label == "CdesTel" else "BQ_4_Sav"
        out_path = out_dir / f"{prefix}_{country}.xlsx"

        # Clean any old copy of the template that was sitting there
        for old in out_dir.glob(f"{prefix}*.xlsx"):
            old.unlink()

        audits, n_existing, n_placeholder = load_audits_for_selection(country, flow_key, call_ids)
        print(f"{country}/{flow_label}: {len(audits)} calls "
              f"({n_existing} avec audit existant, {n_placeholder} placeholders)")
        fill_one_template(template, out_path, country, audits, cols, sheet_name)

    print("\nDone. Excels écrits dans output/_selection/<PAYS>/<flow>/.")


if __name__ == "__main__":
    main()
