from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mongo
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "ledgerline_bank"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 30

    # Auth
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # GenAI
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    # Fraud rules
    fraud_large_txn_amount: float = 100000
    fraud_velocity_count: int = 5
    fraud_velocity_window_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
