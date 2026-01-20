from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OA_", case_sensitive=False)

    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60 * 8
    db_url: str = "sqlite:///./oa.db"
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
