from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://fiberq:fiberq@localhost:5432/fiberq"
    database_sync_url: str = "postgresql://fiberq:fiberq@localhost:5432/fiberq"

    # Zitadel OIDC
    zitadel_domain: str = ""
    zitadel_client_id: str = ""
    zitadel_project_id: str = ""

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
