# -*- coding: utf-8 -*-
"""Passkey Bot — Global Event Listeners & Security Hooks."""
import discord
from discord.ext import commands
import datetime
import logging

log = logging.getLogger("passkey.events")

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log.info(f"Joined new guild: {guild.name} ({guild.id}) with {guild.member_count} members.")
        # Attempt to send a welcome intro if a suitable channel exists
        target_chan = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if target_chan:
            embed = discord.Embed(
                title="🔑 Thanks for adding Passkey!",
                description=(
                    "Passkey is your server's ultimate **Gatekeeper, AutoMod & Security Engine**.\n\n"
                    "**Quick Setup:**\n"
                    "• Run `/setup` or `.setup` to automatically create the `#verify` gateway and `@Verified` role.\n"
                    "• Run `/setmode` to choose between Web Portal, 1-Click Button, or Math CAPTCHA.\n"
                    "• Run `/automod` to inspect real-time anti-spam, anti-invite & anti-phishing defense.\n"
                    "• Run `/help` to see the full list of commands."
                ),
                color=0x6366F1
            )
            embed.set_footer(text="Passkey Security Core")
            try:
                await target_chan.send(embed=embed)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if not self.bot.db:
            return

        config = await self.bot.db.get_guild_config(guild.id)
        min_age_days = int(config.get("min_age_days") or 0)
        
        # Check suspicious brand-new accounts
        if min_age_days > 0:
            age_days = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
            if age_days < min_age_days:
                log_chan_id = config.get("log_channel_id")
                if log_chan_id:
                    chan = guild.get_channel(int(log_chan_id))
                    if chan:
                        embed = discord.Embed(
                            title="⚠️ Suspicious / Underage Account Joined",
                            description=f"{member.mention} (`{member.id}`) created only **{age_days} days ago** (Server min: {min_age_days} days).",
                            color=0xF59E0B,
                            timestamp=datetime.datetime.now(datetime.timezone.utc)
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        try:
                            await chan.send(embed=embed)
                        except Exception:
                            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ You lack the required permission: `{perms}`", ephemeral=True)
            return
        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            await ctx.send(f"❌ Passkey lacks required bot permissions: `{perms}`", ephemeral=True)
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}", ephemeral=True)
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required parameter: `{error.param.name}`. Use `.help {ctx.command}` for syntax.", ephemeral=True)
            return

        log.error(f"Unhandled command error on {ctx.command}: {error}")

async def setup(bot):
    await bot.add_cog(Events(bot))
