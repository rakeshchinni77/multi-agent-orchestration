from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings
    APP_NAME: str = "Multi-Agent AI Orchestrator"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database Configuration (PostgreSQL 15+)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/agent_orchestrator",
        description="Async PostgreSQL connection string using asyncpg driver"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/agent_orchestrator",
        description="Synchronous PostgreSQL connection string for migrations/celery"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis & Celery Message Broker (Redis 7+)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and state pub/sub"
    )
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL (Redis DB 0)"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/1",
        description="Celery task result backend (Redis DB 1)"
    )

    # Groq / LLM Configuration
    LLM_API_KEY: str = Field(
        default="",
        description="Generic LLM API key alias"
    )
    GROQ_API_KEY: str = Field(
        default="",
        description="API key for Groq Cloud LLM inference"
    )
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Primary Groq model name with function-calling support"
    )
    LLM_TEMPERATURE: float = 0.2
    LLM_TIMEOUT: float = 45.0

    # External Tool API Keys
    BRAVE_SEARCH_API_KEY: str = Field(
        default="",
        description="Brave Search REST API key"
    )
    OPENWEATHER_API_KEY: str = Field(
        default="",
        description="OpenWeatherMap REST API key"
    )

    # CORS configuration
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
