# -*- coding: utf-8 -*-
"""
Passkey Bot — Comprehensive Moderation Suite.
Commands:
- timeout / mute (Discord native timeout with flexible duration like 10m, 1h, 1d)
- untimeout / unmute
- kick, ban, unban
- warn, warnings, clearwarns
- purge / clear (with optional user filter)
- slowmode, lock, unlock
"""
import re
import datetime
import logging
import discord
from discord.ext import commands
from discord import app_commands

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
            await ctx.send("❌ You cannot timeout someone with an equal or higher role than you.", ephemeral=True)
            return

        try:
            delta = parse_duration(duration)
        except ValueError as e:
            await ctx.send(f"❌ {e}", ephemeral=True)
            return

        if delta > datetime.timedelta(days=28):
            await ctx.send("❌ Maximum timeout duration is 28 days.", ephemeral=True)
            return

        try:
            await member.timeout(delta, reason=f"[{ctx.author}] {reason}")
            embed = discord.Embed(
                title="⏳ Member Timed Out",
                description=f"**User:** {member.mention} (`{member.id}`)\n**Duration:** `{duration}`\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}",
                color=0xF59E0B
            )
            await ctx.send(embed=embed)
            await self.log_mod_action(
                ctx.guild,
                "⏳ Moderation: Member Timed Out",
                f"**User:** {member.mention} (`{member.id}`)\n**Duration:** `{duration}`\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xF59E0B,
                member.display_avatar.url
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to timeout member: {e}", ephemeral=True)

    @commands.hybrid_command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to remove timeout from", reason="Reason for lifting timeout")
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Timeout removed by moderator"):
        """Remove an active timeout from a member."""
        try:
            await member.timeout(None, reason=f"[{ctx.author}] {reason}")
            await ctx.send(f"✅ Timeout removed for **{member.display_name}**.")
            await self.log_mod_action(
                ctx.guild,
                "🔊 Moderation: Timeout Lifted",
                f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0x10B981
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to lift timeout: {e}", ephemeral=True)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You cannot kick someone with an equal or higher role than you.", ephemeral=True)
            return

        try:
            await member.kick(reason=f"[{ctx.author}] {reason}")
            await ctx.send(f"👢 Kicked **{member.display_name}** | Reason: {reason}")
            await self.log_mod_action(
                ctx.guild,
                "👢 Moderation: Member Kicked",
                f"**User:** {member.name} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xF97316
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to kick member: {e}", ephemeral=True)

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban", reason="Reason for ban", delete_days="Days of message history to delete (0-7)")
    async def ban(self, ctx: commands.Context, member: discord.Member, delete_days: int = 0, *, reason: str = "No reason provided"):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You cannot ban someone with an equal or higher role than you.", ephemeral=True)
            return

        try:
            await member.ban(reason=f"[{ctx.author}] {reason}", delete_message_days=min(max(delete_days, 0), 7))
            await ctx.send(f"🔨 Banned **{member.display_name}** | Reason: {reason}")
            await self.log_mod_action(
                ctx.guild,
                "🔨 Moderation: Member Banned",
                f"**User:** {member.name} (`{member.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0xEF4444
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to ban member: {e}", ephemeral=True)

    @commands.hybrid_command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user_id="ID of user to unban", reason="Reason for unban")
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "Unbanned by moderator"):
        """Unban a user by their Discord User ID."""
        try:
            uid = int(user_id)
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user, reason=f"[{ctx.author}] {reason}")
            await ctx.send(f"✅ Successfully unbanned **{user.name}** (`{uid}`).")
            await self.log_mod_action(
                ctx.guild,
                "🔓 Moderation: User Unbanned",
                f"**User:** {user.name} (`{uid}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
                0x10B981
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to unban: {e}", ephemeral=True)

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Rule violation"):
        """Issue an official warning to a member and record it in database."""
        if not self.bot.db:
            await ctx.send("❌ Database unavailable.", ephemeral=True)
            return

        warn_id = await self.bot.db.add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        all_warns = await self.bot.db.get_warnings(ctx.guild.id, member.id)

        embed = discord.Embed(
            title="⚠️ Official Warning Issued",
            description=f"**Target:** {member.mention} (`{member.id}`)\n**Reason:** {reason}\n**Moderator:** {ctx.author.mention}\n**Total Warnings:** `{len(all_warns)}`",
            color=0xF59E0B
        )
        embed.set_footer(text=f"Warning Case #{warn_id}")
        await ctx.send(embed=embed)

        await self.log_mod_action(
            ctx.guild,
            f"⚠️ Moderation: Warning #{warn_id}",
            f"**Target:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}\n**Total Infractions:** {len(all_warns)}",
            0xF59E0B,
            member.display_avatar.url
        )

    @commands.hybrid_command(name="warnings", aliases=["warns"])
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="Member to view warnings for")
    async def warnings(self, ctx: commands.Context, member: discord.Member):
        """View warning history for a member."""
        if not self.bot.db:
            await ctx.send("❌ Database unavailable.", ephemeral=True)
            return

        records = await self.bot.db.get_warnings(ctx.guild.id, member.id)
        if not records:
            await ctx.send(f"✨ **{member.display_name}** has a completely clean record with 0 warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📋 Infraction History — {member.display_name}",
            description=f"Total recorded infractions: **{len(records)}**",
            color=0xF59E0B
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        for w in records[:10]:
            ts_str = f"<t:{int(w.get('timestamp', 0))}:R>"
            embed.add_field(
                name=f"Case #{w.get('id')} • {ts_str}",
                value=f"**Mod:** <@{w.get('moderator_id')}>\n**Reason:** {w.get('reason')}",
                inline=False
            )

        if len(records) > 10:
            embed.set_footer(text=f"Showing recent 10 of {len(records)} warnings.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearwarns", aliases=["clearwarnings"])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member="Member to clear warnings for")
    async def clear_warns(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member."""
        if not self.bot.db:
            await ctx.send("❌ Database unavailable.", ephemeral=True)
            return

        deleted = await self.bot.db.clear_warnings(ctx.guild.id, member.id)
        await ctx.send(f"🧹 Cleared **{deleted}** warning(s) for {member.mention}.")

    @commands.hybrid_command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.describe(amount="Number of messages to delete (1-100)", member="Filter messages only from this member (optional)")
    async def purge(self, ctx: commands.Context, amount: int = 10, member: discord.Member = None):
        """Bulk delete messages in the current channel."""
        if amount < 1 or amount > 100:
            await ctx.send("❌ Amount must be between 1 and 100.", ephemeral=True)
            return

        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        def check(m):
            return member is None or m.author.id == member.id

        deleted = await ctx.channel.purge(limit=amount, check=check)
        msg_text = f"🧹 Successfully deleted **{len(deleted)}** message(s)."
        if member:
            msg_text += f" (Filtered by {member.mention})"

        if ctx.interaction:
            await ctx.interaction.followup.send(msg_text, ephemeral=True)
        else:
            msg = await ctx.send(msg_text)
            await msg.delete(delay=4)

    @commands.hybrid_command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable, max 21600)")
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        """Set slowmode rate limit for the current channel."""
        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Seconds must be between 0 and 21600 (6 hours).", ephemeral=True)
            return

        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("⏱️ Slowmode has been **disabled** for this channel.")
        else:
            await ctx.send(f"⏱️ Slowmode set to **{seconds}s** per message.")

    @commands.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock_channel(self, ctx: commands.Context):
        """Lock the current channel so members cannot send messages."""
        default_role = ctx.guild.default_role
        overwrites = ctx.channel.overwrites_for(default_role)
        overwrites.send_messages = False
        await ctx.channel.set_permissions(default_role, overwrite=overwrites)
        await ctx.send("🔒 Channel locked.")

    @commands.hybrid_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx: commands.Context):
        """Unlock the current channel."""
        default_role = ctx.guild.default_role
        overwrites = ctx.channel.overwrites_for(default_role)
        overwrites.send_messages = None
        await ctx.channel.set_permissions(default_role, overwrite=overwrites)
        await ctx.send("🔓 Channel unlocked.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
