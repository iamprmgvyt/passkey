# -*- coding: utf-8 -*-
"""Passkey Bot — Multi-Node Link & Domain Sandbox Threat Scanner."""
import discord
from discord.ext import commands
from discord import app_commands
from utils.scanner_manager import dispatch_url_scan, SCANNER_NODES
import logging

log = logging.getLogger("passkey.scan")

class DomainScanner(commands.Cog, name="Threat Scanner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="scan", aliases=["urlscan", "checkurl"])
    @app_commands.describe(url="Suspicious URL to scan in cloud sandbox")
    async def scan_command(self, ctx: commands.Context, url: str):
        """Detonate and analyze a suspicious URL across multi-node VPS containers."""
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            await ctx.send("❌ Please provide a valid URL starting with `http://` or `https://`. Example: `.scan https://example.com`", ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.defer()
            edit_target = ctx.interaction.followup.send
        else:
            msg = await ctx.send("🔄 **Dispatching URL to Passkey VPS Sandbox Cluster (VN-SG / US-VA)...**")
            edit_target = msg.edit

        result = await dispatch_url_scan(url)

        is_threat = (result.get("status") == "threat")
        embed = discord.Embed(
            title=f"🌐 Threat Scan Report — {result.get('verdict')}",
            description=f"**Target URL:** `{result.get('url')}`",
            color=0xEF4444 if is_threat else 0x10B981
        )
        embed.add_field(name="Scanner Node", value=f"`{result.get('node_id')}` ({result.get('node_name')})", inline=True)
        embed.add_field(name="Sandbox Latency", value=f"`{result.get('latency')}`", inline=True)
        embed.add_field(name="HTTP Status", value=f"`{result.get('http_status')}`", inline=True)
        embed.add_field(name="DOM Inspection", value=result.get("dom_inspection", "Clean"), inline=False)
        embed.set_footer(text="Passkey Cloud Threat Intelligence Engine")

        if ctx.interaction:
            await edit_target(embed=embed)
        else:
            await edit_target(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(DomainScanner(bot))
