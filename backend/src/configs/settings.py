from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    # Database (our Postgres/pgvector)
    db_host: str = "0.0.0.0"
    db_port: int = 5432
    db_user: str = "sqlhelper"
    db_password: str = "sqlhelper"
    db_name: str = "vectordb"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 3600

    # Encryption key for storing data-source credentials
    # Override via ENCRYPTION_KEY env var in production
    encryption_key: str = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="

    # Embedding model for semantic search
    embedding_model: str = "all-MiniLM-L6-v2"

    # External services (wired in later features)
    temporal_address: str = "localhost:7233"
    minio_endpoint: str = "localhost:9000"
    minio_public_endpoint: str = ""  # browser-accessible host; falls back to minio_endpoint
    minio_access_key: str = "sqlhelper"
    minio_secret_key: str = "sqlhelper"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # LLM provider: "openai" | "gemini"
    llm_provider: str = "openai"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"

    @property
    def llm_model(self) -> str:
        if self.llm_provider == "gemini":
            return self.gemini_model
        return self.openai_model

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
