from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = "*"
    MAX_TEXT_CHARS: int = 12000
    HF_TIMEOUT_SECONDS: int = 30
    HF_MAX_RETRIES: int = 2

    HF_API_TOKEN: str = ""
    HF_SENTIMENT_MODEL: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    HF_ZERO_SHOT_MODEL: str = "facebook/bart-large-mnli"
    HF_SUMMARY_MODEL: str = "csebuetnlp/mT5_multilingual_XLSum"

    GOOGLE_SHEETS_SPREADSHEET_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""
    GOOGLE_SHEETS_TAB_NAME: str = "atendimentos"

    @property
    def cors_origins_list(self) -> List[str]:
        raw = self.CORS_ORIGINS
        origins = [item.strip() for item in raw.split(",") if item.strip()]
        return origins or ["*"]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env"
    )


settings = Settings()
