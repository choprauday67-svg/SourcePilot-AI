import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SourcePilot AI API"
    VERSION: str = "0.4.0"  # Phase 4
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Auth Security
    SECRET_KEY: str = "sourcepilot_super_secret_jwt_key_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 24 hours

    # Phase 4 — Dedicated Fernet Encryption Key for OAuth Token Encryption (do NOT derive from SECRET_KEY)
    # Default key is a valid Fernet 32-byte base64 key for development
    FERNET_KEY: str = os.getenv(
        "FERNET_KEY",
        "w67v_L7a2q4t9z2Y8X9W0v1U2t3S4r5Q6P7O8N9M0L8="
    )
    
    # Database
    DATABASE_URL: str = "sqlite:///./sourcepilot.db"
    
    # AI Credentials
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Search Connectors
    SEARCH_CONNECTOR_TYPE: str = "mock"  # "mock", "serper", "tavily", "bing"
    SERPER_API_KEY: Optional[str] = os.getenv("SERPER_API_KEY", "")
    TAVILY_API_KEY: Optional[str] = os.getenv("TAVILY_API_KEY", "")
    BING_SEARCH_API_KEY: Optional[str] = os.getenv("BING_SEARCH_API_KEY", "")
    
    # Marketplace & Trade Registry Connectors
    MARKETPLACE_API_KEY: Optional[str] = os.getenv("MARKETPLACE_API_KEY", "")
    MARKETPLACE_API_URL: Optional[str] = os.getenv("MARKETPLACE_API_URL", "")
    REGISTRY_API_KEY: Optional[str] = os.getenv("REGISTRY_API_KEY", "")
    REGISTRY_API_URL: Optional[str] = os.getenv("REGISTRY_API_URL", "")
    REVIEW_SITE_API_KEY: Optional[str] = os.getenv("REVIEW_SITE_API_KEY", "")
    REVIEW_SITE_API_URL: Optional[str] = os.getenv("REVIEW_SITE_API_URL", "")
    
    # Email Provider (Legacy Fallback)
    EMAIL_PROVIDER_TYPE: str = "mailtrap"
    MAILTRAP_HOST: str = os.getenv("MAILTRAP_HOST", "sandbox.smtp.mailtrap.io")
    MAILTRAP_PORT: int = int(os.getenv("MAILTRAP_PORT", "2525"))
    MAILTRAP_USERNAME: str = os.getenv("MAILTRAP_USERNAME", "mock_username")
    MAILTRAP_PASSWORD: str = os.getenv("MAILTRAP_PASSWORD", "mock_password")
    SENDER_EMAIL: str = "rfq@sourcepilot.ai"
    SENDER_NAME: str = "SourcePilot AI Procurement System"
    
    # Phase 2 — Inbound Email Webhook
    INBOUND_EMAIL_WEBHOOK_SECRET: Optional[str] = os.getenv("INBOUND_EMAIL_WEBHOOK_SECRET", "sourcepilot_webhook_secret")

    # Phase 4 — OAuth 2.0 Credentials (Gmail & Outlook)
    MOCK_OAUTH: bool = os.getenv("MOCK_OAUTH", "true").lower() == "true"
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "mock_gmail_client_id")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "mock_gmail_client_secret")
    GMAIL_REDIRECT_URI: str = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:5173/oauth/callback/gmail")

    OUTLOOK_CLIENT_ID: str = os.getenv("OUTLOOK_CLIENT_ID", "mock_outlook_client_id")
    OUTLOOK_CLIENT_SECRET: str = os.getenv("OUTLOOK_CLIENT_SECRET", "mock_outlook_client_secret")
    OUTLOOK_REDIRECT_URI: str = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:5173/oauth/callback/outlook")

    # Phase 4 — Attachment Limits for Quotation Extraction
    MAX_ATTACHMENT_SIZE_MB: int = 10
    ALLOWED_ATTACHMENT_EXTENSIONS: List[str] = [
        ".pdf", ".csv", ".xlsx", ".xls", ".doc", ".docx", ".png", ".jpg", ".txt", ".json"
    ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
