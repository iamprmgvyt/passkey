# -*- coding: utf-8 -*-
"""
Passkey Bot — General & Utility Suite.
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

log = logging.getLogger("passkey.general")

class General(commands.Cog, name="General & Utilities"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Check bot gateway latency and response time."""
        lat = round(self.bot.latency * 1000)
        color = 0x10B981 if lat < 100 else (0xF59E0B if lat < 250 else 0xEF4444)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**WebSocket Gateway Latency:** `{lat}ms`\n**Status:** 🟢 Operational",
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

        embed = discord.Embed(
            title="🔑 Passkey — Global Security Telemetry",
            color=0x6366F1
        )
        embed.add_field(name="🛡️ Protected Guilds", value=f"`{guilds:,}`", inline=True)
        embed.add_field(name="👥 Monitored Users", value=f"`{users:,}`", inline=True)
        embed.add_field(name="⚡ Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="✅ Total Verifications", value=f"`{total_verifs:,}`", inline=True)
        embed.add_field(name="⚠️ Mod Actions Recorded", value=f"`{total_warns:,}`", inline=True)
        embed.add_field(name="⏱️ Bot Uptime", value=f"`{str(self.bot.uptime()).split('.')[0]}`", inline=True)
        embed.set_footer(text="Passkey Zero-Trust Security Network")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="botinfo", aliases=["info", "about"])
    async def botinfo(self, ctx: commands.Context):
        """View technical information and system resources about Passkey."""
        process = psutil.Process()
        ram_mb = process.memory_info().rss / 1024 / 1024
        cpu_pct = psutil.cpu_percent()

        embed = discord.Embed(
            title="🤖 Passkey Bot — System & Architecture",
            description="Next-Generation Discord Security, Gatekeeper & Auto-Moderation Engine.",
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

        created_ts = int(guild.created_at.timestamp())

        embed = discord.Embed(
            title=f"🏰 {guild.name} — Server Information",
            color=0x6366F1
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.add_field(name="👑 Owner", value=f"{guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Created On", value=f"<t:{created_ts}:D> (<t:{created_ts}:R>)", inline=True)

        embed.add_field(name="👥 Members", value=f"Total: **{total_members}**\n👤 Humans: **{humans}** | 🤖 Bots: **{bots}**", inline=True)
        embed.add_field(name="💬 Channels", value=f"💬 Text: **{text_channels}** | 🔊 Voice: **{voice_channels}**", inline=True)
        embed.add_field(name="🛡️ Security Level", value=f"Verification: `{str(guild.verification_level).title()}`\nRoles: **{roles_count}**", inline=True)

        if guild.premium_tier > 0 or guild.premium_subscription_count > 0:
            embed.add_field(name="🚀 Boosts", value=f"Level **{guild.premium_tier}** ({guild.premium_subscription_count} boosts)", inline=True)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", aliases=["whois", "user"])
    @app_commands.describe(member="Member to lookup (defaults to you)")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Display information about a server member."""
        member = member or ctx.author
        created_ts = int(member.created_at.timestamp())
        joined_ts = int(member.joined_at.timestamp()) if member.joined_at else 0

        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        roles_str = ", ".join(roles[:10]) if roles else "None"
        if len(roles) > 10:
            roles_str += f" and {len(roles) - 10} more..."

        embed = discord.Embed(
            title=f"👤 User Profile — {member.display_name}",
            color=member.color if member.color.value != 0 else 0x6366F1
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Tag / Name", value=f"`{member.name}` ({member.mention})", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Top Role", value=f"{member.top_role.mention}", inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{created_ts}:D> (<t:{created_ts}:R>)", inline=True)
        embed.add_field(name="📥 Joined Server", value=f"<t:{joined_ts}:D> (<t:{joined_ts}:R>)", inline=True)
        embed.add_field(name="🤖 Bot Account", value=f"`{'Yes' if member.bot else 'No'}`", inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=roles_str, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"])
    @app_commands.describe(member="Member whose avatar to display")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Display high-resolution avatar of a user."""
        member = member or ctx.author
        avatar_url = member.display_avatar.url

        embed = discord.Embed(
            title=f"🖼️ Avatar — {member.display_name}",
            color=0x6366F1
        )
        embed.set_image(url=avatar_url)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open Full Resolution", url=avatar_url, style=discord.ButtonStyle.link))

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="help", aliases=["commands", "cmds"])
    async def help_cmd(self, ctx: commands.Context):
        """List all Passkey commands and system modules."""
        embed = discord.Embed(
            title="🔑 Passkey Command Manual & Feature Guide",
            description="Next-Gen Verification Gatekeeper, Auto-Moderation & Threat Intelligence Bot.",
            color=0x6366F1
        )
        embed.add_field(
            name="🔑 Gatekeeper & Verification",
            value=(
                "`.setup [web|button|captcha]` — Auto-provision #verify & role\n"
                "`.setmode <web|button|captcha>` — Set verification method\n"
                "`.setlog <#channel>` — Set security & audit log channel\n"
                "`.minage <days>` — Require minimum account age\n"
                "`.verify` — Request verification prompt/link"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ AutoMod & Threat Defense",
            value=(
                "`.automod` — View active defense shields\n"
                "`.automod_toggle <feature> <on/off>` — Toggle shields\n"
                "`.antialt on/off` — Toggle duplicate alt IP detection\n"
                "`.lockdown on/off` — Emergency chat lockdown\n"
                "`.scan <url>` — Analyze link in VPS sandbox"
            ),
            inline=False
        )
        embed.add_field(
            name="🔨 Moderation Suite",
            value=(
                "`.timeout <@user> <time> [reason]` — Time out user (e.g. 10m, 1h)\n"
                "`.untimeout <@user>` — Remove timeout\n"
                "`.warn <@user> <reason>` — Issue recorded warning\n"
                "`.warnings <@user>` — View warning history\n"
                "`.clearwarns <@user>` — Clear member warnings\n"
                "`.kick`, `.ban`, `.unban <id>` — Member removal\n"
                "`.purge <amount> [@user]` — Delete messages with filter\n"
                "`.slowmode <seconds>`, `.lock`, `.unlock`"
            ),
            inline=False
        )
        embed.add_field(
            name="📊 Information & Utilities",
            value="`.serverinfo`, `.userinfo`, `.avatar`, `.botinfo`, `.stats`, `.ping`",
            inline=False
        )
        embed.set_footer(text="All commands support both Slash Commands (/) and Prefix (.)")
        await ctx.send(embed=embed)

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context, scope: str = "global"):
        """
        Anti-duplicate Slash Command synchronization tool (Owner only).
        Usage:
        - .sync global       -> Clears local guild commands & syncs globally (Prevents duplicates)
        - .sync clean_all    -> Purges guild-scoped commands from all cached guilds and updates global
        - .sync clear_guild  -> Purges guild commands from this server
        - .sync clear_global -> Clears all global slash commands
        - .sync guild        -> Syncs only to this specific guild
        """
        scope = scope.lower().strip()
        msg = await ctx.send(f"🔄 **Processing `{scope}` sync...**")

        try:
            if scope in ["global", "clean_global"]:
                # Step 1: Clear current guild commands so they don't duplicate with global
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)

                # Step 2: Sync global commands
                synced = await self.bot.tree.sync()
                await msg.edit(content=(
                    f"🌍 **Global Deploy Successful!**\n"
                    f"• Synced **{len(synced)}** global slash commands.\n"
                    f"• Cleared guild-level overrides for `{ctx.guild.name}` to **prevent duplicate commands**.\n"
                    f"*(Note: Discord global slash commands take up to a few minutes to propagate across all servers).* "
                ))

            elif scope == "clean_all":
                # Clear all guild-level command caches across all joined guilds
                cleared_guilds = 0
                for g in self.bot.guilds:
                    try:
                        self.bot.tree.clear_commands(guild=g)
                        await self.bot.tree.sync(guild=g)
                        cleared_guilds += 1
                    except Exception:
                        pass
                synced = await self.bot.tree.sync()
                await msg.edit(content=(
                    f"✨ **Full Cleanup & Global Deploy Done!**\n"
                    f"• Cleared duplicate guild commands in **{cleared_guilds}** servers.\n"
                    f"• Synced **{len(synced)}** clean global slash commands."
                ))

            elif scope == "clear_guild":
                self.bot.tree.clear_commands(guild=ctx.guild)
                await self.bot.tree.sync(guild=ctx.guild)
                await msg.edit(content=f"🧹 Cleared all guild-scoped slash commands for **{ctx.guild.name}**.")

            elif scope == "clear_global":
                self.bot.tree.clear_commands(guild=None)
                await self.bot.tree.sync()
                await msg.edit(content="🧹 Cleared all global slash commands.")

            elif scope == "guild":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await self.bot.tree.sync(guild=ctx.guild)
                await msg.edit(content=f"🏰 Synced **{len(synced)}** slash commands instantly to this guild (`{ctx.guild.name}`).")

            else:
                await msg.edit(content="❌ Unknown scope. Use: `.sync global`, `.sync clean_all`, `.sync clear_guild`, or `.sync guild`")

        except Exception as e:
            log.error(f"Sync error: {e}")
            await msg.edit(content=f"❌ Error during command sync: `{e}`")


async def setup(bot):
    await bot.add_cog(General(bot))
