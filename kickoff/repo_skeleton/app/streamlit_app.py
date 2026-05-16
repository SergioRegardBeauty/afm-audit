"""Atlas For Men — interface web multi-user (Streamlit).

Écrans :
  - Login (email + password, bcrypt)
  - Dashboard (KPIs globaux)
  - Transcripts (listing + filtres)
  - Lancer audit (sélection transcript → Claude → résultat)
  - Audits (historique des passages IA, comparaison humain si dispo)

Toute action sensible est loggée dans la table `audit_log` (RGPD).

Démarrage local :
    cd kickoff/repo_skeleton
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import io
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# rendre src/afm_audit importable depuis app/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from afm_audit.audit import (  # noqa: E402
    audit_one_file_from_db,
    detect_flow,
    detect_pays_langue,
    parse_csv_transcript,
)
from afm_audit.config import settings  # noqa: E402
from afm_audit.db import get_connection  # noqa: E402
from afm_audit.llm import audit_transcript  # noqa: E402

# Rendre `pipeline/fill_excel.py` importable pour réutiliser les helpers Excel
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "pipeline"))
from fill_excel import (  # type: ignore  # noqa: E402
    CDE_TEL_COLS,
    SAV_COLS,
    fill_one_template,
)

TEMPLATE_CDE = PROJECT_ROOT / "BQ_1_CdesTel_10 (2).xlsx"
TEMPLATE_SAV = PROJECT_ROOT / "BQ_4_Sav_10_ (2).xlsx"


# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Atlas For Men — Audit IA",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Authentification (lecture du users.yaml hors-Git)
# API streamlit-authenticator >= 0.3 : login() écrit dans st.session_state au lieu
# de retourner un tuple ; Authenticate(...) ne supporte plus @st.cache_resource car
# il crée des widgets cookie-manager.
# ---------------------------------------------------------------------------
def load_users_config() -> dict:
    """Trois sources possibles, par ordre de priorité :
       1. st.secrets['users_yaml']  → string YAML, utilisé sur Streamlit Cloud
       2. app/users.yaml local      → utilisé en dev local
       3. erreur sinon
    """
    # 1. Streamlit Cloud secrets
    try:
        yaml_content = st.secrets.get("users_yaml")
    except (FileNotFoundError, AttributeError):
        yaml_content = None
    if yaml_content:
        return yaml.load(yaml_content, Loader=SafeLoader)

    # 2. Fichier local
    users_yaml = Path(__file__).parent / "users.yaml"
    if users_yaml.exists():
        with users_yaml.open("r", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)

    # 3. Pas de config
    st.error(
        "Configuration utilisateurs introuvable :\n"
        "- En **local** : copie `app/users.yaml.example` en `app/users.yaml` et remplis-le.\n"
        "- Sur **Streamlit Cloud** : ajoute dans `Settings > Secrets` une clé `users_yaml` "
        "contenant le YAML complet (voir doc DEPLOY_CLOUD.md)."
    )
    st.stop()


_cfg = load_users_config()
authenticator = stauth.Authenticate(
    _cfg["credentials"],
    _cfg["cookie"]["name"],
    _cfg["cookie"]["key"],
    _cfg["cookie"]["expiry_days"],
)

authenticator.login(location="main")
auth_status = st.session_state.get("authentication_status")

if auth_status is False:
    st.error("Email ou mot de passe incorrect.")
    st.stop()
if auth_status is None:
    st.info("Connecte-toi pour accéder à l'interface.")
    st.stop()

name = st.session_state.get("name", "")
username = st.session_state.get("username", "")

# À partir d'ici, l'utilisateur est authentifié.
with st.sidebar:
    st.markdown(f"**Connecté : {name}**")
    authenticator.logout("Se déconnecter", location="sidebar")
    st.divider()
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📜 Transcripts", "🤖 Lancer un audit",
         "📤 Auto-audit (upload CSV)", "📋 Audits"],
        label_visibility="collapsed",
    )


# ---------------------------------------------------------------------------
# Helpers DB (cache 5 min sur les KPIs)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def fetch_counts_by_pays_flow() -> pd.DataFrame:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT pays, flow,
                   COUNT(*) AS n,
                   AVG(duree_secondes)::int AS duree_moy_s,
                   SUM(size_bytes)/1024/1024 AS total_mb
            FROM transcripts
            GROUP BY pays, flow
            ORDER BY pays, flow
            """
        )
        rows = cur.fetchall()
    return pd.DataFrame(rows)


@st.cache_data(ttl=300)
def fetch_audits_summary() -> pd.DataFrame:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.audit_version,
                   COUNT(*) AS n,
                   AVG(a.note_totale_sur_10)::numeric(4,2) AS note_moy,
                   SUM(CASE WHEN a.note_zero_par_SI THEN 1 ELSE 0 END) AS n_si
            FROM audits a
            GROUP BY a.audit_version
            ORDER BY n DESC
            """
        )
        rows = cur.fetchall()
    return pd.DataFrame(rows)


def fetch_transcripts_page(pays_filter: list[str] | None, flow_filter: list[str] | None,
                          size_min: int, limit: int = 50, offset: int = 0) -> pd.DataFrame:
    sql = "SELECT id, file_name, pays, flow, duree_secondes, size_bytes, ingested_at " \
          "FROM transcripts WHERE size_bytes >= %s"
    params: list = [size_min]
    if pays_filter:
        sql += " AND pays = ANY(%s)"
        params.append(pays_filter)
    if flow_filter:
        sql += " AND flow = ANY(%s)"
        params.append(flow_filter)
    sql += " ORDER BY ingested_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return pd.DataFrame(cur.fetchall())


def log_action(actor: str, action: str, target_id: str | None = None,
              target_type: str | None = None, details: dict | None = None) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit_log (actor, action, target_id, target_type, details) "
            "VALUES (%s, %s, %s, %s, %s)",
            (actor, action, target_id, target_type, details or {}),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_dashboard() -> None:
    st.title("📊 Dashboard")
    st.caption("Vue d'ensemble des transcripts et audits en base.")

    df_counts = fetch_counts_by_pays_flow()
    if df_counts.empty:
        st.warning("Aucun transcript en DB. Lance `python scripts/ingest_local_transcripts.py` d'abord.")
        return

    total_transcripts = int(df_counts["n"].sum())
    total_mb = int(df_counts["total_mb"].sum())
    duree_moy = int(df_counts["duree_moy_s"].mean()) if not df_counts.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Transcripts ingérés", f"{total_transcripts:,}")
    c2.metric("Volume DB", f"{total_mb} MB")
    c3.metric("Durée moyenne / appel", f"{duree_moy} s")

    st.subheader("Répartition pays × flow")
    pivot = df_counts.pivot_table(index="pays", columns="flow", values="n", fill_value=0)
    st.dataframe(pivot, use_container_width=True)

    st.subheader("Audits IA produits")
    df_audits = fetch_audits_summary()
    if df_audits.empty:
        st.info("Aucun audit IA pour l'instant. Lance le module 'Lancer un audit' pour démarrer.")
    else:
        st.dataframe(df_audits, use_container_width=True)


def page_transcripts() -> None:
    st.title("📜 Transcripts")

    c1, c2, c3 = st.columns(3)
    pays = c1.multiselect("Pays", ["FR", "GB", "DE", "PL", "CZ"], default=[])
    flow = c2.multiselect("Flow", ["cde_tel", "sav", "unknown"], default=[])
    size_min = c3.slider("Taille minimum (bytes)", 0, 5000, 500,
                         help="< 500B = silences / IVR-only, exclus par défaut.")

    df = fetch_transcripts_page(pays or None, flow or None, size_min)
    st.caption(f"{len(df)} transcripts affichés (max 50 par page).")

    if df.empty:
        st.info("Aucun transcript ne correspond aux filtres.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)


def page_lancer_audit() -> None:
    st.title("🤖 Lancer un audit IA")
    st.caption("Sélectionne un transcript, choisis le modèle, et lance l'audit Claude.")

    df = fetch_transcripts_page(None, None, 3000, limit=200)
    if df.empty:
        st.warning("Aucun transcript de taille suffisante (≥ 3 KB) à auditer.")
        return

    file_choice = st.selectbox(
        "Transcript à auditer",
        options=df["file_name"].tolist(),
        format_func=lambda f: f"{f} ({df[df.file_name==f].pays.iloc[0]} / {df[df.file_name==f].flow.iloc[0]})",
    )
    model = st.selectbox(
        "Modèle LLM",
        ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        index=0,
        help="Haiku ≈ 10× moins cher, Sonnet ≈ qualité supérieure.",
    )
    audit_version = st.text_input("Tag de version", value="ui_v1",
                                  help="Pour distinguer ce passage d'autres en DB.")

    if st.button("Lancer l'audit", type="primary"):
        transcript_id = df[df.file_name == file_choice]["id"].iloc[0]
        with st.spinner(f"Audit en cours sur {file_choice}..."):
            try:
                result = audit_one_file_from_db(
                    transcript_id=transcript_id,
                    audit_version=audit_version,
                    model=model,
                )
                log_action(username, "RUN_AUDIT", target_id=str(transcript_id),
                          target_type="transcript",
                          details={"audit_version": audit_version, "model": model})
                st.success(f"Audit créé : note {result.get('note_totale_sur_10', '?')}/10")
                st.json(result, expanded=False)
            except Exception as e:
                st.error(f"Erreur : {e}")


def _build_audit_dict(file_name: str, pays: str, langue: str, flow: str,
                       parsed_csv, llm_result: dict) -> dict:
    """Construit le dict attendu par fill_one_template à partir des résultats Claude."""
    n_tel_match = re.match(r"^(\d{8,15})_", file_name)
    n_tel = n_tel_match.group(1) if n_tel_match else ""
    n_appel = re.sub(r"\.(mp3\.csv|csv|mp3)$", "", file_name)

    audit = llm_result.get("parsed") or {}
    meta = audit.setdefault("metadata", {})
    meta.setdefault("n_appel", n_appel)
    meta.setdefault("n_tel", n_tel)
    meta.setdefault("pays", pays)
    meta.setdefault("langue_appel", langue)
    meta.setdefault("DMT_DMC", f"{parsed_csv.duree // 60:02d}:{parsed_csv.duree % 60:02d}")
    audit.setdefault("criteres", {})
    audit.setdefault("totaux", {})
    audit.setdefault("SI_detectees", [])
    return audit


def page_auto_audit() -> None:
    st.title("📤 Auto-audit : upload CSV → Excel")
    st.caption("Uploade un ou plusieurs CSV transcripts HappyScribe. "
               "L'app identifie le pays + flow (CdesTel/SAV) de chaque, "
               "lance Claude, et te génère les Excels BQ_1/BQ_4 par pays × flow.")

    files = st.file_uploader(
        "Sélectionne tes CSV transcripts (.mp3.csv ou .csv)",
        accept_multiple_files=True,
        type=["csv"],
    )
    if not files:
        st.info("📂 Aucun fichier sélectionné.")
        return

    c1, c2 = st.columns(2)
    model = c1.selectbox(
        "Modèle LLM",
        ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"],
        index=0,
        help="Haiku ≈ 10× moins cher mais qualité moindre. Sonnet pour la prod.",
    )
    max_files = c2.number_input(
        "Limite (sécurité)", min_value=1, max_value=200, value=min(20, len(files)),
        help="Cap le nombre de fichiers audités par run pour éviter de cramer du budget.",
    )

    files_to_run = files[: int(max_files)]
    st.write(f"**{len(files_to_run)} fichiers** seront audités "
             f"(sur {len(files)} uploadés). "
             f"Coût estimé : ~{len(files_to_run) * (0.01 if 'haiku' in model else 0.10):.2f} USD")

    if not st.button("🚀 Lancer l'audit", type="primary"):
        return

    results_by_pays_flow: dict[tuple[str, str], list[dict]] = {}
    skipped: list[tuple[str, str]] = []  # (filename, reason)
    progress = st.progress(0.0, text="Démarrage...")

    for i, f in enumerate(files_to_run):
        progress.progress(
            (i) / len(files_to_run),
            text=f"Audit {i+1}/{len(files_to_run)} : {f.name}",
        )
        try:
            content = f.read().decode("utf-8", errors="replace")
            parsed = parse_csv_transcript(content)
            pays, langue = detect_pays_langue(f.name)
            flow = detect_flow(parsed.text)
        except Exception as e:
            skipped.append((f.name, f"parse error : {e}"))
            continue

        if len(parsed.text) < 100:
            skipped.append((f.name, f"transcript trop court ({len(parsed.text)} chars)"))
            continue

        try:
            llm_result = audit_transcript(
                parsed.text, flow=flow, file_name=f.name,
                pays=pays, langue=langue, model=model,
            )
        except Exception as e:
            skipped.append((f.name, f"LLM error : {e}"))
            continue

        audit_dict = _build_audit_dict(f.name, pays, langue, flow, parsed, llm_result)
        results_by_pays_flow.setdefault((pays, flow), []).append(audit_dict)

    progress.progress(1.0, text=f"✅ Terminé : {sum(len(v) for v in results_by_pays_flow.values())} audits OK, "
                                f"{len(skipped)} skipped.")

    # --- Résumé par pays/flow ---
    if results_by_pays_flow:
        summary = [{"Pays": p, "Flow": fl, "Audits": len(v)}
                   for (p, fl), v in results_by_pays_flow.items()]
        st.subheader("Résultats par pays × flow")
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

    if skipped:
        st.subheader(f"⚠️ {len(skipped)} fichiers ignorés")
        st.dataframe(pd.DataFrame(skipped, columns=["Fichier", "Raison"]),
                     use_container_width=True, hide_index=True)

    if not results_by_pays_flow:
        st.warning("Aucun audit produit. Vérifie le contenu des fichiers.")
        return

    # --- Génération des Excels BQ et bundle ZIP ---
    with st.spinner("Génération des Excels BQ + bundle ZIP..."):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for (pays, flow), audits in results_by_pays_flow.items():
                template = TEMPLATE_CDE if flow == "cde_tel" else TEMPLATE_SAV
                cols = CDE_TEL_COLS if flow == "cde_tel" else SAV_COLS
                sheet_name = "Cde tél" if flow == "cde_tel" else "SAV"
                flow_label = "CdesTel" if flow == "cde_tel" else "SAV"
                prefix = "BQ_1_CdesTel" if flow == "cde_tel" else "BQ_4_Sav"
                arc_name = f"{pays}/{flow_label}/{prefix}_{pays}.xlsx"
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                try:
                    fill_one_template(template, tmp_path, pays, audits, cols, sheet_name)
                    zf.write(tmp_path, arcname=arc_name)
                finally:
                    tmp_path.unlink(missing_ok=True)

    st.download_button(
        "📦 Télécharger le pack Excel (ZIP)",
        zip_buffer.getvalue(),
        file_name="audits_atlas_for_men.zip",
        mime="application/zip",
        type="primary",
    )


def page_audits() -> None:
    st.title("📋 Audits IA produits")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.file_name, t.pays, t.flow,
                   a.audit_version, a.llm_model,
                   a.note_totale_sur_10, a.note_zero_par_SI, a.si_count,
                   a.created_at
            FROM audits a JOIN transcripts t ON t.id = a.transcript_id
            ORDER BY a.created_at DESC LIMIT 100
            """
        )
        rows = cur.fetchall()
    if not rows:
        st.info("Aucun audit en DB. Va dans 'Lancer un audit' pour en produire.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if page.startswith("📊"):
    page_dashboard()
elif page.startswith("📜"):
    page_transcripts()
elif page.startswith("🤖"):
    page_lancer_audit()
elif page.startswith("📤"):
    page_auto_audit()
elif page.startswith("📋"):
    page_audits()

st.sidebar.divider()
st.sidebar.caption("Atlas For Men — Audit IA — v1 interface interne")
