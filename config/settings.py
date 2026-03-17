import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # WhatsApp Business Cloud API
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ALLOWED_NUMBERS: list[str] = [
        n.strip() for n in os.getenv("WHATSAPP_ALLOWED_NUMBERS", "").split(",") if n.strip()
    ]

    # AI Provider — "anthropic" or "openai"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "anthropic")

    # Claude / Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Notion
    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    NOTION_NOTES_PAGE_ID: str = os.getenv("NOTION_NOTES_PAGE_ID", "")
    NOTION_TODOS_DB_ID: str = os.getenv("NOTION_TODOS_DB_ID", "")

    # Database
    DB_PATH: str = os.getenv("DB_PATH", "./assistant.db")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))

    # Misc
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "30"))


settings = Settings()
