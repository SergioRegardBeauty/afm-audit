"""
Pour les transcripts trop courts pour etre audites par IA (<500B),
genere directement un JSON 'audit' avec NA partout + commentaire 'Non auditable'.
Pas d'API call, instantane.

Classifie aussi par flux:
- Si le contenu contient un mot-cle Cde Tel ou SAV -> classe ainsi
- Sinon -> par defaut cde_tel (la majorite des appels AFM)

Pour les transcripts 500B-3KB, on ne touche pas (subagent les fera).
"""
from __future__ import annotations
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
AUDITS_DIR = ROOT / "audits_ia" / "v1"

COUNTRY_MAP = [
    ("Atlas FR", "FR"),
    ("Atlas EN", "GB"),
    ("atlas German", "DE"),
    ("atlas Polaand", "PL"),
    ("atlas Tcheque", "CZ"),
    ("atlas Tchèque", "CZ"),
]

MICRO_THRESHOLD = 500   # <500B = quasi silent

LANG_FROM_COUNTRY = {"FR": "fr", "GB": "en", "DE": "de", "PL": "pl", "CZ": "cs"}


def detect_country(folder_name: str) -> str | None:
    for prefix, country in COUNTRY_MAP:
        if folder_name.startswith(prefix):
            return country
    return None


def read_transcript_short(csv_path: Path) -> tuple[str, str]:
    """Renvoie (full_text concatene, dernier End time)."""
    try:
        with csv_path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = [r for r in reader if r.get("Text")]
        full = " ".join((r.get("Text") or "").strip().strip('"') for r in rows)
        dmt = rows[-1].get("End time", "") if rows else ""
        return full, dmt
    except Exception:
        return "", ""


def classify_quick(text: str) -> str:
    """Quick classification fallback."""
    lower = text.lower()
    sav_kws = [r"o[uù] est", r"rembours", r"plaint", r"reclam", r"r[éeé]clam",
               r"retour", r"d[éeé]fect", r"refund", r"return", r"complaint",
               r"erstattung", r"reklamation", r"zwrot", r"reklamacja",
               r"reklamac", r"st[ií]žnost"]
    for kw in sav_kws:
        if re.search(kw, lower):
            return "sav"
    return "cde_tel"


CDE_TEL_CRITERES = [
    "1_accueil", "2_identification", "3_climat", "4_mise_en_attente",
    "5_conclusion", "6_prise_conges", "7_personnalisation",
    "8_pre_commande", "9_commande", "10_outils", "11_coord_bancaires",
    "12_rebond_commercial", "13_objection", "14_ecoute_active",
    "15_accompagnement",
]

CDE_TEL_BAREMES = {
    "1_accueil": 0.5, "2_identification": 1.0, "3_climat": 0.5,
    "4_mise_en_attente": 0.3, "5_conclusion": 0.5, "6_prise_conges": 0.5,
    "7_personnalisation": 0.5, "8_pre_commande": 0.5, "9_commande": 1.2,
    "10_outils": 0.3, "11_coord_bancaires": 0.2, "12_rebond_commercial": 1.0,
    "13_objection": 1.0, "14_ecoute_active": 1.0, "15_accompagnement": 1.0,
}

SAV_CRITERES = [
    "1_accueil", "2_identification", "3_mise_en_attente", "4_conclusion",
    "5_prise_conges", "6_personnalisation", "7_climat",
    "8_maitrise_directivite", "9_decouverte_reformulation",
    "10_pertinence_reponse", "11_outils", "12_codification",
    "13_delai_traitement", "14_experience_client", "15_ecoute_empathie",
    "16_enchantement",
]

SAV_BAREMES = {
    "1_accueil": 0.5, "2_identification": 1.0, "3_mise_en_attente": 0.3,
    "4_conclusion": 0.5, "5_prise_conges": 0.5, "6_personnalisation": 0.5,
    "7_climat": 1.0, "8_maitrise_directivite": 0.5,
    "9_decouverte_reformulation": 1.0, "10_pertinence_reponse": 1.5,
    "11_outils": 0.5, "12_codification": 0.5, "13_delai_traitement": 0.2,
    "14_experience_client": 1.0, "15_ecoute_empathie": 0.5,
    "16_enchantement": 0.5,
}


def build_na_audit(csv_path: Path, country: str, flow: str, full_text: str, dmt: str) -> dict:
    basename = csv_path.name.replace(".mp3.csv", "")
    phone = basename.split("_")[0]
    lang = LANG_FROM_COUNTRY.get(country, "fr")
    criteres_list = CDE_TEL_CRITERES if flow == "cde_tel" else SAV_CRITERES
    baremes = CDE_TEL_BAREMES if flow == "cde_tel" else SAV_BAREMES

    text_preview = (full_text[:150] + "...") if len(full_text) > 150 else full_text

    criteres = {}
    for c in criteres_list:
        criteres[c] = {
            "notation": "NA",
            "note": "NA",
            "bareme": baremes[c],
            "justification": "Transcript trop court (<500 octets) — appel raccroche, silencieux ou IVR-only. Non auditable.",
            "timestamp_preuve": "",
        }

    return {
        "metadata": {
            "n_appel": basename,
            "agent": "",
            "n_client": "",
            "pays": country,
            "langue_appel": lang,
            "n_cde_req": "",
            "n_tel": phone,
            "DMT_DMC": dmt,
            "type_cde" if flow == "cde_tel" else "type_demande": "non auditable",
            "demande_client": f"Appel non auditable. Contenu transcript : '{text_preview}'",
        },
        "criteres": criteres,
        "SI_detectees": [],
        "totaux": {
            "relation_client": 0,
            "connaissance_metier": 0,
            "technique_vente" if flow == "cde_tel" else "experience_client": 0,
            "experience_client" if flow == "cde_tel" else "enchantement": 0,
            "note_totale_sur_10": None,
            "note_sur_100": None,
            "note_zero_par_SI": False,
        },
        "commentaire_global": "Audit automatique : transcript trop court pour evaluation IA (<500 octets). Soit appel raccroche avant decrochage, soit silence/bruit de fond uniquement, soit IVR seul.",
        "commentaire_traduit_fr": "",
        "_auto_na": True,
    }


def main():
    folders = [d for d in ROOT.iterdir() if d.is_dir() and detect_country(d.name)]
    n_created = 0
    n_skipped = 0
    n_already = 0
    stats = {}

    for folder in folders:
        country = detect_country(folder.name)
        if not country:
            continue
        for csv_path in folder.glob("*.csv"):
            size = csv_path.stat().st_size
            if size >= MICRO_THRESHOLD:
                n_skipped += 1
                continue
            basename = csv_path.name.replace(".mp3.csv", "")
            full_text, dmt = read_transcript_short(csv_path)
            flow = classify_quick(full_text)

            # Skip if already audited
            target = AUDITS_DIR / country / flow / f"{basename}.json"
            if target.exists():
                n_already += 1
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            audit = build_na_audit(csv_path, country, flow, full_text, dmt)
            with target.open("w", encoding="utf-8") as f:
                json.dump(audit, f, ensure_ascii=False, indent=2)
            n_created += 1
            stats.setdefault((country, flow), 0)
            stats[(country, flow)] += 1

    print(f"NA audits crees     : {n_created}")
    print(f"Skipped (>=500B)    : {n_skipped}")
    print(f"Deja audites        : {n_already}")
    print()
    print("=== Par pays/flux ===")
    for (c, f), n in sorted(stats.items()):
        print(f"  {c} {f}: +{n}")


if __name__ == "__main__":
    main()
