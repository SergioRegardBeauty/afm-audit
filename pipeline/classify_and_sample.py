"""
Classifie chaque transcript CSV comme Cde Tel / SAV / Unknown
en se basant sur les premieres prises de parole client + mots-cles multilingues.
Echantillonne 10 par flux par pays. Produit pipeline/manifest.json.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
OUT = ROOT / "pipeline"
OUT.mkdir(parents=True, exist_ok=True)

# Mapping dossier -> pays
COUNTRY_MAP = [
    ("Atlas FR", "FR"),
    ("Atlas EN", "GB"),
    ("atlas German", "DE"),
    ("atlas Polaand", "PL"),
    ("atlas Tcheque", "CZ"),
    ("atlas Tchèque", "CZ"),
    ("All files", "MIXED"),
]

MIN_BYTES = 500  # transcripts < 500B sont auto-NA (auto_na_audits.py)
TARGET_PER_FLOW = 999999  # tous les appels classifies (mode exhaustif)

# Mots-cles d'intention par langue
# Cde Tel = nouvelle commande / passage de commande
CDE_TEL_KEYWORDS = {
    "fr": [
        r"passer\s+(une\s+)?(nouvelle\s+)?commande",
        r"passer\s+(une\s+)?cde",
        r"(je\s+)?voudrais\s+(commander|passer)",
        r"(je\s+)?souhaite\s+(commander|passer)",
        r"je\s+veux\s+commander",
        r"c['e]?\s*serait\s+pour\s+(passer|une\s+commande|commander)",
        r"c['e]?\s*est\s+pour\s+(passer|une\s+commande|commander)",
        r"pour\s+passer\s+une\s+commande",
        r"code\s+avantage",
        r"j['ae]i\s+(le\s+)?catalogue",
        r"taille\s+(s|m|l|xl|xxl|2xl|3xl|4xl)",
    ],
    "en": [
        r"place\s+an?\s+order",
        r"want\s+to\s+order",
        r"would\s+like\s+to\s+order",
        r"need\s+to\s+order",
        r"like\s+to\s+place",
        r"new\s+order",
        r"i\s+have\s+the\s+catalog",
        r"size\s+(s|m|l|xl|xxl|2xl|3xl|4xl)",
        r"reference\s+number",
        r"promo\s*code",
        r"advantage\s+code",
    ],
    "de": [
        r"bestellung\s+aufgeben",
        r"eine\s+bestellung\s+(machen|aufgeben)",
        r"m[oö]chte\s+(eine\s+)?bestell",
        r"ich\s+will\s+bestellen",
        r"katalog",
        r"vorteils?code",
        r"artikelnummer",
        r"gr[oö][sß]e",
    ],
    "pl": [
        r"z[lł]o[zż]y[cć]\s+zam[oó]wien",
        r"zam[oó]wi[cć]",
        r"chc[ęe]\s+zam[oó]wi[cć]",
        r"zamawiam",
        r"katalog",
        r"rozmiar",
        r"kod\s+rabatowy",
    ],
    "cz": [
        r"objedn[aá]vku",
        r"chci\s+objednat",
        r"objedn[aá]v[aá]m",
        r"obj[eě]dnat",
        r"katalog",
        r"velikost",
        r"katalogov[eéaá]\s+[čc]",
        r"slev[oa]v[yý]\s+k[oó]d",
    ],
}

# SAV = service apres-vente / suivi / reclamation
SAV_KEYWORDS = {
    "fr": [
        r"o[uù]\s+(est|en\s+est)\s+ma\s+commande",
        r"suivi\s+de\s+(ma\s+)?commande",
        r"j['ae]i\s+pass[ée]\s+(une\s+)?commande",
        r"je\s+n['ae]i\s+pas\s+re[cç]u",
        r"j['ae]i\s+pas\s+re[cç]u",
        r"rien\s+re[cç]u",
        r"toujours\s+(pas|rien)\s+re[cç]u",
        r"remboursement",
        r"remboursé",
        r"rembourser",
        r"annuler\s+(ma\s+|une\s+)?commande",
        r"r[eé]clamation",
        r"d[eé]fectueux",
        r"abim[eé]",
        r"cass[eé]",
        r"ne\s+fonctionne\s+pas",
        r"retour(ner)?(\s+un\s+article)?",
        r"renvoyer",
        r"double\s+pr[eé]l[eè]vement",
        r"facture",
        r"livraison",
        r"d[eé]lai\s+de\s+livraison",
        r"colis",
        r"point\s+relais",
    ],
    "en": [
        r"where\s+is\s+my\s+order",
        r"order\s+status",
        r"i\s+placed\s+an?\s+order",
        r"haven['e]?t\s+received",
        r"didn['e]?t\s+(receive|get)",
        r"not\s+received",
        r"refund",
        r"return\s+(my|the|an?)\s+(item|order|product|parcel)",
        r"cancel\s+(my\s+)?order",
        r"complaint",
        r"damaged",
        r"defective",
        r"broken",
        r"delivery",
        r"missing",
        r"wrong\s+(item|address|size)",
    ],
    "de": [
        r"wo\s+ist\s+meine\s+bestellung",
        r"bestellstatus",
        r"ich\s+habe\s+(eine\s+)?bestellung\s+(aufgegeben|gemacht)",
        r"nicht\s+erhalten",
        r"(noch\s+)?nicht\s+bekommen",
        r"erstattung",
        r"zur[uü]ckgeben",
        r"reklamation",
        r"besch[aä]digt",
        r"defekt",
        r"lieferung",
        r"r[uü]cksendung",
        r"paket",
    ],
    "pl": [
        r"gdzie\s+(jest\s+)?moje\s+zam[oó]wienie",
        r"zwrot",
        r"reklamacja",
        r"nie\s+otrzyma[lł]",
        r"przesy[lł]ka",
        r"problem\s+z",
        r"odst[aą]pi[cć]",
        r"anulowa[cć]",
        r"zwr[oó]ci[cć]",
        r"uszkodzon",
        r"reklamuj",
    ],
    "cz": [
        r"kde\s+je\s+m[ée]\s+objedn[aá]vk",
        r"vr[aá]cen[ií]",
        r"reklamac",
        r"nedostal",
        r"probl[eé]m",
        r"st[ií]žnost",
        r"zru[sš]it",
        r"po[sš]kozen",
        r"nefunguje",
        r"reklamuji",
        r"vr[aá]tit",
        r"po[sš]l[eěa]te",
        r"vym[eě]nit",
    ],
}


def detect_country(folder_name: str) -> str:
    for prefix, country in COUNTRY_MAP:
        if folder_name.startswith(prefix):
            return country
    return "MIXED"


def country_to_lang(country: str) -> str:
    return {"FR": "fr", "GB": "en", "DE": "de", "PL": "pl", "CZ": "cz"}.get(country, "fr")


def read_transcript(csv_path: Path) -> tuple[list[dict], str]:
    """Lit un CSV transcript. Retourne (liste de segments, texte concatene)."""
    rows: list[dict] = []
    try:
        with csv_path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                if row.get("Text"):
                    rows.append({
                        "n": row.get("Number"),
                        "speaker": row.get("Speaker", "").strip(),
                        "start": row.get("Start time", "").strip(),
                        "end": row.get("End time", "").strip(),
                        "duration": row.get("Duration", "").strip(),
                        "text": row.get("Text", "").strip().strip('"'),
                    })
    except Exception as e:
        return [], ""
    full_text = " ".join(r["text"] for r in rows)
    return rows, full_text


def classify(rows: list[dict], full_text: str, lang: str) -> tuple[str, dict]:
    """Renvoie ('cde_tel' | 'sav' | 'unknown', info)."""
    if not rows:
        return "unknown", {"reason": "empty"}

    text_norm = full_text.lower()

    cde_kws = CDE_TEL_KEYWORDS.get(lang, []) + CDE_TEL_KEYWORDS["fr"]
    sav_kws = SAV_KEYWORDS.get(lang, []) + SAV_KEYWORDS["fr"]

    cde_hits = []
    sav_hits = []

    for pattern in cde_kws:
        matches = re.findall(pattern, text_norm)
        if matches:
            cde_hits.append(pattern)

    for pattern in sav_kws:
        matches = re.findall(pattern, text_norm)
        if matches:
            sav_hits.append(pattern)

    # Heuristique : "j'ai passé une commande" (SAV) gagne contre "passer une commande" (Cde Tel)
    # car l'imparfait/passe = appel post-commande.
    # Le mot 'remboursement' / 'retour' / 'rembourser' force SAV.
    strong_sav_signals = ["remboursement", "rembourser", "annuler", "réclamation",
                         "refund", "return", "cancel",
                         "erstattung", "reklamation", "zur[uü]ckgeben",
                         "zwrot", "reklamacja", "anulowa[cć]",
                         "reklamac", "st[ií]žnost", "vr[aá]cen", "po[sš]kozen"]
    for s in strong_sav_signals:
        if re.search(s, text_norm):
            return "sav", {"cde_hits": cde_hits[:3], "sav_hits": sav_hits[:5],
                          "score_cde": len(cde_hits), "score_sav": len(sav_hits) + 5,
                          "trigger": f"strong_sav:{s}"}

    # Decision par score
    cde_score = len(cde_hits)
    sav_score = len(sav_hits)

    if cde_score == 0 and sav_score == 0:
        return "unknown", {"cde_hits": [], "sav_hits": [], "score_cde": 0, "score_sav": 0}

    if cde_score >= sav_score and cde_score >= 1:
        return "cde_tel", {"cde_hits": cde_hits[:5], "sav_hits": sav_hits[:3],
                          "score_cde": cde_score, "score_sav": sav_score}
    else:
        return "sav", {"cde_hits": cde_hits[:3], "sav_hits": sav_hits[:5],
                      "score_cde": cde_score, "score_sav": sav_score}


def main():
    folders = [d for d in ROOT.iterdir() if d.is_dir() and any(
        d.name.startswith(p) for p, _ in COUNTRY_MAP
    )]

    # Bucket : country -> flow -> list[file_info]
    bucket: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    unknowns: dict[str, list[dict]] = defaultdict(list)
    stats = defaultdict(lambda: defaultdict(int))

    for folder in folders:
        country = detect_country(folder.name)
        if country == "MIXED":
            # On va re-detecter par contenu pour les "All files"
            country_hint = "FR"  # fallback
        else:
            country_hint = country

        lang = country_to_lang(country_hint)

        csvs = [p for p in folder.iterdir() if p.is_file() and p.suffix == ".csv"]
        for csv_path in csvs:
            size = csv_path.stat().st_size
            stats[country]["total"] += 1
            if size < MIN_BYTES:
                stats[country]["skipped_tiny"] += 1
                continue
            rows, full_text = read_transcript(csv_path)
            if not rows or len(full_text) < 200:
                stats[country]["skipped_empty"] += 1
                continue

            flow, info = classify(rows, full_text, lang)
            file_info = {
                "path": str(csv_path.relative_to(ROOT)).replace("\\", "/"),
                "name": csv_path.name,
                "size_bytes": size,
                "n_segments": len(rows),
                "first_customer_utterance": next(
                    (r["text"] for r in rows[:8] if r["speaker"] and r["speaker"] != "Orateur 1"),
                    rows[0]["text"] if rows else ""
                )[:200],
                "duration_estimate": rows[-1]["end"] if rows else None,
                "classification": flow,
                "classification_info": info,
                "country": country,
                "lang": lang,
            }

            if flow == "cde_tel":
                bucket[country]["cde_tel"].append(file_info)
                stats[country]["cde_tel"] += 1
            elif flow == "sav":
                bucket[country]["sav"].append(file_info)
                stats[country]["sav"] += 1
            else:
                unknowns[country].append(file_info)
                stats[country]["unknown"] += 1

    # Echantillonnage : 10 par flux par pays, deterministe (seed fixe)
    random.seed(42)
    sample: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))

    for country, flows in bucket.items():
        if country == "MIXED":
            continue
        for flow_name in ("cde_tel", "sav"):
            candidates = flows.get(flow_name, [])
            # Mode exhaustif : on prend tous les substantiels, tries par taille (grands d'abord)
            candidates_sorted = sorted(candidates, key=lambda x: x["size_bytes"], reverse=True)
            if len(candidates_sorted) <= TARGET_PER_FLOW:
                picks = candidates_sorted
            else:
                picks = random.sample(candidates_sorted, TARGET_PER_FLOW)
            sample[country][flow_name] = picks

    manifest = {
        "stats": {c: dict(s) for c, s in stats.items()},
        "sample": {c: {f: lst for f, lst in flows.items()} for c, flows in sample.items()},
        "unknowns_count": {c: len(lst) for c, lst in unknowns.items()},
        "target_per_flow": TARGET_PER_FLOW,
        "min_bytes": MIN_BYTES,
    }

    out_path = OUT / "manifest.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Manifest written: {out_path}")
    print()
    print("=== STATS PAR PAYS ===")
    for country in sorted(stats.keys()):
        s = stats[country]
        sampled_cde = len(sample.get(country, {}).get("cde_tel", []))
        sampled_sav = len(sample.get(country, {}).get("sav", []))
        print(f"  {country:<6} total={s['total']:>5} cde_tel={s['cde_tel']:>4} sav={s['sav']:>4} unknown={s['unknown']:>4} tiny={s['skipped_tiny']:>4} empty={s['skipped_empty']:>4}  |  sampled cde={sampled_cde}/sav={sampled_sav}")


if __name__ == "__main__":
    main()
