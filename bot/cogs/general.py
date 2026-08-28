# -*- coding: utf-8 -*-
"""
Passkey Bot — General & Utility Suite with Custom Neon Emoji Embeds.
Commands:
- serverinfo, userinfo, avatar, botinfo
- ping, stats, help
- sync (Slash command synchronization)
"""
import sys
import psutil
import datetime
import logging
import discord
from discord.ext import commands
from discord import app_commands
from utils.emojis import Emojis

log = logging.getLogger("passkey.general")

class General(commands.Cog, name="General & Utilities"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check bot gateway latency and response time."""
        lat = round(self.bot.latency * 1000)
        color = 0x10B981 if lat < 100 else (0xF59E0B if lat < 250 else 0xEF4444)
        shield_emoji = Emojis.get("shield", self.bot)
        passkey_emoji = Emojis.get("passkey", self.bot)
        
        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey Gateway Status",
            description=f"**WebSocket Ping:** `{lat}ms`\n**Status:** {shield_emoji} All Systems Operational",
            color=color
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stats")
    async def stats(self, ctx: commands.Context):
        """Display live bot security & network statistics."""
        guilds = len(self.bot.guilds)
        users = sum(g.member_count or 0 for g in self.bot.guilds)
        
        db_stats = {}
        if self.bot.db:
            db_stats = await self.bot.db.get_global_stats()

        total_verifs = db_stats.get("total_verifications", 0)
        total_warns = db_stats.get("total_warnings", 0)

        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)
        warn_emoji = Emojis.get("warn", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey — Global Security Telemetry",
            color=0x6366F1
        )
        embed.add_field(name=f"{shield_emoji} Protected Guilds", value=f"`{guilds:,}`", inline=True)
        embed.add_field(name=f"👥 Monitored Users", value=f"`{users:,}`", inline=True)
        embed.add_field(name=f"⚡ Gateway Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name=f"{verified_emoji} Total Verifications", value=f"`{total_verifs:,}`", inline=True)
        embed.add_field(name=f"{warn_emoji} Security Interventions", value=f"`{total_warns:,}`", inline=True)
        embed.add_field(name=f"⏱️ Bot Uptime", value=f"`{str(self.bot.uptime()).split('.')[0]}`", inline=True)
        embed.set_footer(text="Passkey Zero-Trust Security Network")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="botinfo", aliases=["info", "about"])
    async def botinfo(self, ctx: commands.Context):
        """View technical information and system resources about Passkey."""
        process = psutil.Process()
        ram_mb = process.memory_info().rss / 1024 / 1024
        cpu_pct = psutil.cpu_percent()

        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey Gatekeeper — Architecture",
            description=f"{shield_emoji} Next-Generation Discord Security, Gatekeeper & Auto-Moderation Engine.",
            color=0x6366F1
        )
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="🐍 Python", value=f"`{sys.version.split()[0]}`", inline=True)
        embed.add_field(name="📦 Discord.py", value=f"`v{discord.__version__}`", inline=True)
        embed.add_field(name="💾 RAM Usage", value=f"`{ram_mb:.1f} MB`", inline=True)
        embed.add_field(name="⚙️ CPU Usage", value=f"`{cpu_pct}%`", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{str(self.bot.uptime()).split('.')[0]}`", inline=True)
        embed.add_field(name="🌐 Shards / Guilds", value=f"`1 / {len(self.bot.guilds)}`", inline=True)

        embed.set_footer(text="Passkey Cloud Core • High Availability")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", aliases=["server", "guildinfo"])
    async def serverinfo(self, ctx: commands.Context):
        """Display detailed information about the current server."""
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ This command must be used within a server.", ephemeral=True)
            return

        total_members = guild.member_count or 0
        bots = sum(1 for m in guild.members if m.bot)
        humans = total_members - bots
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles_count = len(guild.roles)

        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)

        embed = discord.Embed(
            title=f"{shield_emoji} Server Information — {guild.name}",
            color=0x6366F1
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Server Owner", value=f"{guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
        embed.add_field(name="🆔 Guild ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Created On", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="👥 Members", value=f"Total: `{total_members}` (Humans: `{humans}`, Bots: `{bots}`)", inline=True)
        embed.add_field(name="💬 Channels", value=f"Text: `{text_channels}` | Voice: `{voice_channels}`", inline=True)
        embed.add_field(name="🎭 Roles", value=f"`{roles_count}` roles", inline=True)

        embed.set_footer(text=f"Passkey Protected • Verification System Ready")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", aliases=["user", "whois"])
    @app_commands.describe(member="Member to inspect")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Display security and profile information for a server member."""
        member = member or ctx.author
        roles = [r.mention for r in reversed(member.roles) if not r.is_default()]
        roles_str = ", ".join(roles[:8]) if roles else "None"
        if len(roles) > 8:
            roles_str += f" (+{len(roles)-8} more)"

        passkey_emoji = Emojis.get("passkey", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} User Profile — {member.display_name}",
            color=member.color or 0x6366F1
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👤 Username", value=f"{member} (`{member.id}`)", inline=True)
        embed.add_field(name="🤖 Bot Account", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
        embed.add_field(name=f"🎭 Roles [{len(member.roles)-1}]", value=roles_str, inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"])
    @app_commands.describe(user="User whose avatar you want to view")
    async def avatar(self, ctx: commands.Context, user: discord.User = None):
        """View high-resolution avatar of a user."""
        user = user or ctx.author
        embed = discord.Embed(
            title=f"🖼️ Avatar for {user.display_name}",
            color=0x6366F1
        )
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help")
    async def help_cmd(self, ctx: commands.Context):
        """Display the complete Passkey command catalog."""
        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)
        lock_emoji = Emojis.get("lock", self.bot)
        ban_emoji = Emojis.get("ban", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey Gatekeeper — Commands Manual",
            description="Next-Generation Zero-Trust Discord Server Defense System.\nBoth Slash (`/`) and Prefix (`.`) commands are supported.",
            color=0x6366F1
        )

        embed.add_field(
            name=f"{passkey_emoji} Verification Setup",
            value=(
                "• `/setup` — Launch 5-Step Paginated Setup Wizard.\n"
                "• `/post_verify` — Send interactive 'Click to Verify' panel into channel.\n"
                "• `/settings` — Open Master Server Configuration Panel.\n"
                "• `/setmode <mode>` — Switch between 9 verification engines.\n"
                "• `/setlang <lang>` — Configure default server language.\n"
                "• `/minage <days>` — Enforce minimum Discord account age."
            ),
            inline=False
        )

        embed.add_field(
            name=f"{shield_emoji} AutoMod & Threat Shields",
            value=(
                "• `/automod` — View active defense shields status.\n"
                "• `/automod_toggle <shield> <on/off>` — Toggle specific shield.\n"
                "• `/antialt <on/off>` — Multi-account clone detection.\n"
                "• `/lockdown <on/off>` — Instant channel raid freeze.\n"
                "• `/scan <url>` — Multi-node sandbox threat analysis."
            ),
            inline=False
        )

        embed.add_field(
            name=f"{ban_emoji} Moderation & Management",
            value=(
                "• `/warn <@user> [reason]` — Issue formal infraction strike.\n"
                "• `/warnings <@user>` — View user strike history.\n"
                "• `/clearwarns <@user>` — Reset user warning strikes.\n"
                "• `/timeout <@user> <time> [reason]` — Restrict chat permissions.\n"
                "• `/kick <@user> [reason]` — Kick member from server.\n"
                "• `/ban <@user> [reason]` — Ban member from server.\n"
                "• `/purge <amount>` — Bulk delete messages."
            ),
            inline=False
        )

        embed.set_footer(text="Passkey Security Core • Type /help anytime")
        await ctx.send(embed=embed)

    @commands.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx: commands.Context, mode: str = "global"):
        """Sync and refresh Slash Commands with Discord gateway."""
        passkey_emoji = Emojis.get("passkey", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)

        if mode.lower() == "global":
            synced = await self.bot.tree.sync()
            embed = discord.Embed(
                title=f"{verified_emoji} Global Slash Commands Synced!",
                description=f"Successfully registered **{len(synced)} global Slash Commands** with Discord.",
                color=0x10B981
            )
            await ctx.send(embed=embed)
        else:
            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            embed = discord.Embed(
                title=f"{verified_emoji} Guild Slash Commands Synced!",
                description=f"Successfully registered **{len(synced)} Slash Commands** specifically for **{ctx.guild.name}**.",
                color=0x10B981
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
