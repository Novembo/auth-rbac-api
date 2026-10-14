"""Configuration de l'application, lue depuis les variables d'environnement."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Base de données : SQLite par défaut en local, surchargeable en production
    # (ex. postgresql+psycopg://user:pass@host/dbname).
    database_url: str = "sqlite:///./data/app.db"

    # Clé de signature des JWT — à changer impérativement en production.
    # Génère-en une avec : python -c "import secrets; print(secrets.token_urlsafe(32))"
    secret_key: str = "WK-j43yi8Ziwtg7WAiTHFxLxlnoOE6WpRPo473vGH7w"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Origines autorisées à appeler l'API (séparées par des virgules).
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
