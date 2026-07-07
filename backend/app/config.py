from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://rastrowatch:rastrowatch@postgres:5432/rastrowatch"
    admin_user: str = "admin"
    admin_password: str = "cambia-esta-clave"
    session_secret: str = "cambia-este-secreto"
    uploads_dir: str = "/app/uploads"

    openai_api_key: str = ""
    openai_model: str = ""
    default_openai_vision_model: str = "gpt-5.5"
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_marketplace: str = "EBAY_ES"
    thewatchapi_key: str = ""
    watchcharts_api_key: str = ""
    apify_token: str = ""
    apify_wallapop_actor_id: str = ""
    apify_milanuncios_actor_id: str = ""
    apify_catawiki_actor_id: str = ""


settings = Settings()
