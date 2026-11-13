from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_url: str
    pg_url: str
    secret_key: str
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()