# -*- coding: utf-8 -*-
"""Passkey Bot — Global Configuration & Environment Settings."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_PREFIX = os.getenv("BOT_PREFIX", ".") or "."
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///passkey.db")
    TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "")
    TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")
    
    # Render automatically sets PORT (e.g., 10000)
    DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT", "8000")))
    
    # Render provides RENDER_EXTERNAL_URL (e.g., https://your-service.onrender.com)
    DASHBOARD_URL = os.getenv("DASHBOARD_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000"
    DASHBOARD_URL = DASHBOARD_URL.rstrip("/")
    
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1399740322883567646")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
    SHIELD_ADMIN_KEY = os.getenv("SHIELD_ADMIN_KEY", "passkey_admin_secret")

    # Zoho Mail SMTP Settings for Email OTP Verification
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.zoho.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # 465 (SSL) or 587 (TLS)
    SMTP_USER = os.getenv("SMTP_USER", "passkeybot@zohomail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "NH1R6GnDuu7A")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Passkey Security Gatekeeper")

    # Cloudflare Turnstile CAPTCHA (Bot Protection for Web Portal)
    # Default testing keys provided by Cloudflare: 1x00000000000000000000AA (always passes)
    CF_TURNSTILE_SITEKEY = os.getenv("CF_TURNSTILE_SITEKEY", "1x00000000000000000000AA")
    CF_TURNSTILE_SECRET = os.getenv("CF_TURNSTILE_SECRET", "1x0000000000000000000000000000000AA")
