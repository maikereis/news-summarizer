from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="OPENAI_", protected_namespaces=("settings_",))
    model_id: str = Field("gpt-4o-mini", json_schema_extra={"env": "MODEL_ID"})
    api_key: SecretStr | None = Field(None, json_schema_extra={"env": "API_KEY"})


class HuggingFaceSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="HUGGINGFACE_")
    access_token: SecretStr | None = Field(None, json_schema_extra={"env": "ACCESS_TOKEN"})


class MongoSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="MONGO_")
    name: str = Field("name", json_schema_extra={"env": "NAME"})
    username: str = Field("user", json_schema_extra={"env": "USERNAME"})
    password: SecretStr = Field("pass", json_schema_extra={"env": "PASSWORD"})
    host: str = Field("localhost", json_schema_extra={"env": "HOST"})
    port: int = Field(27017, json_schema_extra={"env": "PORT"})

    @property
    def dsn(self) -> str:
        return f"mongodb://{self.username}:{self.password.get_secret_value()}@{self.host}:{self.port}"


class AWSSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="AWS_")
    region: str = Field("sa-east-1", json_schema_extra={"env": "REGION"})
    access_key: str | None = Field(None, json_schema_extra={"env": "ACCESS_KEY"})
    secret_key: SecretStr | None = Field(None, json_schema_extra={"env": "SECRET_KEY"})
    arn_role: str | None = Field(None, json_schema_extra={"env": "ARN_ROLE"})


class QdrantSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="QDRANT_")
    use_cloud: bool = Field(False, json_schema_extra={"env": "USE_CLOUD"})
    host: str = Field("localhost", json_schema_extra={"env": "DATABASE_HOST"})
    rest_port: int = Field(6333, json_schema_extra={"env": "REST_API_PORT"})
    grpc_port: int = Field(6334, json_schema_extra={"env": "GRPC_API_PORT"})
    cloud_url: str = Field("", json_schema_extra={"env": "CLOUD_URL"})
    apikey: SecretStr | None = Field(None, json_schema_extra={"env": "APIKEY"})


class RAGSettings(BaseSettings):
    model_config = SettingsConfigDict(env=".env", env_prefix="RAG_", protected_namespaces=("settings_",))
    embedding_model_id: str = Field(None, json_schema_extra={"env": "EMBEDDING_MODEL_ID"})
    reranking_cross_encoder_model_id: str = Field(None, json_schema_extra={"env": "RERANKING_CROSS_ENCODER_MODEL_ID"})
    model_device: str = Field("cpu", json_schema_extra={"env": "MODEL_DEVICE"})


class Settings:
    def __init__(self):
        self.openai = OpenAISettings()
        self.huggingface = HuggingFaceSettings()
        self.mongo = MongoSettings()
        self.aws = AWSSettings()
        self.qdrant = QdrantSettings()
        self.rag = RAGSettings()

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from environment variables or defaults.
        """
        return cls()


settings = Settings.load_settings()
