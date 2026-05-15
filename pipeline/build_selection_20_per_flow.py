"""
Build a selection of 20 calls per (country, flow) from the existing manifest.

For each of FR, GB, DE, PL, CZ × (cde_tel, sav):
  - Filter transcripts whose MP3 exists somewhere under Audio MP3/
  - Stratify random sampling across days of January 2026
  - Copy the CSV + the matching MP3 into output/_selection/<COUNTRY>/<FLOW>/

Output : output/_selection/<COUNTRY>/{CdesTel,SAV}/ with both .csv and .mp3 paired,
         plus output/_selection/SELECTION_MANIFEST.csv listing every picked file
         (country, flow, day, csv path, mp3 path, transcript size).
"""
from __future__ import annotations

import csv
import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
MANIFEST = ROOT / "pipeline" / "manifest.json"
TRANSCRIPTS_ROOT = ROOT / "Transcription MP3"
AUDIO_ROOT = ROOT / "Audio MP3"
OUT_ROOT = ROOT / "output" / "_selection"

PER_FLOW = 20
COUNTRIES = ["FR", "GB", "DE", "PL", "CZ"]
FLOW_LABEL = {"cde_tel": "CdesTel", "sav": "SAV"}

random.seed(42)


def index_mp3(audio_root: Path) -> dict[str, Path]:
    """basename (with .mp3) → absolute path."""
    print(f"Indexing MP3 under {audio_root} ...")
    idx: dict[str, Path] = {}
    duplicates = 0
    for p in audio_root.rglob("*.mp3"):
        bn = p.name
        if bn in idx:
            duplicates += 1
            continue
        idx[bn] = p
    print(f"  → {len(idx)} unique MP3, {duplicates} duplicates ignored")
    return idx


def parse_day(filename: str) -> str | None:
    """`004901805708007_20260114192905.mp3.csv` → '2026-01-14'"""
    m = re.search(r"_(\d{4})(\d{2})(\d{2})\d{6}\.mp3", filename)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def stratified_sample(items: list[dict], k: int, key) -> list[dict]:
    """Pick k items spread as evenly as possible across keys (e.g. days).
    If fewer unique keys than k, complete with random extra items."""
    by_key: dict = defaultdict(list)
    for it in items:
        by_key[key(it)].append(it)
    for v in by_key.values():
        random.shuffle(v)

    # Round-robin take one per key until k reached
    picked: list[dict] = []
    remaining_per_key = {k_: list(v) for k_, v in by_key.items()}
    while len(picked) < k and any(remaining_per_key.values()):
        for kk in list(remaining_per_key.keys()):
            if remaining_per_key[kk]:
                picked.append(remaining_per_key[kk].pop())
                if len(picked) >= k:
                    break
    return picked


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mp3_idx = index_mp3(AUDIO_ROOT)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    stats = defaultdict(lambda: defaultdict(int))

    for country in COUNTRIES:
        sample = manifest.get("sample", {}).get(country, {})
        for flow_key in ("cde_tel", "sav"):
            files = sample.get(flow_key, [])
            # files items have a "path" (relative to ROOT) — the CSV transcript path
            # the matching mp3 name = filename without ".csv"
            candidates = []
            missing_mp3 = 0
            missing_csv = 0
            for f in files:
                csv_rel = f["path"]
                # The manifest was generated when CSV folders lived at the repo root.
                # They have since been moved under "Transcription MP3/". Try both.
                csv_path = ROOT / "Transcription MP3" / csv_rel.replace("/", "\\")
                if not csv_path.exists():
                    csv_path_legacy = ROOT / csv_rel.replace("/", "\\")
                    if csv_path_legacy.exists():
                        csv_path = csv_path_legacy
                    else:
                        missing_csv += 1
                        continue
                csv_name = csv_path.name  # e.g. xxx_20260114.mp3.csv
                mp3_name = csv_name.removesuffix(".csv")  # xxx_20260114.mp3
                mp3_path = mp3_idx.get(mp3_name)
                if not mp3_path:
                    missing_mp3 += 1
                    continue
                day = parse_day(csv_name) or "?"
                candidates.append({
                    "csv_path": csv_path,
                    "mp3_path": mp3_path,
                    "csv_name": csv_name,
                    "day": day,
                    "size_b": csv_path.stat().st_size,
                })

            print(f"\n{country} / {flow_key}: total in manifest={len(files)}, "
                  f"with MP3={len(candidates)}, missing MP3={missing_mp3}, missing CSV={missing_csv}")

            if not candidates:
                stats[country][flow_key] = 0
                continue

            picks = stratified_sample(candidates, PER_FLOW, key=lambda x: x["day"])
            stats[country][flow_key] = len(picks)

            # Nested structure : <PAYS>/<FLUX>/Audio MP3/ and <PAYS>/<FLUX>/Transcription/
            flow_root = OUT_ROOT / country / FLOW_LABEL[flow_key]
            audio_dir = flow_root / "Audio MP3"
            transcript_dir = flow_root / "Transcription"
            audio_dir.mkdir(parents=True, exist_ok=True)
            transcript_dir.mkdir(parents=True, exist_ok=True)
            for p in picks:
                mp3_name = p["csv_name"].removesuffix(".csv")
                shutil.copy2(p["csv_path"], transcript_dir / p["csv_name"])
                shutil.copy2(p["mp3_path"], audio_dir / mp3_name)
                summary_rows.append({
                    "country": country,
                    "flow": FLOW_LABEL[flow_key],
                    "day": p["day"],
                    "csv_file": p["csv_name"],
                    "mp3_file": mp3_name,
                    "transcript_size_b": p["size_b"],
                    "csv_local": str(transcript_dir / p["csv_name"]),
                    "mp3_local": str(audio_dir / mp3_name),
                })

    # Write manifest CSV
    manifest_csv = OUT_ROOT / "SELECTION_MANIFEST.csv"
    if summary_rows:
        with manifest_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            w.writeheader()
            w.writerows(summary_rows)
    else:
        print("WARN: no rows selected — manifest CSV not written")
    print(f"\n=== TOTALS ===")
    for c in COUNTRIES:
        print(f"  {c}  CdesTel={stats[c]['cde_tel']:>2}  SAV={stats[c]['sav']:>2}  "
              f"total={stats[c]['cde_tel']+stats[c]['sav']}")
    grand = sum(stats[c]['cde_tel'] + stats[c]['sav'] for c in COUNTRIES)
    print(f"Grand total : {grand} pairs (CSV + MP3)")
    print(f"\nManifest CSV : {manifest_csv}")


if __name__ == "__main__":
    main()
