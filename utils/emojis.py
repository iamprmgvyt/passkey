# -*- coding: utf-8 -*-
"""
Passkey Bot — Complete Dynamic Custom Emoji System.
Seamlessly maps all 12 Custom Passkey Neon Emojis (from /static/emojis/)
once uploaded to your Discord Application / Server, with clean fallback support.
"""
from typing import Optional
import discord

class Emojis:
    """Emoji registry for Passkey Custom Icons."""
    
    # Custom Emoji Name Mapping (matches files in /static/emojis/)
    NAMES = {
        "passkey": "pk_passkey",
        "shield": "pk_shield",
        "otp": "pk_otp",
        "alt": "pk_alt",
        "verified": "pk_verified",
        "warn": "pk_warn",
        "ban": "pk_ban",
        "lock": "pk_lock",
        "unlock": "pk_unlock",
        "biometric": "pk_biometric",
        "image_captcha": "pk_image_captcha",
        "pattern": "pk_pattern",
        "social": "pk_social",
        "rules": "pk_rules",
        "turnstile": "pk_turnstile",
        "dot_green": "pk_green",
        "dot_red": "pk_red"
    }

    # Fallback Unicode Emojis
    FALLBACKS = {
        "passkey": "🔑",
        "shield": "🛡️",
        "otp": "✉️",
        "alt": "👥",
        "verified": "✅",
        "warn": "⚠️",
        "ban": "🔨",
        "lock": "🔒",
        "unlock": "🔓",
        "biometric": "📱",
        "image_captcha": "🖼️",
        "pattern": "🎮",
        "social": "🔗",
        "rules": "📜",
        "turnstile": "🌐",
        "dot_green": "🟢",
        "dot_red": "🔴",
        "prev": "◀️",
        "next": "▶️",
        "deploy": "🚀",
        "wizard": "✨"
    }

    @classmethod
    def get(cls, key: str, bot: Optional[discord.Client] = None) -> str:
        """Get custom emoji string <:name:id> if found in bot's guilds, else fallback."""
        target_name = cls.NAMES.get(key, key)
        
        if bot:
            # Check bot's global emojis
            emoji = discord.utils.get(bot.emojis, name=target_name)
            if emoji:
                return str(emoji)

        return cls.FALLBACKS.get(key, "🔹")
