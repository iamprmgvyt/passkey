# -*- coding: utf-8 -*-
"""Passkey Bot — Anti-Alt & Duplicate Account Detection with Custom Emoji Embeds."""
import discord
from discord.ext import commands
from discord import app_commands
import logging
from utils.emojis import Emojis

log = logging.getLogger("passkey.antialt")

class AntiAlt(commands.Cog, name="Anti-Alt Shield"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="antialt")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(mode="Turn Anti-Alt protection on or off")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Enable (ON)", value="on"),
        app_commands.Choice(name="Disable (OFF)", value="off"),
    ])
    async def antialt_toggle(self, ctx: commands.Context, mode: str = "on"):
        """Toggle anti-alt account detection (.antialt on/off or /antialt)."""
        mode = mode.lower()
        if mode not in ["on", "off", "enable", "disable"]:
            await ctx.send("ℹ Usage: `.antialt on` or `.antialt off`", ephemeral=True)
            return

        enabled = 1 if mode in ["on", "enable"] else 0
        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "antialt_enabled", enabled)

        alt_emoji = Emojis.get("alt", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)
        status_str = "ENABLED " if enabled else "DISABLED "
        color = 0x10B981 if enabled else 0xEF4444

        embed = discord.Embed(
            title=f"{alt_emoji} Anti-Alt Account Shield — {status_str}",
            description=(
                f"{shield_emoji} **Real-time duplicate IP & verified email checking is now {status_str.lower()}** for **{ctx.guild.name}**.\n\n"
                "When active, Passkey intercepts duplicate fingerprints and enforces your server's chosen Anti-Alt policy (Quarantine, Log, Kick, or Ban)."
            ),
            color=color
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiAlt(bot))
