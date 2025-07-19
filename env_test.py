from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, BaseModel

class label_config(BaseModel): 
    LABEL: SecretStr

class Settings(BaseSettings):
    label: label_config

    BROKER_CONFIG__API_KEY: str
    BROKER_CONFIG__API_SECRET: str
    APP_CONFIG__PRIVATE_KEY: str
    APP_CONFIG__WALLET_MAP_JSON: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_nested_delimiter="__")


print(Settings().model_dump())
