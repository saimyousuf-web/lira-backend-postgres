from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- AWS Config ---
    REGION: str | None = None
    # --- Cognito ---
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    DISABLE_EMAILS: bool

    DATABASE_URL: str


settings = Settings()