#!/usr/bin/env python3
"""
WhatsApp Assistant — Entry Point
Initializes the database, then launches the Flask webhook server.
"""

import logging
from config.settings import settings
from state.database import init_db
from bot.whatsapp_bot import start as start_server

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    print(f"Starting WhatsApp webhook server on {settings.HOST}:{settings.PORT}...")
    start_server()
