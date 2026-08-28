# -*- coding: utf-8 -*-
"""Passkey Bot — System diagnostics."""
import discord
from discord.ext import commands

class System(commands.Cog, name="System"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="reload")
    @commands.is_owner()
    async def reload_ext(self, ctx: commands.Context, ext: str = "dashboard"):
        """Reload extensions or dashboard."""
        if ext == "dashboard":
            from dashboard.app import reload_dashboard
            res = reload_dashboard()
            await ctx.send(f"Dashboard reloaded ({res.get('reloaded_count', 0)} pages refreshed).")
        else:
            await self.bot.reload_extension(f"bot.cogs.{ext}")
            await ctx.send(f"Reloaded `bot.cogs.{ext}`")

async def setup(bot):
    await bot.add_cog(System(bot))
