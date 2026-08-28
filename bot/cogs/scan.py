# -*- coding: utf-8 -*-
"""Passkey Bot — Multi-Node Link & Domain Sandbox Threat Scanner with Custom Emoji Embeds."""
import discord
from discord.ext import commands
from discord import app_commands
from utils.scanner_manager import dispatch_url_scan, SCANNER_NODES
from utils.emojis import Emojis
import logging

log = logging.getLogger("passkey.scan")

class DomainScanner(commands.Cog, name="Threat Scanner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="scan", aliases=["urlscan", "checkurl"])
    @app_commands.describe(url="Suspicious URL to scan in cloud sandbox")
    async def scan_command(self, ctx: commands.Context, url: str):
        """Detonate and analyze a suspicious URL across multi-node VPS containers."""
        warn_emoji = Emojis.get("warn", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            embed = discord.Embed(
                title=f"{warn_emoji} Invalid URL",
                description="Please provide a valid URL starting with `http://` or `https://`.\n*Example:* `.scan https://example.com`",
                color=0xEF4444
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.defer()
            edit_target = ctx.interaction.followup.send
        else:
            embed_wait = discord.Embed(
                title=f"{shield_emoji} Sandbox Detonation in Progress",
                description="Dispatching URL to Passkey VPS Sandbox Cluster (VN-SG / US-VA)...",
                color=0x6366F1
            )
            msg = await ctx.send(embed=embed_wait)
            edit_target = msg.edit

        result = await dispatch_url_scan(url)

        is_threat = (result.get("status") == "threat")
        status_emoji = warn_emoji if is_threat else verified_emoji

        embed = discord.Embed(
            title=f"{status_emoji} Threat Intelligence Report — {result.get('verdict')}",
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
