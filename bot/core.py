# -*- coding: utf-8 -*-
"""Passkey Bot — Core Client Implementation with Automatic Slash Command & Emoji Sync."""
import discord
from discord.ext import commands
import datetime
import logging
from utils.config import Config
from utils.emojis import Emojis
from database.db import Database

log = logging.getLogger("passkey.core")

class PasskeyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = True
        intents.emojis = True

        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.db = Database(Config.DATABASE_URL)
        self.synced = False

    def uptime(self) -> datetime.timedelta:
        return datetime.datetime.now(datetime.timezone.utc) - self.start_time

    async def setup_hook(self):
        await self.db.connect()

        cogs = [
            "bot.cogs.events",
            "bot.cogs.general",
            "bot.cogs.verification",
            "bot.cogs.antialt",
            "bot.cogs.automod",
            "bot.cogs.scan",
            "bot.cogs.moderation",
            "bot.cogs.system"
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                log.info(f"Loaded cog: {cog}")
            except Exception as e:
                log.error(f"Failed to load {cog}: {e}")

    async def on_ready(self):
        log.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="over server gates • /help | .help"
        ))

        # 1. Automatic Global Slash Command Sync on Ready
        if not self.synced:
            try:
                synced_cmds = await self.tree.sync()
                self.synced = True
                log.info(f"✅ Successfully synced {len(synced_cmds)} global Slash Commands with Discord!")
            except Exception as e:
                log.warning(f"Auto-syncing slash commands failed: {e}")

        # 2. Automatic Custom Emojis Auto-Uploader
        for guild in self.guilds:
            try:
                uploaded = await Emojis.ensure_guild_emojis(guild)
                if uploaded:
                    log.info(f"✅ Synced {len(uploaded)} Custom Neon Emojis into {guild.name}")
            except Exception as e:
                log.warning(f"Could not auto-sync emojis in {guild.name}: {e}")

bot = PasskeyBot()
