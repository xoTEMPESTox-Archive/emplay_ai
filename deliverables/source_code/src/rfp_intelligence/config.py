import os
from pathlib import Path
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """Find the root repository directory containing deliverables/ and README.md."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "deliverables").exists() and (parent / "README.md").exists():
            return parent
    return Path(__file__).resolve().parent.parent.parent.parent


REPO_ROOT = get_project_root()


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=[
            str(REPO_ROOT / ".env"),
            str(REPO_ROOT / "deliverables" / "source_code" / ".env"),
        ],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider & Model Settings (LiteLLM model identifiers)
    llm_model: str = Field(
        default="groq/openai/gpt-oss-120b",
        validation_alias=AliasChoices("LLM_MODEL", "AI_MODEL"),
    )
    validator_llm_model: str = Field(
        default="groq/openai/gpt-oss-120b",
        validation_alias=AliasChoices("VALIDATOR_LLM_MODEL", "AI_MODEL"),
    )
    embedding_model: str = Field(
        default="ollama/qwen3-embedding:0.6b",
        validation_alias=AliasChoices("EMBEDDING_MODEL"),
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    # API Keys for Cloud Providers (LiteLLM routes automatically)
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Storage Paths (resolved relative to repository root)
    vector_db_dir: Path = Field(
        default=REPO_ROOT / "deliverables" / "source_code" / "data" / "processed" / "chroma",
        alias="VECTOR_DB_DIR",
    )
    processed_data_dir: Path = Field(
        default=REPO_ROOT / "deliverables" / "source_code" / "data" / "processed",
        alias="PROCESSED_DATA_DIR",
    )
    outputs_dir: Path = Field(
        default=REPO_ROOT / "deliverables" / "outputs", alias="OUTPUTS_DIR"
    )
    company_profile_path: Path = Field(
        default=REPO_ROOT
        / "deliverables"
        / "source_code"
        / "data"
        / "company_capabilities.json",
        alias="COMPANY_PROFILE_PATH",
    )

    # Runtime Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    top_k_retrieval: int = Field(default=5, alias="TOP_K_RETRIEVAL")
    max_validation_retries: int = Field(default=2, alias="MAX_VALIDATION_RETRIES")
    enable_semantic_cache: bool = Field(default=True, alias="ENABLE_SEMANTIC_CACHE")


# Singleton instance
settings = Settings()

if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.groq_api_key:
    os.environ["GROQ_API_KEY"] = settings.groq_api_key
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

