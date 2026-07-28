import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SourcePilot AI API"
    VERSION: str = "0.2.0"  # Phase 2
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Auth Security
    SECRET_KEY: str = "sourcepilot_super_secret_jwt_key_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite:///./sourcepilot.db"
    
    # AI Credentials
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Search Connectors
    SEARCH_CONNECTOR_TYPE: str = "mock"  # "mock", "serper", "tavily"
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    
    # Phase 2 — Marketplace Connector (optional; mock if not set)
    MARKETPLACE_API_KEY: Optional[str] = os.getenv("MARKETPLACE_API_KEY", "")
    MARKETPLACE_API_URL: Optional[str] = os.getenv("MARKETPLACE_API_URL", "")
    
    # Phase 2 — Trade Registry Connector (optional; mock if not set)
    REGISTRY_API_KEY: Optional[str] = os.getenv("REGISTRY_API_KEY", "")
    REGISTRY_API_URL: Optional[str] = os.getenv("REGISTRY_API_URL", "")
    
    # Phase 2 — Review Site Connector (optional; mock if not set)
    REVIEW_SITE_API_KEY: Optional[str] = os.getenv("REVIEW_SITE_API_KEY", "")
    REVIEW_SITE_API_URL: Optional[str] = os.getenv("REVIEW_SITE_API_URL", "")
    
    # Email Provider
    EMAIL_PROVIDER_TYPE: str = "mailtrap"  # "mailtrap", "sendgrid", "ses"
    MAILTRAP_HOST: str = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
    MAILTRAP_PORT: int = int(os.getenv("MAILTRAP_PORT", "2525"))
    MAILTRAP_USERNAME: str = os.getenv("MAILTRAP_USERNAME", "mock_username")
    MAILTRAP_PASSWORD: str = os.getenv("MAILTRAP_PASSWORD", "mock_password")
    SENDER_EMAIL: str = "rfq@sourcepilot.ai"
    SENDER_NAME: str = "SourcePilot AI Procurement System"
    
    # Phase 2 — Inbound Email Webhook
    INBOUND_EMAIL_WEBHOOK_SECRET: Optional[str] = os.getenv("INBOUND_EMAIL_WEBHOOK_SECRET", "sourcepilot_webhook_secret")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
