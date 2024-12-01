from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="OPENAI_", protected_namespaces=("settings_",))
    model_id: str = Field(None, env="MODEL_ID")
    api_key: SecretStr | None = Field(None, env="API_KEY")


class HuggingFaceSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="HUGGINGFACE_")
    access_token: SecretStr | None = Field(None, env="ACCESS_TOKEN")


class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="MONGO_")
    username: str = Field("user", env="USERNAME")
    password: SecretStr = Field("pass", env="PASSWORD")
    host: str = Field("localhost", env="HOST")
    port: int = Field(27017, env="PORT")

    @property
    def dsn(self) -> str:
        return f"mongodb://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}"


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="AWS_")
    region: str = Field("sa-east-1", env="REGION")
    access_key: str | None = Field(None, env="ACCESS_KEY")
    secret_key: SecretStr | None = Field(None, env="SECRET_KEY")
    arn_role: str | None = Field(None, env="ARN_ROLE")


class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="QDRANT_")
    use_cloud: bool = Field(False, env="USE_CLOUD")
    host: str = Field("localhost", env="DATABASE_HOST")
    port: int = Field(6333, env="DATABASE_PORT")
    cloud_url: str = Field("", env="CLOUD_URL")
    apikey: SecretStr | None = Field(None, env="APIKEY")


class Settings:
    def __init__(self):
        self.openai = OpenAISettings()
        self.huggingface = HuggingFaceSettings()
        self.mongo = MongoSettings()
        self.aws = AWSSettings()
        self.qdrant = QdrantSettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from environment variables or defaults.
        """
        return cls()


settings = Settings.load_settings()
