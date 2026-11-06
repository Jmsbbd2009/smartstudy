import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./development.db")
    secret: str = os.getenv("JWT_SECRET", "")
    environment: str = os.getenv("APP_ENV", "development")
    redis_url: str = os.getenv("REDIS_URL", "")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    origins: tuple = tuple(os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","))
    ai_url: str = os.getenv("AI_BASE_URL", "")
    ai_key: str = os.getenv("AI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "")
    moderation_url: str = os.getenv("AI_MODERATION_URL", "")

    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_username: str = os.getenv("TELEGRAM_BOT_USERNAME", "un_censoredai_Bot")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    passkey_rp_id: str = os.getenv("PASSKEY_RP_ID", "localhost")
    passkey_origin: str = os.getenv("PASSKEY_ORIGIN", "http://localhost:5173")
    ai_provider: str = os.getenv("AI_PROVIDER", "compatible")
    hf_token: str = os.getenv("HF_TOKEN", "")
    hf_model: str = os.getenv("HF_MODEL", "Qwen/Qwen3-32B")
    hf_guard_model: str = os.getenv("HF_GUARD_MODEL", "meta-llama/Llama-Guard-4-12B")

    groq_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    groq_guard_model: str = os.getenv("GROQ_GUARD_MODEL", "openai/gpt-oss-safeguard-20b")
    deepseek_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")

    def validate(self):
        if len(self.secret) < 32 or self.secret.startswith("replace-"):
            raise RuntimeError("JWT_SECRET must be a randomly generated secret of at least 32 characters")
        if self.environment == "production":
            if not self.database_url.startswith("postgresql") or not self.redis_url:
                raise RuntimeError("Production requires PostgreSQL and Redis")
            if any(not origin.startswith("https://") for origin in self.origins):
                raise RuntimeError("Production CORS origins must use HTTPS")


settings = Settings()
