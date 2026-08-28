# -*- coding: utf-8 -*-
"""
Passkey Bot — Advanced Auto-Moderation & Threat Shield Cog.
Features:
- Anti-Spam (Rate-limit & Duplicate Message Protection)
- Anti-Invite (Blocks unauthorized Discord server invites)
- Anti-Phishing (Instant detection of fake nitro, token grabbers, scam links)
- Anti-Mass-Mention (Blocks unauthorized mass pings & @everyone)
- Emergency Server / Channel Lockdown (.lockdown on/off)
"""
import re
import time
import datetime
import logging
import discord
from discord.ext import commands
from discord import app_commands

log = logging.getLogger("passkey.automod")

INVITE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite|dsc\.gg)/[a-zA-Z0-9_-]+", re.IGNORECASE)
PHISHING_KEYWORDS = [
    "nitro-gift", "free-nitro", "steam-gift", "steanncommunity", "airdrop-claim",
    "discords-gift", "discord-nitro", "steamcomunuty", "gift-discord", "claim-nitro",
    "discordnitro", "nitro-free", "dlscord", "discrod", "bit.ly/nitro", "t.me/claim"
]

class AutoMod(commands.Cog, name="Auto-Moderation"):
    def __init__(self, bot):
        self.bot = bot
        # In-memory spam tracker: {guild_id: {user_id: [(timestamp, content)]}}
        self.user_message_history = {}

    def is_staff(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild or member.guild_permissions.manage_messages:
            return True
        return False

    async def log_violation(self, guild: discord.Guild, member: discord.Member, rule: str, reason: str, message_content: str = ""):
        """Helper to send security alerts to configured log channel."""
        if not self.bot.db:
            return
        config = await self.bot.db.get_guild_config(guild.id)
        log_channel_id = config.get("log_channel_id")
        if not log_channel_id:
            return
        chan = guild.get_channel(int(log_channel_id))
        if not chan:
            return

        embed = discord.Embed(
            title=f"🚨 AutoMod Alert — {rule}",
            description=f"**Offender:** {member.mention} (`{member.id}`)\n**Action:** Message Blocked\n**Details:** {reason}",
            color=0xEF4444,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        if message_content:
            preview = message_content[:200] + ("..." if len(message_content) > 200 else "")
            embed.add_field(name="Message Content", value=f"```{preview}```", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        try:
            await chan.send(embed=embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        if self.is_staff(member):
            return

        config = {}
        if self.bot.db:
            config = await self.bot.db.get_guild_config(message.guild.id)

        content = message.content.lower()

        # 1. Anti-Phishing Link Check
        if config.get("automod_phishing", 1):
            for bad_kw in PHISHING_KEYWORDS:
                if bad_kw in content:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    # Apply 1 hour timeout for scam attempt
                    try:
                        await member.timeout(datetime.timedelta(hours=1), reason="[AutoMod] Malicious / Phishing link detected")
                    except Exception:
                        pass
                    await self.log_violation(message.guild, member, "Anti-Phishing", f"Posted suspected phishing link containing `{bad_kw}` (Applied 1h Timeout)", message.content)
                    try:
                        await message.channel.send(f"🛡️ {member.mention}, posting malicious or phishing links is strictly prohibited! (Timed out)", delete_after=5)
                    except Exception:
                        pass
                    return

        # 2. Anti-Invite Check
        if config.get("automod_invites", 1):
            if INVITE_REGEX.search(message.content):
                try:
                    await message.delete()
                except Exception:
                    pass
                await self.log_violation(message.guild, member, "Anti-Invite", "Posted unauthorized Discord invite link.", message.content)
                try:
                    await message.channel.send(f"⚠️ {member.mention}, Discord invite links are not allowed here.", delete_after=5)
                except Exception:
                    pass
                return

        # 3. Anti-Mass Mention Check
        if config.get("automod_mentions", 1):
            if len(message.mentions) >= 5 or (("@everyone" in message.content or "@here" in message.content) and not member.guild_permissions.mention_everyone):
                try:
                    await message.delete()
                except Exception:
                    pass
                try:
                    await member.timeout(datetime.timedelta(minutes=10), reason="[AutoMod] Mass mention spam")
                except Exception:
                    pass
                await self.log_violation(message.guild, member, "Anti-Mass-Mention", f"Attempted to mention {len(message.mentions)} members or @everyone", message.content)
                try:
                    await message.channel.send(f"⚠️ {member.mention}, mass mentions are prohibited! (Timed out for 10m)", delete_after=5)
                except Exception:
                    pass
                return

        # 4. Anti-Spam / Rate-Limit Check
        if config.get("automod_spam", 1):
            now = time.time()
            guild_id = message.guild.id
            user_id = member.id

            if guild_id not in self.user_message_history:
                self.user_message_history[guild_id] = {}
            if user_id not in self.user_message_history[guild_id]:
                self.user_message_history[guild_id][user_id] = []

            history = self.user_message_history[guild_id][user_id]
            # Keep only messages from the last 5 seconds
            history = [(ts, txt) for ts, txt in history if now - ts < 5.0]
            history.append((now, message.content))
            self.user_message_history[guild_id][user_id] = history

            # Check 1: More than 5 messages in 4 seconds
            # Check 2: Same message repeated 3 times in 5 seconds
            is_fast_spam = len(history) >= 5
            is_repeat_spam = sum(1 for _, txt in history if txt.strip() == message.content.strip()) >= 3 and len(message.content.strip()) > 3

            if is_fast_spam or is_repeat_spam:
                try:
                    await message.delete()
                except Exception:
                    pass
                try:
                    await member.timeout(datetime.timedelta(minutes=2), reason="[AutoMod] Automated message spam detected")
                except Exception:
                    pass
                self.user_message_history[guild_id][user_id] = []
                await self.log_violation(message.guild, member, "Anti-Spam", "Flooding channels with repetitive/fast messages (Timed out 2m)", message.content)
                try:
                    await message.channel.send(f"🛑 {member.mention}, slow down! Spamming is not permitted.", delete_after=5)
                except Exception:
                    pass
                return

    # --- Commands ---

    @commands.hybrid_command(name="automod")
    @commands.has_permissions(administrator=True)
    async def automod_status(self, ctx: commands.Context):
        """View current AutoMod defense shields status for this server."""
        guild = ctx.guild
        config = {}
        if self.bot.db:
            config = await self.bot.db.get_guild_config(guild.id)

        spam = "🟢 Enabled" if config.get("automod_spam", 1) else "🔴 Disabled"
        invites = "🟢 Enabled" if config.get("automod_invites", 1) else "🔴 Disabled"
        phishing = "🟢 Enabled" if config.get("automod_phishing", 1) else "🔴 Disabled"
        mentions = "🟢 Enabled" if config.get("automod_mentions", 1) else "🔴 Disabled"
        antialt = "🟢 Enabled" if config.get("antialt_enabled", 1) else "🔴 Disabled"
        min_age = f"**{config.get('min_age_days', 0)} days**"

        embed = discord.Embed(
            title=f"🛡️ Passkey AutoMod & Security Shields — {guild.name}",
            description="Active real-time automated defense shields protecting your server:",
            color=0x6366F1
        )
        embed.add_field(name="Anti-Spam Shield", value=spam, inline=True)
        embed.add_field(name="Anti-Invite Shield", value=invites, inline=True)
        embed.add_field(name="Anti-Phishing / Scams", value=phishing, inline=True)
        embed.add_field(name="Anti-Mass Mention", value=mentions, inline=True)
        embed.add_field(name="Anti-Alt Account Shield", value=antialt, inline=True)
        embed.add_field(name="Minimum Account Age", value=min_age, inline=True)

        embed.set_footer(text="Use .automod-toggle <feature> or /automod_toggle to enable/disable shields.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="automod_toggle", aliases=["automod-toggle"])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        feature="Shield feature to toggle",
        status="Enable or Disable"
    )
    @app_commands.choices(
        feature=[
            app_commands.Choice(name="Anti-Spam", value="spam"),
            app_commands.Choice(name="Anti-Invite", value="invites"),
            app_commands.Choice(name="Anti-Phishing", value="phishing"),
            app_commands.Choice(name="Anti-Mass Mention", value="mentions"),
        ],
        status=[
            app_commands.Choice(name="Enable (ON)", value="on"),
            app_commands.Choice(name="Disable (OFF)", value="off"),
        ]
    )
    async def automod_toggle(self, ctx: commands.Context, feature: str, status: str):
        """Toggle an AutoMod shield ON or OFF."""
        feature = feature.lower()
        key_map = {
            "spam": "automod_spam",
            "invites": "automod_invites",
            "phishing": "automod_phishing",
            "mentions": "automod_mentions"
        }
        if feature not in key_map:
            await ctx.send("❌ Valid features: `spam`, `invites`, `phishing`, `mentions`", ephemeral=True)
            return

        db_key = key_map[feature]
        is_on = 1 if status.lower() in ["on", "enable", "1"] else 0

        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, db_key, is_on)

        state_str = "ENABLED 🟢" if is_on else "DISABLED 🔴"
        await ctx.send(f"🛡️ **AutoMod Shield `{feature.upper()}` is now {state_str}** for this server.")

    @commands.hybrid_command(name="lockdown")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(action="Turn lockdown ON or OFF")
    @app_commands.choices(action=[
        app_commands.Choice(name="Lockdown ON (Freeze chat)", value="on"),
        app_commands.Choice(name="Lockdown OFF (Resume chat)", value="off"),
    ])
    async def lockdown(self, ctx: commands.Context, action: str = "on"):
        """Emergency raid shield: Lock or unlock the current channel for regular members."""
        channel = ctx.channel
        guild = ctx.guild
        default_role = guild.default_role

        if action.lower() in ["on", "enable"]:
            overwrites = channel.overwrites_for(default_role)
            overwrites.send_messages = False
            await channel.set_permissions(default_role, overwrite=overwrites, reason=f"[Emergency Lockdown] by {ctx.author}")
            embed = discord.Embed(
                title="🔒 Channel Locked Down",
                description="This channel has been placed under emergency lockdown by administrators. Sending messages is temporarily disabled.",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
        else:
            overwrites = channel.overwrites_for(default_role)
            overwrites.send_messages = None
            await channel.set_permissions(default_role, overwrite=overwrites, reason=f"[Lockdown Lifted] by {ctx.author}")
            embed = discord.Embed(
                title="🔓 Channel Lockdown Lifted",
                description="Emergency lockdown has been lifted. Normal chatting may resume.",
                color=0x10B981
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
