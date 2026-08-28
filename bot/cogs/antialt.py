# -*- coding: utf-8 -*-
"""Passkey Bot — Anti-Alt & Duplicate Account Detection."""
import discord
from discord.ext import commands
from discord import app_commands
import logging

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
            await ctx.send("ℹ️ Usage: `.antialt on` or `.antialt off`", ephemeral=True)
            return

        enabled = 1 if mode in ["on", "enable"] else 0
        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "antialt_enabled", enabled)

        status = "ENABLED 🟢 (Protecting against duplicate alt accounts)" if enabled else "DISABLED 🔴"
        await ctx.send(f"🛡️ **Anti-Alt Protection is now {status}** for this server.")

async def setup(bot):
    await bot.add_cog(AntiAlt(bot))
