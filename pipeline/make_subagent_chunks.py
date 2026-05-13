"""
Decoupe les listes de transcripts par pays/flux en chunks de N audits.
Genere un fichier txt par chunk dans pipeline/subagent_inputs_chunks/.
Saute les audits deja faits (PL et CZ) et ceux deja sauvegardes en v1 (pour FR cde_tel uniquement).
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(r"f:\WORK\Audit_Dialoga_AtlasForMen_2026")
MANIFEST = ROOT / "pipeline" / "manifest.json"
OUT_DIR = ROOT / "pipeline" / "subagent_inputs_chunks"
AUDITS_V1 = ROOT / "audits_ia" / "v1"

# Reset le dossier pour eviter les vieux chunks
if OUT_DIR.exists():
    for p in OUT_DIR.iterdir():
        if p.is_file():
            p.unlink()
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 50

with MANIFEST.open(encoding="utf-8") as f:
    manifest = json.load(f)

# Skip PL et CZ (deja audites entierement en v1) — toujours skip
SKIP_COUNTRIES = {"PL", "CZ"}
# La logique skip "deja audites" via JSON existants est plus bas (done_basenames)

summary = []
for country, flows in manifest["sample"].items():
    if country in SKIP_COUNTRIES:
        continue
    for flow, files in flows.items():
        if not files:
            continue
        # Filtre les audits deja faits en v1
        done_dir = AUDITS_V1 / country / flow
        done_basenames = set()
        if done_dir.exists():
            done_basenames = {p.stem for p in done_dir.glob("*.json")}

        # Garde seulement les transcripts non encore audites
        pending = []
        for info in files:
            basename = info["name"].replace(".mp3.csv", "")
            if basename in done_basenames:
                continue
            pending.append(info)

        if not pending:
            print(f"  {country} {flow}: tout deja fait, skip")
            continue

        # Chunk
        n_chunks = (len(pending) + CHUNK_SIZE - 1) // CHUNK_SIZE
        for chunk_i in range(n_chunks):
            chunk = pending[chunk_i * CHUNK_SIZE : (chunk_i + 1) * CHUNK_SIZE]
            lines = []
            for i, info in enumerate(chunk, 1):
                full_path = ROOT / info["path"].replace("/", "\\")
                lines.append(f"{i}. {full_path}")
            chunk_name = f"{country}_{flow}_chunk_{chunk_i+1:03d}.txt"
            (OUT_DIR / chunk_name).write_text("\n".join(lines), encoding="utf-8")
            summary.append((country, flow, chunk_i + 1, len(chunk), chunk_name))

print(f"\n=== {len(summary)} chunks generes ===\n")
total_audits = sum(s[3] for s in summary)
print(f"Total audits a faire : {total_audits}")
print()
by_country = {}
for c, f, idx, n, name in summary:
    by_country.setdefault((c, f), []).append((idx, n, name))
for (c, f), chunks in sorted(by_country.items()):
    total_in = sum(n for _, n, _ in chunks)
    print(f"  {c} {f}: {len(chunks)} chunks, {total_in} audits")
