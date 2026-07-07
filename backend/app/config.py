from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://rastrowatch:rastrowatch@postgres:5432/rastrowatch"
    admin_user: str = "admin"
    admin_password: str = "cambia-esta-clave"
    session_secret: str = "cambia-este-secreto"
    uploads_dir: str = "/app/uploads"


settings = Settings()
