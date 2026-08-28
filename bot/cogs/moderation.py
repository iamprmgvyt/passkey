# -*- coding: utf-8 -*-
"""
Passkey Bot — Comprehensive Moderation Suite with Custom Neon Emoji Embeds.
Commands:
- timeout / mute
- untimeout / unmute
- kick, ban, unban
- warn, warnings, clearwarns
- purge / clear
- slowmode, lock, unlock
"""
import re
import datetime
import logging
import discord
from discord.ext import commands
from discord import app_commands
from utils.emojis import Emojis

log = logging.getLogger("passkey.moderation")

def parse_duration(duration_str: str) -> datetime.timedelta:
    """Parse time string like 10m, 2h, 1d, 7d into timedelta."""
    match = re.match(r"^(\d+)([smhd])$", duration_str.strip().lower())
    if not match:
        raise ValueError("Invalid format. Use numbers followed by s, m, h, or d (e.g. 10m, 2h, 1d).")
    
    val, unit = int(match.group(1)), match.group(2)
    if unit == "s":
        return datetime.timedelta(seconds=val)
    elif unit == "m":
        return datetime.timedelta(minutes=val)
    elif unit == "h":
        return datetime.timedelta(hours=val)
    elif unit == "d":
        return datetime.timedelta(days=val)
    raise ValueError("Invalid unit.")


class Moderation(commands.Cog, name="Moderation"):
    """Full-featured Discord Moderation System."""

    def __init__(self, bot):
        self.bot = bot

    async def log_mod_action(self, guild: discord.Guild, title: str, description: str, color: int = 0x6366F1, thumbnail_url: str = None):
        if not self.bot.db:
            return
        config = await self.bot.db.get_guild_config(guild.id)
        log_channel_id = config.get("log_channel_id")
        if not log_channel_id:
            return
        chan = guild.get_channel(int(log_channel_id))
        if chan:
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            try:
                await chan.send(embed=embed)
            except Exception:
                pass

    @commands.hybrid_command(name="timeout", aliases=["mute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Target member to timeout",
        duration="Duration string (e.g. 10m, 1h, 1d)",
        reason="Reason for timeout"
    )
    async def timeout(self, ctx: commands.Context, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Timeout a member to temporarily restrict them from speaking or reacting."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(title="❌ Permission Denied", description="You cannot timeout someone with an equal or higher role than you.", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            delta = parse_duration(duration)
        except ValueError as e:
            embed = discord.Embed(title="❌ Invalid Duration", description=str(e), color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        if delta > datetime.timedelta(days=28):
            embed = discord.Embed(title="❌ Duration Too Long", description="Maximum timeout duration is 28 days.", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            await member.timeout(delta, reason=f"[{ctx.author}] {reason}")
            warn_emoji = Emojis.get("warn", self.bot)
            embed = discord.Embed(
                title=f"{warn_emoji} Member Timed Out",
                description=f"**User:** {member.mention} (`{member.id}`)\n**Duration:** `{duration}`\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
                color=0xF59E0B
            )
            await ctx.send(embed=embed)
            await self.log_mod_action(
                ctx.guild,
                f"{warn_emoji} Moderation: Member Timed Out",
                f"**User:** {member.mention} (`{member.id}`)\n**Duration:** `{duration}`\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xF59E0B,
                member.display_avatar.url
            )
        except Exception as e:
            embed = discord.Embed(title="❌ Action Failed", description=f"Failed to timeout member: {e}", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to remove timeout from", reason="Reason for lifting timeout")
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Timeout removed by moderator"):
        """Remove an active timeout from a member."""
        try:
            await member.timeout(None, reason=f"[{ctx.author}] {reason}")
            verified_emoji = Emojis.get("verified", self.bot)
            embed = discord.Embed(
                title=f"{verified_emoji} Timeout Removed",
                description=f"Timeout restriction removed for **{member.display_name}**.",
                color=0x10B981
            )
            await ctx.send(embed=embed)
            await self.log_mod_action(
                ctx.guild,
                f"{verified_emoji} Moderation: Timeout Lifted",
                f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0x10B981
            )
        except Exception as e:
            embed = discord.Embed(title="❌ Action Failed", description=f"Failed to lift timeout: {e}", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(title="❌ Permission Denied", description="You cannot kick someone with an equal or higher role than you.", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            await member.kick(reason=f"[{ctx.author}] {reason}")
            warn_emoji = Emojis.get("warn", self.bot)
            embed = discord.Embed(
                title=f"{warn_emoji} Member Kicked",
                description=f"**User:** {member.name} (`{member.id}`)\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
                color=0xF97316
            )
            await ctx.send(embed=embed)
            await self.log_mod_action(
                ctx.guild,
                f"{warn_emoji} Moderation: Member Kicked",
                f"**User:** {member.name} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xF97316
            )
        except Exception as e:
            embed = discord.Embed(title="❌ Action Failed", description=f"Failed to kick member: {e}", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="User to ban", reason="Reason for ban", delete_days="Number of days of messages to delete (0-7)")
    async def ban(self, ctx: commands.Context, user: discord.User, delete_days: int = 0, *, reason: str = "No reason provided"):
        """Permanently ban a user from the server."""
        member = ctx.guild.get_member(user.id)
        if member and member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(title="❌ Permission Denied", description="You cannot ban someone with an equal or higher role than you.", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        try:
            await ctx.guild.ban(user, reason=f"[{ctx.author}] {reason}", delete_message_days=min(max(delete_days, 0), 7))
            ban_emoji = Emojis.get("ban", self.bot)
            embed = discord.Embed(
                title=f"{ban_emoji} Member Permanently Banned",
                description=f"**User:** {user} (`{user.id}`)\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
            await self.log_mod_action(
                ctx.guild,
                f"{ban_emoji} Moderation: Member Banned",
                f"**User:** {user} (`{user.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xEF4444
            )
        except Exception as e:
            embed = discord.Embed(title="❌ Action Failed", description=f"Failed to ban member: {e}", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to warn", reason="Reason for warning strike")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Rule violation"):
        """Issue a formal recorded warning strike to a member."""
        if member.bot:
            embed = discord.Embed(title="❌ Error", description="You cannot warn bot accounts.", color=0xEF4444)
            await ctx.send(embed=embed, ephemeral=True)
            return

        warn_count = 1
        if self.bot.db:
            await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
            warns = await self.bot.db.get_warnings(ctx.guild.id, member.id)
            warn_count = len(warns)

        warn_emoji = Emojis.get("warn", self.bot)
        embed = discord.Embed(
            title=f"{warn_emoji} Warning Strike #{warn_count} Issued",
            description=f"**User:** {member.mention} (`{member.id}`)\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}\n**Total Strikes:** `{warn_count}`",
            color=0xF59E0B
        )
        await ctx.send(embed=embed)
        await self.log_mod_action(
            ctx.guild,
            f"{warn_emoji} Moderation: Warning Strike #{warn_count}",
            f"**User:** {member.mention}\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
            0xF59E0B
        )

    @commands.hybrid_command(name="warnings", aliases=["warns"])
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member whose warning history to view")
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """View complete infraction history for a member."""
        warns = []
        if self.bot.db:
            warns = await self.bot.db.get_warnings(ctx.guild.id, member.id)

        warn_emoji = Emojis.get("warn", self.bot)
        if not warns:
            embed = discord.Embed(
                title=f"📋 Infraction Record — {member.display_name}",
                description="✅ Clean record! This member has 0 active warnings.",
                color=0x10B981
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{warn_emoji} Infraction Record — {member.display_name} ({len(warns)} Strikes)",
            color=0xF59E0B
        )
        for i, w in enumerate(warns[-10:], 1):
            embed.add_field(
                name=f"Strike #{i} • ID: `{w.get('id', i)}`",
                value=f"**Reason:** {w.get('reason', 'N/A')}\n**Date:** <t:{int(w.get('created_at', 0))}:R>",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge(self, ctx: commands.Context, amount: int = 10):
        """Bulk-delete recent messages from the current channel."""
        amount = min(max(amount, 1), 100)
        await ctx.defer(ephemeral=True)
        deleted = await ctx.channel.purge(limit=amount)
        verified_emoji = Emojis.get("verified", self.bot)
        embed = discord.Embed(
            title=f"{verified_emoji} Messages Purged",
            description=f"Successfully purged **{len(deleted)} messages** from {ctx.channel.mention}.",
            color=0x10B981
        )
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
