"""Configuration centralisee via pydantic-settings + dotenv."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic (REQUIRED — audit IA ne tourne pas sans)
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-sonnet-4-6", alias="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(4096, alias="ANTHROPIC_MAX_TOKENS")

    # Google (optionnel — non utilisé par l'UI Streamlit, requis seulement pour l'ingest Drive)
    google_application_credentials: Path = Field(
        Path("./service_account.json"), alias="GOOGLE_APPLICATION_CREDENTIALS"
    )
    drive_folder_ids_transcripts: str = Field("", alias="DRIVE_FOLDER_IDS_TRANSCRIPTS")
    drive_folder_ids_recordings: str = Field("", alias="DRIVE_FOLDER_IDS_RECORDINGS")

    # Postgres (REQUIRED pour l'UI — sans DB, rien ne marche)
    database_url: str = Field("", alias="DATABASE_URL")

    # S3 (optionnel — non utilisé par l'UI, requis seulement pour upload_csv_to_bucket.py)
    s3_endpoint_url: str = Field("http://localhost:9000", alias="S3_ENDPOINT_URL")
    s3_bucket: str = Field("afm-audit-recordings", alias="S3_BUCKET")
    s3_region: str = Field("fr-par", alias="S3_REGION")
    s3_access_key: str = Field("", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field("", alias="S3_SECRET_KEY")
    s3_use_ssl: bool = Field(False, alias="S3_USE_SSL")

    # ASR
    deepgram_api_key: str = Field("", alias="DEEPGRAM_API_KEY")
    assemblyai_api_key: str = Field("", alias="ASSEMBLYAI_API_KEY")

    # Runtime
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    audit_batch_size: int = Field(10, alias="AUDIT_BATCH_SIZE")
    audit_output_dir: Path = Field(Path("./output"), alias="AUDIT_OUTPUT_DIR")
    prompts_dir: Path = Field(Path("./prompts"), alias="PROMPTS_DIR")

    @property
    def transcripts_folder_ids(self) -> list[str]:
        return [s.strip() for s in self.drive_folder_ids_transcripts.split(",") if s.strip()]

    @property
    def recordings_folder_ids(self) -> list[str]:
        return [s.strip() for s in self.drive_folder_ids_recordings.split(",") if s.strip()]


settings = Settings()  # singleton chargé une fois au démarrage
