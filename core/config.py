from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    REGION: str
    DATABASE_URL: str
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    DISABLE_EMAILS: bool
    DYNAMODB_LIRA_ROLE_POLICIES_TABLE_NAME: str
    DYNAMODB_USERS_ACCESS_TABLE_NAME: str

settings = Settings()