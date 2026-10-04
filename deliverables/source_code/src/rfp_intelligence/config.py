"""Configuration settings for RFP Intelligence Platform."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings (LiteLLM model identifiers)
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    llm_model: str = Field(default="gemini/gemini-2.0-flash", alias="LLM_MODEL")
    validator_llm_model: str = Field(
        default="gemini/gemini-2.0-flash", alias="VALIDATOR_LLM_MODEL"
    )

    # Embedding Settings
    embedding_model: str = Field(
        default="gemini/text-embedding-004", alias="EMBEDDING_MODEL"
    )

    # Storage Paths
    vector_db_dir: Path = Field(
        default=Path("data/processed/chroma"), alias="VECTOR_DB_DIR"
    )
    processed_data_dir: Path = Field(
        default=Path("data/processed"), alias="PROCESSED_DATA_DIR"
    )
    outputs_dir: Path = Field(
        default=Path("deliverables/outputs"), alias="OUTPUTS_DIR"
    )

    # Runtime Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    top_k_retrieval: int = Field(default=5, alias="TOP_K_RETRIEVAL")
    max_validation_retries: int = Field(default=2, alias="MAX_VALIDATION_RETRIES")


# Singleton instance
settings = Settings()
