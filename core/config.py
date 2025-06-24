# Единый конфигурационный файл для всего проекта
from pydantic_settings import BaseSettings
from pydantic import Field  # Если используете Field

class Settings(BaseSettings):
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    DB_DSN: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/onboard",
        env="DB_DSN",
    )
    QDRANT_URL: str = Field("http://localhost:6333", env="QDRANT_URL")
    ADMINS: list[int] = Field(default_factory=list, env="ADMINS")  # comma-sep ids
    ACCESS_ID: str = Field(..., env="ACCESS_ID")
    EMB_MODEL_NAME: str = Field(..., env="EMB_MODEL_NAME")
    GF_PASSWORD: str = Field (..., env="GF_PASSWORD")
    MODEL_PATH: str = Field(..., env="MODEL_PATH")
    TOP_K: str = Field(..., env="TOP_K")
    N_CTX: int = Field(..., env="N_CTX")
    LLM_ENDPOINT: str = Field(..., env="LLM_ENDPOINT")
    LLM_USER: str = Field(..., env="LLM_USER")
    LLM_PASS: str = Field(..., env="LLM_PASS")
    LLM_REMOTE: str = Field(..., env="LLM_REMOTE")
    SCENARIO_DIR: str = Field("data/scenarios", env="SCENARIO_DIR")

    class Config:
        env_file = ".env"
        env_prefix = ""   # без префикса, читаем как есть

settings = Settings()