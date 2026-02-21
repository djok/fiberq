from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://fiberq:fiberq@localhost:5432/fiberq"
    database_sync_url: str = "postgresql://fiberq:fiberq@localhost:5432/fiberq"

    # Kanidm OIDC
    kanidm_url: str = ""
    kanidm_client_id: str = ""
    kanidm_api_token: str = ""
    kanidm_verify_tls: bool = True

    # API
    api_secret_key: str = "dev-secret-key"
    log_level: str = "info"

    # Storage
    storage_photos_dir: str = "/app/storage/photos"
    storage_gpkg_dir: str = "/app/storage/gpkg"

    # DB schema
    db_schema: str = "fiberq"

    @property
    def asyncpg_dsn(self) -> str:
        """Convert SQLAlchemy-style URL to plain asyncpg DSN."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
