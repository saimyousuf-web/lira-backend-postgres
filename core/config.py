from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    # --- AWS Config ---
    REGION: str
    # --- Postgresql Config ---
    DATABASE_URL: str
     # --- Cognito ---
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    DISABLE_EMAILS: bool
    DYNAMODB_LIRA_ROLE_POLICIES_TABLE_NAME: str
    DYNAMODB_USERS_ACCESS_TABLE_NAME: str
    # --- S3 ----
    S3_BASE_FILE_URL: str | None = None
    S3_BUCKET_NAME : str 
    QDRANT_URL: str 
    QDRANT_API_KEY: str
    QDRANT_COLLECTION : str
    QDRANT_COLLECTION: str
    S3_BASE_FILE_URL: str | None = None
    # --- Ollama (local LLM) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    # --- Local embeddings ---
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"

settings = Settings()