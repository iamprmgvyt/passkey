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
            command_prefix=commands.when_mentioned_or("p!", "P!", "p.", "P.", "."),
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
            type=discord.ActivityType.watching, name="over server gates • p!help | /help"
        ))

        # 1. Automatic Global & Instant Guild Slash Command Sync on Ready
        if not self.synced:
            try:
                synced = await self.tree.sync()
                log.info(f"Automatically synced {len(synced)} Slash Commands globally.")
                for guild in self.guilds:
                    try:
                        self.tree.copy_global_to(guild=guild)
                        await self.tree.sync(guild=guild)
                        log.info(f"Instantly synced Slash Commands for guild: {guild.name} ({guild.id})")
                    except Exception as ge:
                        log.warning(f"Could not sync slash commands for guild {guild.id}: {ge}")
                self.synced = True
            except Exception as e:
                log.error(f"Failed to sync slash commands on ready: {e}")

        # 2. Automatic Custom Emojis Auto-Uploader
        for guild in self.guilds:
            try:
                uploaded = await Emojis.ensure_guild_emojis(guild)
                if uploaded:
                    log.info(f" Synced {len(uploaded)} Custom Neon Emojis into {guild.name}")
            except Exception as e:
                log.warning(f"Could not auto-sync emojis in {guild.name}: {e}")

bot = PasskeyBot()
