from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://agenda:agenda@localhost:5432/agenda"

    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"

    secret_key: str = "change-me-dev-only"
    session_cookie_name: str = "session_id"
    session_cookie_secure: bool = False
    session_ttl_days: int = 7

    clinic_timezone: str = "Europe/Brussels"

    # itsme OIDC — leave blank to use the mock identity provider.
    itsme_issuer: str | None = None
    itsme_client_id: str | None = None
    itsme_client_secret: str | None = None
    itsme_redirect_uri: str = "http://localhost:8000/api/v1/auth/itsme/callback"
    itsme_scopes: str = "openid profile"

    @property
    def itsme_configured(self) -> bool:
        return bool(self.itsme_issuer and self.itsme_client_id and self.itsme_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
