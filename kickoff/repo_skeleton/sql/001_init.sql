-- Atlas For Men — schéma Postgres initial
-- Hébergement EU obligatoire (RGPD)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------------
-- TRANSCRIPTS — métadonnées des appels ingérés
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transcripts (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  drive_file_id     TEXT UNIQUE NOT NULL,
  file_name         TEXT NOT NULL,
  pays              CHAR(2) NOT NULL,           -- FR, GB, DE, PL, CZ
  langue            VARCHAR(8) NOT NULL,        -- fr, en, de, pl, cs
  n_tel             TEXT,
  n_appel           TEXT NOT NULL,              -- basename sans .mp3.csv
  duree_secondes    INT,
  size_bytes        INT NOT NULL,
  flow              VARCHAR(16),                -- cde_tel | sav | unknown
  ingested_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  raw_text          TEXT,                       -- transcript concaténé
  recording_s3_key  TEXT                        -- path dans le bucket S3 si MP3 attaché
);

CREATE INDEX IF NOT EXISTS idx_transcripts_pays_flow ON transcripts(pays, flow);
CREATE INDEX IF NOT EXISTS idx_transcripts_ingested_at ON transcripts(ingested_at DESC);

-- ------------------------------------------------------------------
-- AUDITS — résultats des passages IA
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audits (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transcript_id            UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
  audit_version            VARCHAR(32) NOT NULL,   -- ex: 'v1', 'v2_n8n', 'v2_python'
  llm_model                VARCHAR(64) NOT NULL,   -- ex: 'claude-sonnet-4-6'
  prompt_hash              VARCHAR(64),            -- sha256 du prompt utilisé
  flow                     VARCHAR(16) NOT NULL,   -- cde_tel | sav
  agent                    TEXT,
  n_client                 TEXT,
  type                     TEXT,
  demande_client           TEXT,
  note_totale_sur_10       NUMERIC(4,2),
  note_sur_100             INT,
  note_zero_par_SI         BOOLEAN NOT NULL DEFAULT FALSE,
  si_count                 INT NOT NULL DEFAULT 0,
  commentaire_global       TEXT,
  commentaire_traduit_fr   TEXT,
  criteres_jsonb           JSONB NOT NULL,        -- 15-16 critères structurés
  si_jsonb                 JSONB,                 -- liste SI détectées
  raw_llm_response         TEXT,                  -- pour debug / audit IA
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audits_transcript ON audits(transcript_id);
CREATE INDEX IF NOT EXISTS idx_audits_version ON audits(audit_version);
CREATE INDEX IF NOT EXISTS idx_audits_flow ON audits(flow);
CREATE INDEX IF NOT EXISTS idx_audits_si ON audits(si_count) WHERE si_count > 0;
CREATE INDEX IF NOT EXISTS idx_audits_zero_si ON audits(note_zero_par_SI) WHERE note_zero_par_SI = TRUE;
CREATE INDEX IF NOT EXISTS idx_audits_criteres ON audits USING gin(criteres_jsonb);

-- ------------------------------------------------------------------
-- HUMAN_AUDITS — gold standard humain pour calibration
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS human_audits (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transcript_id            UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
  evaluateur               TEXT NOT NULL,
  date_audit               DATE NOT NULL,
  flow                     VARCHAR(16) NOT NULL,
  note_totale_sur_10       NUMERIC(4,2),
  criteres_jsonb           JSONB NOT NULL,
  commentaire              TEXT,
  source_excel_file        TEXT,                  -- nom du fichier Excel d'origine
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_human_audits_transcript ON human_audits(transcript_id);

-- ------------------------------------------------------------------
-- CALIBRATION_RESULTS — écarts IA vs humain
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calibration_results (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  human_audit_id      UUID NOT NULL REFERENCES human_audits(id) ON DELETE CASCADE,
  ia_audit_id         UUID NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
  ecart_note_totale   NUMERIC(4,2),               -- ia - humain
  ecart_par_critere   JSONB,                      -- {critere: ecart}
  agreement_global    NUMERIC(4,2),               -- 0.0 à 1.0
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_calib UNIQUE (human_audit_id, ia_audit_id)
);

-- ------------------------------------------------------------------
-- AUDIT_LOG — actions sensibles (RGPD : qui a vu quoi)
-- ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor       TEXT NOT NULL,           -- email ou service account
  action      TEXT NOT NULL,           -- READ_TRANSCRIPT, EXPORT_AUDITS, etc.
  target_id   UUID,
  target_type TEXT,
  details     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- ------------------------------------------------------------------
-- VIEW : derniers audits par appel
-- ------------------------------------------------------------------
CREATE OR REPLACE VIEW v_latest_audits AS
SELECT DISTINCT ON (t.id)
  t.id AS transcript_id, t.file_name, t.pays, t.flow, t.duree_secondes,
  a.id AS audit_id, a.audit_version, a.llm_model,
  a.note_totale_sur_10, a.note_zero_par_SI, a.si_count,
  a.created_at AS audit_created_at
FROM transcripts t
JOIN audits a ON a.transcript_id = t.id
ORDER BY t.id, a.created_at DESC;

COMMENT ON TABLE transcripts IS 'Métadonnées des transcripts ingérés depuis Drive';
COMMENT ON TABLE audits IS 'Résultats des audits IA (1 audit = 1 passage prompt+modèle)';
COMMENT ON TABLE human_audits IS 'Audits humains servant de gold standard';
COMMENT ON TABLE calibration_results IS 'Écart IA vs humain pour mesurer la qualité';
COMMENT ON TABLE audit_log IS 'Traçabilité RGPD : qui accède à quoi';
