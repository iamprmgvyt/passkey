# -*- coding: utf-8 -*-
"""
Passkey Bot — Complete Dynamic Custom Emoji System.
Automatically uploads all 12 Custom Passkey Neon Emojis (from /static/emojis/)
directly into Discord Servers upon bot join or setup!
"""
import os
import logging
from typing import Optional, Dict
import discord

log = logging.getLogger("passkey.emojis")

class Emojis:
    """Emoji registry & auto-uploader for Passkey Custom Neon Icons."""
    
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
        "rules": "pk_lock",
        "turnstile": "pk_verified",
        "dot_green": "pk_verified",
        "dot_red": "pk_warn"
    }

    FILE_MAP = {
        "pk_passkey": "static/emojis/passkey.png",
        "pk_shield": "static/emojis/shield.png",
        "pk_otp": "static/emojis/otp.png",
        "pk_alt": "static/emojis/alt.png",
        "pk_verified": "static/emojis/verified.png",
        "pk_warn": "static/emojis/warn.png",
        "pk_ban": "static/emojis/ban.png",
        "pk_lock": "static/emojis/lock.png",
        "pk_biometric": "static/emojis/biometric.png",
        "pk_image_captcha": "static/emojis/image_captcha.png",
        "pk_pattern": "static/emojis/pattern.png",
        "pk_social": "static/emojis/social.png",
    }

    # Fallback Unicode Emojis (used only if guild emoji slots are completely full)
    FALLBACKS = {
        "passkey": "",
        "shield": "",
        "otp": "",
        "alt": "",
        "verified": "",
        "warn": "",
        "ban": "",
        "lock": "",
        "unlock": "",
        "biometric": "",
        "image_captcha": "",
        "pattern": "",
        "social": "",
        "rules": "",
        "turnstile": "",
        "dot_green": "",
        "dot_red": "",
        "prev": "",
        "next": "",
        "deploy": "",
        "wizard": ""
    }

    @classmethod
    def get(cls, key: str, bot: Optional[discord.Client] = None, guild: Optional[discord.Guild] = None) -> str:
        """Get custom emoji string <:name:id> if found in guild or bot's cache, else fallback."""
        target_name = cls.NAMES.get(key, key)
        
        # 1. Search in specific guild
        if guild:
            emoji = discord.utils.get(guild.emojis, name=target_name)
            if emoji:
                return str(emoji)

        # 2. Search across all guilds bot has access to
        if bot:
            emoji = discord.utils.get(bot.emojis, name=target_name)
            if emoji:
                return str(emoji)

        return cls.FALLBACKS.get(key, "")

    @classmethod
    async def ensure_guild_emojis(cls, guild: discord.Guild) -> Dict[str, str]:
        """Automatically upload all 12 Custom Passkey Neon Emojis into guild."""
        if not guild.me.guild_permissions.manage_emojis_and_stickers and not guild.me.guild_permissions.administrator:
            log.warning(f"Bot lacks manage_emojis permission in {guild.name}")
            return {}

        existing = {e.name: e for e in guild.emojis}
        uploaded = {}

        for name, file_path in cls.FILE_MAP.items():
            if name in existing:
                uploaded[name] = str(existing[name])
                continue

            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        img_bytes = f.read()
                    new_emoji = await guild.create_custom_emoji(
                        name=name,
                        image=img_bytes,
                        reason="[Passkey Gatekeeper] Auto-upload custom neon emojis pack"
                    )
                    uploaded[name] = str(new_emoji)
                    log.info(f" Successfully uploaded custom emoji {name} to {guild.name}")
                except Exception as e:
                    log.warning(f"Could not upload emoji {name} to {guild.name}: {e}")

        return uploaded
