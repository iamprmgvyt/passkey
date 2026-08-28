# -*- coding: utf-8 -*-
"""
Passkey Bot — Complete Next-Gen Multi-Mode Verification Engine.
Supports 9 Verification Modes:
1. 🌐 Web Portal (Cloudflare Turnstile CAPTCHA + Anti-Alt IP)
2. 📱 WebAuthn Biometric (Hardware Touch ID, Face ID, Windows Hello, YubiKey)
3. ✉️ Email OTP (6-digit code via Zoho SMTP + Alt Email check)
4. ⚡ Direct 1-Click Button (Instant In-Discord)
5. 🔢 Math CAPTCHA Modal (Dynamic arithmetic challenge)
6. 🖼️ Image Visual CAPTCHA (In-Discord Pillow distorted security image)
7. 🎮 Emoji Sequence Pattern (Interactive 3-symbol sequence button matching)
8. 🔗 Social Connection Verification (Checks linked accounts)
9. 📝 Server Rules Agreement & Quiz Modal

Plus:
- 5-Attempt Verification Limit Enforcement (Warnings -> Kick -> Ban)
- Anti-Alt Enforcement Policy (Quarantine both accounts, Log only, Kick, Ban, Ignore)
- Interactive 5-Step Setup Wizard with Pagination (◀️ / ▶️) & ChannelSelect
- 10 Global Languages (English default, Vietnamese, Japanese, Korean, etc.)
- Dynamic Custom Emoji System Integration (utils.emojis)
"""
import os
import random
import secrets
import time
import datetime
import logging
from typing import Dict, Tuple, List
import discord
from discord.ext import commands
from discord import app_commands

from utils.captcha_gen import generate_image_captcha
from utils.emojis import Emojis

log = logging.getLogger("passkey.verification")

# In-memory verification sessions: {token: {"user_id": int, "guild_id": int, "created_at": float}}
VERIFY_SESSIONS = {}

# In-memory failed attempts tracker: {(guild_id, user_id): failed_count}
VERIFY_FAILED_ATTEMPTS: Dict[Tuple[int, int], int] = {}

# In-memory image CAPTCHA challenges: {(guild_id, user_id): {"code": str, "expires": float}}
IMAGE_CAPTCHA_STORE: Dict[Tuple[int, int], dict] = {}


async def handle_failed_attempt(bot, guild: discord.Guild, member: discord.Member, reason: str = "Verification failed") -> str:
    """Track failed attempts (Max 5 attempts rule).
    - 5 fails -> Warn 1
    - 10 fails -> Warn 2
    - 15 fails -> Kick
    - 20+ fails -> Ban
    """
    key = (guild.id, member.id)
    VERIFY_FAILED_ATTEMPTS[key] = VERIFY_FAILED_ATTEMPTS.get(key, 0) + 1
    failed_count = VERIFY_FAILED_ATTEMPTS[key]
    remaining = 5 - (failed_count % 5 if failed_count % 5 != 0 else 5)

    if failed_count % 5 != 0:
        return f"❌ {reason}. You have **{remaining} attempt(s)** remaining before a penalty."

    # User hit a multiple of 5 failed attempts! Check their total warnings count
    warn_count = 0
    if bot.db:
        warns = await bot.db.get_warnings(guild.id, member.id)
        warn_count = len(warns)

    if warn_count == 0:
        if bot.db:
            await bot.db.add_warning(guild.id, member.id, bot.user.id, "Exceeded 5 failed verification attempts (Warning #1)")
        try:
            await member.send(f"⚠️ **[Warning #1]** You failed verification 5 times in **{guild.name}**. Please be careful!")
        except Exception:
            pass
        return "⚠️ **Warning #1 Issued!** You exceeded 5 failed verification attempts."

    elif warn_count == 1:
        if bot.db:
            await bot.db.add_warning(guild.id, member.id, bot.user.id, "Exceeded 10 failed verification attempts (Warning #2)")
        try:
            await member.send(f"⚠️ **[Warning #2]** You failed verification 10 times in **{guild.name}**. One more violation will result in a KICK!")
        except Exception:
            pass
        return "⚠️ **Warning #2 Issued!** You exceeded 10 failed verification attempts. Further failures will result in a KICK."

    elif warn_count == 2:
        if bot.db:
            await bot.db.add_warning(guild.id, member.id, bot.user.id, "Exceeded verification limit 3 times (KICK)")
        try:
            await member.send(f"👢 **You were kicked from {guild.name}** for failing verification 3 consecutive times.")
            await member.kick(reason="[Passkey Gatekeeper] Exceeded 5 failed verification attempts 3 times.")
        except Exception as e:
            log.warning(f"Could not kick member {member}: {e}")
        return "👢 **Kicked from Server!** You exceeded verification attempts 3 times."

    else:
        try:
            await member.send(f"🔨 **You have been banned from {guild.name}** due to repeated verification abuse.")
            await member.ban(reason="[Passkey Gatekeeper] Repeated verification abuse after kick.", delete_message_days=1)
        except Exception as e:
            log.warning(f"Could not ban member {member}: {e}")
        return "🔨 **Banned from Server!** Repeated verification abuse."


async def handle_alt_detection(bot, guild: discord.Guild, member: discord.Member, alt_user_id: str, method: str = "IP/Email") -> Tuple[bool, str]:
    """Execute the configured Anti-Alt punishment policy."""
    config = {}
    if bot.db:
        config = await bot.db.get_guild_config(guild.id)

    action = config.get("antialt_action", "quarantine").lower()
    if action == "ignore":
        return True, "Allowed."

    alt_member = guild.get_member(int(alt_user_id)) if alt_user_id.isdigit() else None
    alt_mention = alt_member.mention if alt_member else f"`{alt_user_id}`"

    log_channel_id = config.get("log_channel_id")
    log_chan = guild.get_channel(int(log_channel_id)) if log_channel_id else (discord.utils.get(guild.text_channels, name="passkey-logs") or discord.utils.get(guild.text_channels, name="security-logs"))
    if log_chan:
        alt_emoji = Emojis.get("alt", bot)
        embed = discord.Embed(
            title=f"{alt_emoji} Alt Account Detected!",
            description=(
                f"**New Account**: {member.mention} (`{member.id}`)\n"
                f"**Linked Alt**: {alt_mention}\n"
                f"**Detection Method**: `{method}`\n"
                f"**Action Applied**: `{action.upper()}`"
            ),
            color=0xEF4444,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Passkey Deep Neural Anti-Alt Defense")
        try:
            await log_chan.send(embed=embed)
        except Exception as e:
            log.warning(f"Failed to send alt alert to log channel: {e}")

    if action == "log":
        return True, "Alt link logged to moderators."

    if action == "kick":
        try:
            await member.send(f"❌ You were kicked from **{guild.name}** because this account is linked to an existing member ({alt_mention}).")
            await member.kick(reason=f"[Passkey Anti-Alt] Linked to existing member {alt_user_id}")
        except Exception:
            pass
        return False, "This account is flagged as an alternate account and was kicked."

    if action == "ban":
        try:
            await member.send(f"🔨 You were banned from **{guild.name}** for attempting to join with an alternate account.")
            await member.ban(reason=f"[Passkey Anti-Alt] Linked to existing member {alt_user_id}", delete_message_days=0)
        except Exception:
            pass
        return False, "This account is flagged as an alternate account and was banned."

    if action == "quarantine":
        q_role = discord.utils.get(guild.roles, name="Quarantined")
        if not q_role:
            try:
                q_role = await guild.create_role(name="Quarantined", color=discord.Color.dark_red(), reason="[Passkey] Alt Quarantine Role")
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(q_role, read_messages=False, send_messages=False)
                    except Exception:
                        pass
            except Exception:
                pass

        if q_role:
            try:
                await member.add_roles(q_role, reason="[Passkey Anti-Alt] Suspected Alt Account")
                if alt_member:
                    await alt_member.add_roles(q_role, reason="[Passkey Anti-Alt] Suspected Alt Master")
            except Exception:
                pass

        return False, "Suspected alternate account detected. Both linked accounts have been placed in quarantine for administrator review."

    return True, "OK"


async def grant_verified_role(bot, guild: discord.Guild, member: discord.Member, method: str = "button", email: str = "") -> Tuple[bool, str]:
    """Helper to grant verified role, check account age, and log to db/channel."""
    config = {}
    if bot.db:
        config = await bot.db.get_guild_config(guild.id)

    min_age_days = int(config.get("min_age_days") or 0)
    if min_age_days > 0:
        created_at = member.created_at
        account_age_days = (datetime.datetime.now(datetime.timezone.utc) - created_at).days
        if account_age_days < min_age_days:
            return False, f"Your Discord account is too new ({account_age_days} days old). Minimum required is {min_age_days} days."

    verified_role_id = config.get("verified_role_id")
    verified_role = guild.get_role(int(verified_role_id)) if verified_role_id else discord.utils.get(guild.roles, name="Verified")

    if not verified_role:
        try:
            verified_role = await guild.create_role(name="Verified", color=discord.Color.from_rgb(16, 185, 129))
            if bot.db:
                await bot.db.set_guild_config(guild.id, "verified_role_id", str(verified_role.id))
        except Exception as e:
            return False, f"Could not create or find Verified role: {e}"

    if verified_role in member.roles:
        return True, "Already verified."

    try:
        await member.add_roles(verified_role, reason=f"[Passkey Gatekeeper] Verified via {method}")
        if bot.db:
            await bot.db.log_verification(guild.id, member.id, method=method, email=email)

        VERIFY_FAILED_ATTEMPTS.pop((guild.id, member.id), None)

        log_channel_id = config.get("log_channel_id")
        if log_channel_id:
            log_chan = guild.get_channel(int(log_channel_id))
            if log_chan:
                embed = discord.Embed(
                    title="🔑 Member Verified",
                    description=f"{member.mention} (`{member.id}`) passed gatekeeper verification.",
                    color=0x10B981,
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
                embed.add_field(name="Method", value=f"`{method.upper()}`", inline=True)
                embed.add_field(name="Account Age", value=f"`{(datetime.datetime.now(datetime.timezone.utc) - member.created_at).days} days`", inline=True)
                if email:
                    embed.add_field(name="Verified Email", value=f"`{email}`", inline=False)
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await log_chan.send(embed=embed)
                except Exception:
                    pass

        return True, "Verified successfully."
    except Exception as e:
        return False, f"Failed to assign role: {e}"


# --- Modals & Views for Verification Modes ---

class MathCaptchaModal(discord.ui.Modal, title="🔢 Math Security Challenge"):
    def __init__(self, bot, guild: discord.Guild, num1: int, num2: int):
        super().__init__()
        self.bot = bot
        self.guild = guild
        self.answer = str(num1 + num2)

        self.captcha_input = discord.ui.TextInput(
            label=f"What is {num1} + {num2}?",
            placeholder="Type the correct numeric answer...",
            min_length=1,
            max_length=6,
            required=True
        )
        self.add_item(self.captcha_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_ans = self.captcha_input.value.strip()
        if user_ans != self.answer:
            penalty_msg = await handle_failed_attempt(self.bot, self.guild, interaction.user, "Incorrect arithmetic answer")
            await interaction.response.send_message(penalty_msg, ephemeral=True)
            return

        VERIFY_FAILED_ATTEMPTS.pop((self.guild.id, interaction.user.id), None)
        success, msg = await grant_verified_role(self.bot, self.guild, interaction.user, method="math_captcha")
        if success:
            await interaction.response.send_message(f"✅ **Verification Successful!** Welcome to **{self.guild.name}**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ {msg}", ephemeral=True)


class ImageCaptchaModal(discord.ui.Modal, title="🖼️ Visual CAPTCHA Verification"):
    def __init__(self, bot, guild: discord.Guild, expected_code: str):
        super().__init__()
        self.bot = bot
        self.guild = guild
        self.expected_code = expected_code.upper()

        self.inp_code = discord.ui.TextInput(
            label="Enter the 5 characters shown in the image:",
            placeholder="e.g. 7KP9X",
            min_length=5,
            max_length=5,
            required=True
        )
        self.add_item(self.inp_code)

    async def on_submit(self, interaction: discord.Interaction):
        user_code = self.inp_code.value.strip().upper()
        if user_code != self.expected_code:
            penalty_msg = await handle_failed_attempt(self.bot, self.guild, interaction.user, "Incorrect image CAPTCHA code")
            await interaction.response.send_message(penalty_msg, ephemeral=True)
            return

        VERIFY_FAILED_ATTEMPTS.pop((self.guild.id, interaction.user.id), None)
        IMAGE_CAPTCHA_STORE.pop((self.guild.id, interaction.user.id), None)
        success, msg = await grant_verified_role(self.bot, self.guild, interaction.user, method="image_captcha")
        if success:
            await interaction.response.send_message(f"✅ **Verification Successful!** Welcome to **{self.guild.name}**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ {msg}", ephemeral=True)


class ImageCaptchaChallengeView(discord.ui.View):
    def __init__(self, bot, guild: discord.Guild, code: str):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild = guild
        self.code = code

    @discord.ui.button(label="Submit CAPTCHA Code", style=discord.ButtonStyle.primary, emoji="⌨️")
    async def btn_submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ImageCaptchaModal(self.bot, self.guild, self.code)
        await interaction.response.send_modal(modal)


class EmojiSequenceView(discord.ui.View):
    """Interactive Emoji Sequence Pattern Matching Challenge."""
    def __init__(self, bot, guild: discord.Guild, target_sequence: List[str], all_emojis: List[str]):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild
        self.target_sequence = target_sequence
        self.entered_sequence: List[str] = []

        shuffled = random.sample(all_emojis, len(all_emojis))
        for emoji in shuffled:
            btn = discord.ui.Button(label=emoji, style=discord.ButtonStyle.secondary, custom_id=f"seq_{emoji}")
            btn.callback = self._make_callback(emoji)
            self.add_item(btn)

    def _make_callback(self, emoji: str):
        async def callback(interaction: discord.Interaction):
            self.entered_sequence.append(emoji)
            idx = len(self.entered_sequence) - 1

            if self.entered_sequence[idx] != self.target_sequence[idx]:
                self.stop()
                penalty_msg = await handle_failed_attempt(self.bot, self.guild, interaction.user, "Incorrect emoji sequence")
                await interaction.response.send_message(penalty_msg, ephemeral=True)
                return

            if len(self.entered_sequence) == len(self.target_sequence):
                self.stop()
                VERIFY_FAILED_ATTEMPTS.pop((self.guild.id, interaction.user.id), None)
                success, msg = await grant_verified_role(self.bot, self.guild, interaction.user, method="emoji_sequence")
                if success:
                    await interaction.response.send_message(f"🎉 **Pattern Matched!** Welcome to **{self.guild.name}**!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"⚠️ {msg}", ephemeral=True)
            else:
                progress = " ".join(self.entered_sequence)
                await interaction.response.send_message(f"🧩 Pattern Progress: `{progress}` ({len(self.entered_sequence)}/{len(self.target_sequence)})", ephemeral=True)

        return callback


class ServerRulesModal(discord.ui.Modal, title="📜 Server Rules & Agreement"):
    def __init__(self, bot, guild: discord.Guild):
        super().__init__()
        self.bot = bot
        self.guild = guild

        self.inp_agree = discord.ui.TextInput(
            label="Do you agree to follow the server rules?",
            placeholder="Type 'I AGREE' to confirm...",
            min_length=7,
            max_length=7,
            required=True
        )
        self.add_item(self.inp_agree)

    async def on_submit(self, interaction: discord.Interaction):
        ans = self.inp_agree.value.strip().upper()
        if ans != "I AGREE":
            penalty_msg = await handle_failed_attempt(self.bot, self.guild, interaction.user, "You must type 'I AGREE' to accept the server rules")
            await interaction.response.send_message(penalty_msg, ephemeral=True)
            return

        VERIFY_FAILED_ATTEMPTS.pop((self.guild.id, interaction.user.id), None)
        success, msg = await grant_verified_role(self.bot, self.guild, interaction.user, method="rules_agreement")
        if success:
            await interaction.response.send_message(f"✅ **Rules Accepted!** Welcome to **{self.guild.name}**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ {msg}", ephemeral=True)


class VerifyButtonView(discord.ui.View):
    def __init__(self, bot, guild_id: int = 0):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Click to Verify", style=discord.ButtonStyle.success, emoji="🔑", custom_id="passkey:btn_verify")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild or self.bot.get_guild(self.guild_id)
        if not guild:
            await interaction.response.send_message("❌ Server context not found.", ephemeral=True)
            return

        config = {}
        if self.bot.db:
            config = await self.bot.db.get_guild_config(guild.id)

        verified_role_id = config.get("verified_role_id")
        verified_role = guild.get_role(int(verified_role_id)) if verified_role_id else discord.utils.get(guild.roles, name="Verified")

        if verified_role and verified_role in interaction.user.roles:
            await interaction.response.send_message("✅ You are already verified in this server!", ephemeral=True)
            return

        mode = config.get("verify_mode", "web").lower()
        lang = config.get("language", "en")

        # 1. Direct Button Mode
        if mode == "button":
            success, msg = await grant_verified_role(self.bot, guild, interaction.user, method="button")
            if success:
                await interaction.response.send_message("✅ **Verified successfully!** You now have access to the server.", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            return

        # 2. Math CAPTCHA Modal Mode
        if mode == "captcha":
            n1 = random.randint(1, 20)
            n2 = random.randint(1, 20)
            modal = MathCaptchaModal(self.bot, guild, n1, n2)
            await interaction.response.send_modal(modal)
            return

        # 3. Image Visual CAPTCHA Mode
        if mode == "image_captcha":
            buf, code = generate_image_captcha()
            file = discord.File(buf, filename="passkey_captcha.png")
            embed = discord.Embed(
                title="🖼️ Passkey Visual Security Challenge",
                description="Please read the 5 characters inside the image below and click **Submit CAPTCHA Code** to answer.",
                color=0x6366F1
            )
            embed.set_image(url="attachment://passkey_captcha.png")
            embed.set_footer(text="Passkey Zero-Trust Security • 5-Attempt Limit")
            view = ImageCaptchaChallengeView(self.bot, guild, code)
            await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)
            return

        # 4. Emoji Sequence Pattern Mode
        if mode == "pattern":
            emojis_pool = ["🔑", "🛡️", "⚡", "💎", "⭐", "🔒"]
            target_seq = random.sample(emojis_pool, 3)
            seq_display = " ".join(target_seq)
            embed = discord.Embed(
                title="🎮 Passkey Emoji Pattern Challenge",
                description=(
                    f"Please click the buttons below in this **exact sequence**:\n\n"
                    f"# {seq_display}\n\n"
                    f"⚠️ *Click each emoji in order. One mistake will reset the attempt.*"
                ),
                color=0x6366F1
            )
            view = EmojiSequenceView(self.bot, guild, target_seq, emojis_pool)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        # 5. Server Rules Agreement Mode
        if mode == "rules":
            modal = ServerRulesModal(self.bot, guild)
            await interaction.response.send_modal(modal)
            return

        # 6. Social Connection Check Mode
        if mode == "social":
            embed = discord.Embed(
                title="🔗 Passkey Social Account Verification",
                description=(
                    f"Hello **{interaction.user.display_name}**,\n\n"
                    f"This server requires members to have at least **1 connected account** on their Discord profile (e.g. Steam, YouTube, GitHub, Twitter, Spotify, Reddit, etc.).\n\n"
                    "Click the button below to verify your linked connections:"
                ),
                color=0x6366F1
            )
            token = f"pk_{secrets.token_hex(16)}"
            VERIFY_SESSIONS[token] = {"user_id": interaction.user.id, "guild_id": guild.id, "created_at": time.time()}
            from utils.config import Config
            verify_url = f"{Config.DASHBOARD_URL.rstrip('/')}/verify?session={token}"
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Check Social Connections", url=verify_url, style=discord.ButtonStyle.link, emoji="🔗"))
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        # 7. Web Portal, Biometric Passkey, or Email Verification Mode
        token = f"pk_{secrets.token_hex(16)}"
        VERIFY_SESSIONS[token] = {
            "user_id": interaction.user.id,
            "guild_id": guild.id,
            "created_at": time.time()
        }

        from utils.config import Config
        base_url = Config.DASHBOARD_URL.rstrip("/")
        verify_url = f"{base_url}/verify?session={token}"

        is_email = (mode == "email")
        is_biometric = (mode == "biometric")

        if is_biometric:
            title = "📱 Passkey — Hardware Biometric Verification"
            desc = (
                f"Hello **{interaction.user.display_name}**,\n\n"
                f"Click the button below to verify using **Hardware Passkey (Touch ID, Face ID, Windows Hello, or YubiKey)**.\n\n"
                f"⏱️ *Session remains active for 10 minutes.*"
            )
            btn_label = "Verify with Biometrics / TouchID"
            btn_emoji = "📱"
        elif is_email:
            title = "📧 Passkey — Cổng Xác Thực Email" if lang == "vi" else "📧 Passkey — Email Verification Portal"
            desc = (
                f"Xin chào **{interaction.user.display_name}**,\n\nVui lòng bấm nút bên dưới để mở cổng **Xác thực mã OTP Email** cho server **{guild.name}**.\n\n💡 **Lưu ý:** Nếu không thấy mã trong Hộp thư đến, vui lòng kiểm tra thêm mục **Thư rác / Spam** nhé!"
            ) if lang == "vi" else (
                f"Hello **{interaction.user.display_name}**,\n\nClick the button below to complete **Email OTP Verification** for **{guild.name}**.\n\n💡 **Note:** If you don't see the code in your inbox, check your **Spam folder**!"
            )
            btn_label = "Mở Cổng Xác Thực Email" if lang == "vi" else "Open Email Verification"
            btn_emoji = "✉️"
        else:
            title = "🔑 Passkey — Cổng Xác Thực Người Dùng" if lang == "vi" else "🔑 Passkey — Human Verification Portal"
            desc = (
                f"Xin chào **{interaction.user.display_name}**,\n\nVui lòng bấm nút bên dưới để hoàn tất xác thực Cloudflare Turnstile cho **{guild.name}**.\n\n⚠️ *Bạn có tối đa 5 lần thử.*"
            ) if lang == "vi" else (
                f"Hello **{interaction.user.display_name}**,\n\nPlease click the button below to complete Cloudflare Turnstile verification for **{guild.name}**.\n\n⚠️ *You have up to 5 attempts.*"
            )
            btn_label = "Mở Cổng Xác Thực" if lang == "vi" else "Open Verification Portal"
            btn_emoji = "🌐"

        embed = discord.Embed(title=title, description=desc, color=0x6366F1)
        embed.set_footer(text="Passkey Gatekeeper • Zero-Trust Verification Network")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        web_view = discord.ui.View()
        web_view.add_item(discord.ui.Button(label=btn_label, url=verify_url, style=discord.ButtonStyle.link, emoji=btn_emoji))
        await interaction.response.send_message(embed=embed, view=web_view, ephemeral=True)


# --- Multi-Step Interactive Setup Wizard View (5 Steps) ---

class MultiStepSetupWizardView(discord.ui.View):
    def __init__(self, bot, guild: discord.Guild, author: discord.Member):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.author = author

        self.current_step = 1
        self.total_steps = 5

        # Wizard state
        self.selected_mode = "web"
        self.selected_lang = "en"
        self.selected_antialt = "quarantine"
        self.selected_verify_chan = None
        self.selected_log_chan = None
        self.selected_age = 0

        self._build_step_components()

    def _build_step_components(self):
        self.clear_items()

        # Step 1: All 9 Verification Modes
        if self.current_step == 1:
            select = discord.ui.Select(
                placeholder="1️⃣ Select Verification Method (9 Modes Available)...",
                min_values=1,
                max_values=1,
                row=0,
                options=[
                    discord.SelectOption(label="🌐 Web Portal (Cloudflare Turnstile)", value="web", description="Browser challenge with Cloudflare Turnstile + Anti-Alt IP", default=(self.selected_mode == "web")),
                    discord.SelectOption(label="📱 Biometric Passkey (Touch ID / Face ID)", value="biometric", description="Hardware Passkey WebAuthn biometric verification", default=(self.selected_mode == "biometric")),
                    discord.SelectOption(label="✉️ Email OTP", value="email", description="Sends 6-digit verification code to member email", default=(self.selected_mode == "email")),
                    discord.SelectOption(label="🖼️ In-Discord Image CAPTCHA", value="image_captcha", description="Distorted security image challenge inside Discord", default=(self.selected_mode == "image_captcha")),
                    discord.SelectOption(label="🎮 Emoji Sequence Pattern", value="pattern", description="Randomized 3-symbol sequence button matching challenge", default=(self.selected_mode == "pattern")),
                    discord.SelectOption(label="🔗 Social Connection Check", value="social", description="Requires linked Steam, GitHub, YouTube, Twitter, etc.", default=(self.selected_mode == "social")),
                    discord.SelectOption(label="🔢 Math CAPTCHA Modal", value="captcha", description="Interactive math challenge pop-up in Discord", default=(self.selected_mode == "captcha")),
                    discord.SelectOption(label="📝 Server Rules Quiz", value="rules", description="Requires typing 'I AGREE' to server rules", default=(self.selected_mode == "rules")),
                    discord.SelectOption(label="⚡ Direct 1-Click Button", value="button", description="Instant verification inside Discord with single click", default=(self.selected_mode == "button")),
                ]
            )
            select.callback = self._on_select_mode
            self.add_item(select)

        # Step 2: Language
        elif self.current_step == 2:
            select = discord.ui.Select(
                placeholder="2️⃣ Select Default Server Language...",
                min_values=1,
                max_values=1,
                row=0,
                options=[
                    discord.SelectOption(label="🇬🇧 English", value="en", description="Default system language", default=(self.selected_lang == "en")),
                    discord.SelectOption(label="🇻🇳 Tiếng Việt", value="vi", description="Giao diện Tiếng Việt", default=(self.selected_lang == "vi")),
                    discord.SelectOption(label="🇯🇵 日本語", value="ja", description="Japanese interface", default=(self.selected_lang == "ja")),
                    discord.SelectOption(label="🇰🇷 한국어", value="ko", description="Korean interface", default=(self.selected_lang == "ko")),
                    discord.SelectOption(label="🇨🇳 简体中文", value="zh", description="Chinese interface", default=(self.selected_lang == "zh")),
                    discord.SelectOption(label="🇪🇸 Español", value="es", description="Spanish interface", default=(self.selected_lang == "es")),
                    discord.SelectOption(label="🇫🇷 Français", value="fr", description="French interface", default=(self.selected_lang == "fr")),
                    discord.SelectOption(label="🇩🇪 Deutsch", value="de", description="German interface", default=(self.selected_lang == "de")),
                    discord.SelectOption(label="🇷🇺 Русский", value="ru", description="Russian interface", default=(self.selected_lang == "ru")),
                    discord.SelectOption(label="🇧🇷 Português", value="pt", description="Portuguese interface", default=(self.selected_lang == "pt")),
                ]
            )
            select.callback = self._on_select_lang
            self.add_item(select)

        # Step 3: Anti-Alt Suspicion Policy
        elif self.current_step == 3:
            select = discord.ui.Select(
                placeholder="3️⃣ If an Alt Account is Detected...",
                min_values=1,
                max_values=1,
                row=0,
                options=[
                    discord.SelectOption(label="⚠️ Quarantine Both Accounts", value="quarantine", description="Lock both suspected accounts in @Quarantined for admin review", default=(self.selected_antialt == "quarantine")),
                    discord.SelectOption(label="📋 Log & Alert Only", value="log", description="Alert moderators in log channel but allow member to join", default=(self.selected_antialt == "log")),
                    discord.SelectOption(label="👢 Auto-Kick New Alt", value="kick", description="Kick the new alternate account immediately", default=(self.selected_antialt == "kick")),
                    discord.SelectOption(label="🔨 Auto-Ban New Alt", value="ban", description="Ban the new alternate account immediately", default=(self.selected_antialt == "ban")),
                    discord.SelectOption(label="🤫 Silent / Do Nothing", value="ignore", description="Do not log or take any action on duplicate accounts", default=(self.selected_antialt == "ignore")),
                ]
            )
            select.callback = self._on_select_antialt
            self.add_item(select)

        # Step 4: Channels Configuration
        elif self.current_step == 4:
            chan_select = discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.text],
                placeholder="📢 Select Verification Channel (or leave for auto #verify)...",
                min_values=1,
                max_values=1,
                row=0
            )
            chan_select.callback = self._on_select_verify_chan
            self.add_item(chan_select)

            log_select = discord.ui.ChannelSelect(
                channel_types=[discord.ChannelType.text],
                placeholder="📋 Select Security Log Channel (or leave for auto #passkey-logs)...",
                min_values=1,
                max_values=1,
                row=1
            )
            log_select.callback = self._on_select_log_chan
            self.add_item(log_select)

        # Step 5: Minimum Account Age & Review
        elif self.current_step == 5:
            select = discord.ui.Select(
                placeholder="5️⃣ Select Minimum Account Age...",
                min_values=1,
                max_values=1,
                row=0,
                options=[
                    discord.SelectOption(label="🛡️ 0 Days (Disabled - Allow all accounts)", value="0", default=(self.selected_age == 0)),
                    discord.SelectOption(label="🛡️ 3 Days (Block fresh raid accounts)", value="3", default=(self.selected_age == 3)),
                    discord.SelectOption(label="🛡️ 7 Days (Recommended Security)", value="7", default=(self.selected_age == 7)),
                    discord.SelectOption(label="🛡️ 14 Days (Strict Anti-Raid)", value="14", default=(self.selected_age == 14)),
                    discord.SelectOption(label="🛡️ 30 Days (Maximum Security)", value="30", default=(self.selected_age == 30)),
                ]
            )
            select.callback = self._on_select_age
            self.add_item(select)

        # Navigation row: < and > buttons
        btn_prev = discord.ui.Button(label="Previous", style=discord.ButtonStyle.secondary, emoji="◀️", row=2, disabled=(self.current_step == 1))
        btn_prev.callback = self._on_prev
        self.add_item(btn_prev)

        btn_indicator = discord.ui.Button(label=f"Step {self.current_step}/{self.total_steps}", style=discord.ButtonStyle.secondary, disabled=True, row=2)
        self.add_item(btn_indicator)

        if self.current_step < self.total_steps:
            btn_next = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, emoji="▶️", row=2)
            btn_next.callback = self._on_next
            self.add_item(btn_next)
        else:
            btn_deploy = discord.ui.Button(label="Finish & Deploy Setup", style=discord.ButtonStyle.success, emoji="🚀", row=2)
            btn_deploy.callback = self._on_deploy
            self.add_item(btn_deploy)

    def get_step_embed(self) -> discord.Embed:
        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)
        otp_emoji = Emojis.get("otp", self.bot)
        biometric_emoji = Emojis.get("biometric", self.bot)
        pattern_emoji = Emojis.get("pattern", self.bot)
        social_emoji = Emojis.get("social", self.bot)
        alt_emoji = Emojis.get("alt", self.bot)
        lock_emoji = Emojis.get("lock", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey Setup Wizard [Step {self.current_step}/{self.total_steps}]",
            color=0x6366F1
        )
        if self.guild.icon:
            embed.set_thumbnail(url=self.guild.icon.url)

        if self.current_step == 1:
            embed.description = (
                "### 1️⃣ Choose Verification Engine\n"
                "Select one of the **9 advanced verification modes**:\n\n"
                f"• **{verified_emoji} Web Portal**: Cloudflare Turnstile CAPTCHA + Anti-Alt IP.\n"
                f"• **{biometric_emoji} Biometric Passkey**: Hardware Touch ID / Face ID / WebAuthn.\n"
                f"• **{otp_emoji} Email OTP**: 6-digit one-time code to member email.\n"
                f"• **{lock_emoji} Image Visual CAPTCHA**: In-Discord distorted character puzzle.\n"
                f"• **{pattern_emoji} Emoji Sequence**: 3-symbol pattern button matching game.\n"
                f"• **{social_emoji} Social Check**: Requires linked Steam, YouTube, GitHub, etc.\n"
                f"• **{shield_emoji} Math CAPTCHA**: Quick arithmetic modal challenge.\n"
                f"• **{lock_emoji} Rules Agreement**: Server rules confirmation modal.\n"
                f"• **{passkey_emoji} 1-Click Button**: Instant click access.\n\n"
                f"👉 **Current Selection**: `{self.selected_mode.upper()}`"
            )
        elif self.current_step == 2:
            embed.description = (
                "### 2️⃣ Choose Default Server Language\n"
                "Select the default language for verification prompts, embeds, and emails:\n\n"
                "• Supports 10 global languages (English default, Vietnamese, Japanese, Korean, etc.)\n\n"
                f"👉 **Current Selection**: `{self.selected_lang.upper()}`"
            )
        elif self.current_step == 3:
            embed.description = (
                f"### 3️⃣ {alt_emoji} Anti-Alt Account Action Policy\n"
                "What should the bot do when a duplicate IP or Email is detected?\n\n"
                "• **⚠️ Quarantine Both Accounts**: Assigns `@Quarantined` to freeze both accounts for admin review.\n"
                "• **📋 Log & Alert Only**: Sends security audit log to staff, but allows join.\n"
                "• **👢 Auto-Kick**: Instantly kicks the new alt account.\n"
                "• **🔨 Auto-Ban**: Instantly bans the new alt account.\n"
                "• **🤫 Silent Ignore**: Does not log or penalize.\n\n"
                f"👉 **Current Selection**: `{self.selected_antialt.upper()}`"
            )
        elif self.current_step == 4:
            v_text = self.selected_verify_chan.mention if self.selected_verify_chan else "`Auto-create #verify`"
            l_text = self.selected_log_chan.mention if self.selected_log_chan else "`Auto-create #passkey-logs`"
            embed.description = (
                f"### 4️⃣ {shield_emoji} Channel Configuration\n"
                "Select where members verify and where audit logs will be sent:\n\n"
                f"• **Verification Channel**: {v_text}\n"
                f"• **Security Log Channel**: {l_text}\n\n"
                "*(Select from dropdowns or leave empty to auto-create standard channels)*"
            )
        elif self.current_step == 5:
            v_text = self.selected_verify_chan.mention if self.selected_verify_chan else "`Auto-create #verify`"
            l_text = self.selected_log_chan.mention if self.selected_log_chan else "`Auto-create #passkey-logs`"
            embed.description = (
                f"### 5️⃣ {shield_emoji} Minimum Account Age & Ready to Deploy\n"
                "Filter out newly created raid accounts under a certain age:\n\n"
                f"• **Account Age**: `{self.selected_age} days`\n\n"
                "📋 **Configuration Summary**:\n"
                f"• **Method**: `{self.selected_mode.upper()}`\n"
                f"• **Language**: `{self.selected_lang.upper()}`\n"
                f"• **Anti-Alt Policy**: `{self.selected_antialt.upper()}`\n"
                f"• **Verify Channel**: {v_text}\n"
                f"• **Log Channel**: {l_text}\n"
                f"• **Min Age**: `{self.selected_age} days`\n"
                "• **Attempt Limit**: `5 attempts (3 strikes -> Kick / Ban)`\n\n"
                f"Click **{passkey_emoji} Finish & Deploy Setup** to activate Passkey Gatekeeper!"
            )

        embed.set_footer(text="Use ◀️ and ▶️ buttons to navigate between steps • Passkey")
        return embed

    async def _on_select_mode(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        self.selected_mode = interaction.data["values"][0]
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_select_lang(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        self.selected_lang = interaction.data["values"][0]
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_select_antialt(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        self.selected_antialt = interaction.data["values"][0]
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_select_verify_chan(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        chan_id = interaction.data["values"][0]
        self.selected_verify_chan = self.guild.get_channel(int(chan_id))
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_select_log_chan(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        chan_id = interaction.data["values"][0]
        self.selected_log_chan = self.guild.get_channel(int(chan_id))
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_select_age(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        self.selected_age = int(interaction.data["values"][0])
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_prev(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        if self.current_step > 1:
            self.current_step -= 1
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_next(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can interact.", ephemeral=True)
            return
        if self.current_step < self.total_steps:
            self.current_step += 1
        self._build_step_components()
        await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    async def _on_deploy(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who started setup can deploy.", ephemeral=True)
            return

        await interaction.response.defer()
        guild = self.guild

        # 1. Create or find @Verified role
        verified_role = discord.utils.get(guild.roles, name="Verified")
        if not verified_role:
            try:
                verified_role = await guild.create_role(
                    name="Verified",
                    color=discord.Color.from_rgb(16, 185, 129),
                    reason="[Passkey Setup] Created Verified Member Role"
                )
            except Exception as e:
                await interaction.followup.send(f"❌ Failed to create `@Verified` role: {e}")
                return

        # 2. Setup #verify channel
        verify_channel = self.selected_verify_chan or discord.utils.get(guild.text_channels, name="verify") or discord.utils.get(guild.text_channels, name="verification")
        if not verify_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                verified_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, view_channel=True)
            }
            try:
                verify_channel = await guild.create_text_channel(
                    name="verify",
                    overwrites=overwrites,
                    topic="[Passkey Gatekeeper] Click the button below to verify and gain access to the server.",
                    reason="[Passkey Setup] Created Verification Gateway Channel"
                )
            except Exception as e:
                await interaction.followup.send(f"❌ Failed to create `#verify` channel: {e}")
                return
        else:
            # Ensure bot has explicit permission to post in existing channel
            try:
                await verify_channel.set_permissions(
                    guild.me,
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    view_channel=True,
                    reason="[Passkey Setup] Ensure Bot Permissions"
                )
            except Exception:
                pass

        # 3. Setup #passkey-logs channel
        log_channel = self.selected_log_chan or discord.utils.get(guild.text_channels, name="passkey-logs") or discord.utils.get(guild.text_channels, name="security-logs")
        if not log_channel and self.selected_log_chan is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True, view_channel=True)
            }
            try:
                log_channel = await guild.create_text_channel(
                    name="passkey-logs",
                    overwrites=overwrites,
                    topic="[Passkey Gatekeeper] Security audit, verification logs, and alt detection alerts.",
                    reason="[Passkey Setup] Created Passkey Security Log Channel"
                )
            except Exception:
                pass

        # 4. Save settings to DB
        if self.bot.db:
            await self.bot.db.set_guild_config(guild.id, "verified_role_id", str(verified_role.id))
            await self.bot.db.set_guild_config(guild.id, "verify_channel_id", str(verify_channel.id))
            if log_channel:
                await self.bot.db.set_guild_config(guild.id, "log_channel_id", str(log_channel.id))
            await self.bot.db.set_guild_config(guild.id, "verify_mode", self.selected_mode)
            await self.bot.db.set_guild_config(guild.id, "language", self.selected_lang)
            await self.bot.db.set_guild_config(guild.id, "antialt_action", self.selected_antialt)
            await self.bot.db.set_guild_config(guild.id, "min_age_days", self.selected_age)

        # 5. Post Verification Embed to #verify
        passkey_emoji = Emojis.get("passkey", self.bot)
        shield_emoji = Emojis.get("shield", self.bot)
        verified_emoji = Emojis.get("verified", self.bot)

        embed = discord.Embed(
            title=f"{passkey_emoji} Passkey Server Gatekeeper",
            description=(
                f"Welcome to **{guild.name}**!\n\n"
                "To prevent automated raid bots and maintain community safety, "
                "please click the **Click to Verify** button below to complete verification.\n\n"
                f"• **Verification Method**: `{self.selected_mode.upper()}`\n"
                f"• **Language**: `{self.selected_lang.upper()}`\n"
                f"• **Instant Access**: {verified_emoji} Unlocks full access to all member channels immediately."
            ),
            color=0x6366F1
        )
        embed.set_footer(text="Protected by Passkey Zero-Trust Gatekeeper")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        view = VerifyButtonView(self.bot, guild.id)
        try:
            await verify_channel.send(embed=embed, view=view)
        except Exception as e:
            log.warning(f"Could not send verify panel: {e}")

        # 6. Confirmation message
        summary_embed = discord.Embed(
            title=f"{verified_emoji} Passkey Gatekeeper Deployed Successfully!",
            description=f"{shield_emoji} Your server is now protected by Passkey Zero-Trust Security Network.",
            color=0x10B981
        )
        summary_embed.add_field(name="Verification Channel", value=verify_channel.mention, inline=True)
        summary_embed.add_field(name="Log Channel", value=log_channel.mention if log_channel else "`None`", inline=True)
        summary_embed.add_field(name="Role", value=verified_role.mention, inline=True)
        summary_embed.add_field(name="Method", value=f"`{self.selected_mode.upper()}`", inline=True)
        summary_embed.add_field(name="Language", value=f"`{self.selected_lang.upper()}`", inline=True)
        summary_embed.add_field(name="Anti-Alt Action", value=f"`{self.selected_antialt.upper()}`", inline=True)
        summary_embed.add_field(name="Min Account Age", value=f"`{self.selected_age} days`", inline=True)

        self.stop()
        await interaction.followup.send(embed=summary_embed)


# --- Master Server Settings Dashboard View ---

def render_settings_embed(guild: discord.Guild, cfg: dict) -> discord.Embed:
    """Helper to generate the comprehensive server settings embed."""
    verified_role_id = cfg.get("verified_role_id")
    verified_role = guild.get_role(int(verified_role_id)) if verified_role_id else None
    
    verify_channel_id = cfg.get("verify_channel_id")
    verify_channel = guild.get_channel(int(verify_channel_id)) if verify_channel_id else discord.utils.get(guild.text_channels, name="verify")
    
    log_channel_id = cfg.get("log_channel_id")
    log_channel = guild.get_channel(int(log_channel_id)) if log_channel_id else None

    mode = str(cfg.get("verify_mode", "web")).upper()
    lang = str(cfg.get("language", "en")).upper()
    antialt_act = str(cfg.get("antialt_action", "quarantine")).upper()
    min_age = cfg.get("min_age_days", 0)

    spam_st = "🟢 ON" if cfg.get("automod_spam", 1) else "🔴 OFF"
    inv_st = "🟢 ON" if cfg.get("automod_invites", 1) else "🔴 OFF"
    phish_st = "🟢 ON" if cfg.get("automod_phishing", 1) else "🔴 OFF"
    ment_st = "🟢 ON" if cfg.get("automod_mentions", 1) else "🔴 OFF"
    alt_st = "🟢 ON" if cfg.get("antialt_enabled", 1) else "🔴 OFF"

    embed = discord.Embed(
        title=f"⚙️ Passkey Server Settings — {guild.name}",
        description="Master control dashboard for all security, verification, and defense settings.",
        color=0x6366F1,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(
        name="🔑 Verification & Gatekeeper",
        value=(
            f"• **Method**: `{mode}`\n"
            f"• **Role**: {verified_role.mention if verified_role else '`Not Set`'}\n"
            f"• **Channel**: {verify_channel.mention if verify_channel else '`Not Set`'}\n"
            f"• **Language**: `{lang}`\n"
            f"• **Min Account Age**: `{min_age} days`\n"
            f"• **Anti-Alt Policy**: `{antialt_act}`\n"
            f"• **Max Attempts**: `5 attempts (3 strikes -> Kick/Ban)`"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ AutoMod & Shield Defenses",
        value=(
            f"• **Anti-Spam**: {spam_st}\n"
            f"• **Anti-Invite**: {inv_st}\n"
            f"• **Anti-Phishing**: {phish_st}\n"
            f"• **Anti-Mention**: {ment_st}\n"
            f"• **Anti-Alt**: {alt_st}"
        ),
        inline=True
    )

    embed.add_field(
        name="📋 Audit & Logs",
        value=(
            f"• **Log Channel**: {log_channel.mention if log_channel else '`Not Set`'}\n"
            f"• **Database**: `Turso Cloud SQLite (Tokyo)`\n"
            f"• **SMTP Service**: `Online (TLS/SSL)`"
        ),
        inline=True
    )
    embed.set_footer(text="Use the buttons & menus below to toggle any setting instantly • Passkey")
    return embed


class ServerSettingsView(discord.ui.View):
    def __init__(self, bot, guild: discord.Guild, author: discord.Member, cfg: dict):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.author = author
        self.cfg = cfg

    async def _update_view(self, interaction: discord.Interaction):
        if self.bot.db:
            self.cfg = await self.bot.db.get_guild_config(self.guild.id)
        embed = render_settings_embed(self.guild, self.cfg)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="🔑 Change Verification Mode (9 Modes)...",
        row=0,
        options=[
            discord.SelectOption(label="🌐 Web Portal (Cloudflare Turnstile)", value="web", description="Browser challenge with Cloudflare Turnstile"),
            discord.SelectOption(label="📱 Biometric Passkey (Touch ID / Face ID)", value="biometric", description="Hardware Passkey biometric authentication"),
            discord.SelectOption(label="✉️ Email OTP", value="email", description="6-digit verification code sent to member email"),
            discord.SelectOption(label="🖼️ In-Discord Image CAPTCHA", value="image_captcha", description="Distorted security image challenge in Discord"),
            discord.SelectOption(label="🎮 Emoji Sequence Pattern", value="pattern", description="3-symbol sequence button matching challenge"),
            discord.SelectOption(label="🔗 Social Connection Check", value="social", description="Requires linked Steam, GitHub, YouTube, etc."),
            discord.SelectOption(label="🔢 Math CAPTCHA Modal", value="captcha", description="Interactive math challenge pop-up"),
            discord.SelectOption(label="📝 Server Rules Quiz", value="rules", description="Requires typing 'I AGREE' to server rules"),
            discord.SelectOption(label="⚡ Direct 1-Click Button", value="button", description="Instant verification inside Discord"),
        ]
    )
    async def sel_mode(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened the settings can modify them.", ephemeral=True)
            return
        mode = select.values[0]
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "verify_mode", mode)
        await self._update_view(interaction)

    @discord.ui.select(
        placeholder="🌐 Change Server Language...",
        row=1,
        options=[
            discord.SelectOption(label="🇬🇧 English", value="en", description="Default English"),
            discord.SelectOption(label="🇻🇳 Tiếng Việt", value="vi", description="Vietnamese interface"),
            discord.SelectOption(label="🇯🇵 日本語", value="ja", description="Japanese interface"),
            discord.SelectOption(label="🇰🇷 한국어", value="ko", description="Korean interface"),
            discord.SelectOption(label="🇨🇳 简体中文", value="zh", description="Chinese interface"),
            discord.SelectOption(label="🇪🇸 Español", value="es", description="Spanish interface"),
            discord.SelectOption(label="🇫🇷 Français", value="fr", description="French interface"),
            discord.SelectOption(label="🇩🇪 Deutsch", value="de", description="German interface"),
            discord.SelectOption(label="🇷🇺 Русский", value="ru", description="Russian interface"),
            discord.SelectOption(label="🇧🇷 Português", value="pt", description="Portuguese interface"),
        ]
    )
    async def sel_lang(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened the settings can modify them.", ephemeral=True)
            return
        lang = select.values[0]
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "language", lang)
        await self._update_view(interaction)

    @discord.ui.button(label="Spam Shield", style=discord.ButtonStyle.secondary, emoji="🛡️", row=2)
    async def btn_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened settings can toggle this.", ephemeral=True)
            return
        new_val = 0 if self.cfg.get("automod_spam", 1) else 1
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "automod_spam", new_val)
        await self._update_view(interaction)

    @discord.ui.button(label="Invite Shield", style=discord.ButtonStyle.secondary, emoji="🔗", row=2)
    async def btn_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened settings can toggle this.", ephemeral=True)
            return
        new_val = 0 if self.cfg.get("automod_invites", 1) else 1
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "automod_invites", new_val)
        await self._update_view(interaction)

    @discord.ui.button(label="Phishing Shield", style=discord.ButtonStyle.secondary, emoji="🎣", row=2)
    async def btn_phishing(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened settings can toggle this.", ephemeral=True)
            return
        new_val = 0 if self.cfg.get("automod_phishing", 1) else 1
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "automod_phishing", new_val)
        await self._update_view(interaction)

    @discord.ui.button(label="Anti-Alt Shield", style=discord.ButtonStyle.secondary, emoji="👥", row=2)
    async def btn_alt(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened settings can toggle this.", ephemeral=True)
            return
        new_val = 0 if self.cfg.get("antialt_enabled", 1) else 1
        if self.bot.db:
            await self.bot.db.set_guild_config(self.guild.id, "antialt_enabled", new_val)
        await self._update_view(interaction)

    @discord.ui.button(label="🧙 Setup Wizard", style=discord.ButtonStyle.primary, emoji="✨", row=3)
    async def btn_wizard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the admin who opened settings can launch the wizard.", ephemeral=True)
            return
        wizard_view = MultiStepSetupWizardView(self.bot, self.guild, self.author)
        await interaction.response.send_message(embed=wizard_view.get_step_embed(), view=wizard_view, ephemeral=True)


class Verification(commands.Cog, name="Verification Gatekeeper"):
    """Next-Gen Verification and Server Gatekeeper Cog."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(VerifyButtonView(self.bot, 0))
        log.info("Passkey Verification Cog loaded with persistent views.")

    @commands.hybrid_command(name="setup", aliases=["wizard", "setup-wizard", "config-wizard"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    async def setup_command(self, ctx: commands.Context):
        """Interactive step-by-step Setup Wizard with pagination (◀️ Previous / ▶️ Next)."""
        wizard_view = MultiStepSetupWizardView(self.bot, ctx.guild, ctx.author)
        await ctx.send(embed=wizard_view.get_step_embed(), view=wizard_view)

    @commands.hybrid_command(name="settings", aliases=["config", "panel", "setting"])
    @commands.has_permissions(administrator=True)
    async def settings_command(self, ctx: commands.Context):
        """View and customize all server settings in an interactive 1-click dashboard."""
        cfg = {}
        if self.bot.db:
            cfg = await self.bot.db.get_guild_config(ctx.guild.id)
        
        embed = render_settings_embed(ctx.guild, cfg)
        view = ServerSettingsView(self.bot, ctx.guild, ctx.author, cfg)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="setmode")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(mode="Choose verification mode")
    @app_commands.choices(mode=[
        app_commands.Choice(name="🌐 Web Portal (Cloudflare Turnstile)", value="web"),
        app_commands.Choice(name="📱 Biometric Passkey (Touch ID / Face ID)", value="biometric"),
        app_commands.Choice(name="✉️ Email OTP (Direct Code)", value="email"),
        app_commands.Choice(name="🖼️ In-Discord Image CAPTCHA", value="image_captcha"),
        app_commands.Choice(name="🎮 Emoji Sequence Pattern", value="pattern"),
        app_commands.Choice(name="🔗 Social Connection Check", value="social"),
        app_commands.Choice(name="🔢 Interactive Math CAPTCHA", value="captcha"),
        app_commands.Choice(name="📝 Server Rules Quiz", value="rules"),
        app_commands.Choice(name="⚡ Direct 1-Click Button", value="button"),
    ])
    async def set_mode(self, ctx: commands.Context, mode: str):
        """Change the server verification method (9 modes available)."""
        mode = mode.lower()
        valid_modes = ["web", "biometric", "email", "image_captcha", "pattern", "social", "captcha", "rules", "button"]
        if mode not in valid_modes:
            await ctx.send(f"❌ Invalid mode. Choose from: `{', '.join(valid_modes)}`", ephemeral=True)
            return

        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "verify_mode", mode)

        await ctx.send(f"🛡️ **Verification mode updated to:** `{mode.upper()}`", ephemeral=True)

    @commands.hybrid_command(name="setlog")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel="Text channel to receive security and verification logs")
    async def set_log(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the log channel for verification and security audit logs."""
        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "log_channel_id", str(channel.id))
        await ctx.send(f"📋 **Security log channel set to:** {channel.mention}", ephemeral=True)

    @commands.hybrid_command(name="minage")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(days="Minimum Discord account age in days (0 to disable)")
    async def min_age(self, ctx: commands.Context, days: int):
        """Set minimum Discord account age in days required to verify."""
        if days < 0:
            await ctx.send("❌ Days must be 0 or greater.", ephemeral=True)
            return

        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "min_age_days", days)

        status = f"**{days} days**" if days > 0 else "**Disabled (0 days)**"
        await ctx.send(f"🛡️ **Minimum account age required for verification is now:** {status}", ephemeral=True)

    @commands.hybrid_command(name="setlang", aliases=["language", "setlanguage"])
    @commands.has_permissions(administrator=True)
    @app_commands.describe(lang="Choose system language for verification emails and bot messages")
    @app_commands.choices(lang=[
        app_commands.Choice(name="🇬🇧 English (Default)", value="en"),
        app_commands.Choice(name="🇻🇳 Tiếng Việt (Vietnamese)", value="vi"),
        app_commands.Choice(name="🇯🇵 日本語 (Japanese)", value="ja"),
        app_commands.Choice(name="🇰🇷 한국어 (Korean)", value="ko"),
        app_commands.Choice(name="🇨🇳 简体中文 (Chinese)", value="zh"),
        app_commands.Choice(name="🇪🇸 Español (Spanish)", value="es"),
        app_commands.Choice(name="🇫🇷 Français (French)", value="fr"),
        app_commands.Choice(name="🇩🇪 Deutsch (German)", value="de"),
        app_commands.Choice(name="🇷🇺 Русский (Russian)", value="ru"),
        app_commands.Choice(name="🇧🇷 Português (Portuguese)", value="pt"),
    ])
    async def set_language(self, ctx: commands.Context, lang: str = "en"):
        """Change the server language for verification emails and bot messages (English default)."""
        lang = lang.lower().strip()
        lang_names = {
            "en": "🇬🇧 English (Default)",
            "vi": "🇻🇳 Tiếng Việt",
            "ja": "🇯🇵 日本語",
            "ko": "🇰🇷 한국어",
            "zh": "🇨🇳 简体中文",
            "es": "🇪🇸 Español",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "ru": "🇷🇺 Русский",
            "pt": "🇧🇷 Português"
        }
        if lang not in lang_names:
            await ctx.send(f"❌ Supported languages: {', '.join(lang_names.keys())}", ephemeral=True)
            return

        if self.bot.db:
            await self.bot.db.set_guild_config(ctx.guild.id, "language", lang)

        await ctx.send(f"🌐 **Server language set to:** {lang_names[lang]}", ephemeral=True)

    @commands.hybrid_command(name="verify")
    async def verify_cmd(self, ctx: commands.Context):
        """Request your verification session link or prompt."""
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ This command must be used in a server.", ephemeral=True)
            return

        config = {}
        if self.bot.db:
            config = await self.bot.db.get_guild_config(guild.id)
        
        mode = config.get("verify_mode", "web")
        if mode == "button":
            success, msg = await grant_verified_role(self.bot, guild, ctx.author, method="button")
            await ctx.send(f"✅ {msg}" if success else f"❌ {msg}", ephemeral=True)
            return

        token = f"pk_{secrets.token_hex(16)}"
        VERIFY_SESSIONS[token] = {
            "user_id": ctx.author.id,
            "guild_id": guild.id,
            "created_at": time.time()
        }

        from utils.config import Config
        base_url = Config.DASHBOARD_URL.rstrip("/")
        verify_url = f"{base_url}/verify?session={token}"

        is_email = (mode == "email")
        lang = config.get("language", "en")

        embed = discord.Embed(
            title="🔑 Passkey Verification",
            description=f"Click the link below to complete verification for **{guild.name}**.\n\n⚠️ *You have up to 5 attempts to verify.*",
            color=0x6366F1
        )
        embed.set_footer(text="Passkey Gatekeeper • Zero-Trust Verification Network")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open Verification Portal", url=verify_url, style=discord.ButtonStyle.link, emoji="🌐"))
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="post_verify", aliases=["post-verify", "sendverify", "postverify"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @app_commands.describe(channel="Target channel to send verification embed panel (default: current channel)")
    async def post_verify(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Send the interactive 'Click to Verify' panel into a channel."""
        target_channel = channel or ctx.channel
        guild = ctx.guild

        config = {}
        if self.bot.db:
            config = await self.bot.db.get_guild_config(guild.id)

        mode = config.get("verify_mode", "web")
        lang = config.get("language", "en")

        embed = discord.Embed(
            title="🔑 Passkey Server Gatekeeper",
            description=(
                f"Welcome to **{guild.name}**!\n\n"
                "To prevent automated raid bots and maintain community safety, "
                "please click the **Click to Verify** button below to complete verification.\n\n"
                f"• **Verification Method**: `{mode.upper()}`\n"
                f"• **Language**: `{lang.upper()}`\n"
                "• **Instant Access**: Unlocks full access to all member channels immediately."
            ),
            color=0x6366F1
        )
        embed.set_footer(text="Protected by Passkey Zero-Trust Gatekeeper")
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        view = VerifyButtonView(self.bot, guild.id)
        try:
            await target_channel.send(embed=embed, view=view)
            if self.bot.db:
                await self.bot.db.set_guild_config(guild.id, "verify_channel_id", str(target_channel.id))
            await ctx.send(f"✅ **Verification panel successfully posted into** {target_channel.mention}!", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Failed to send embed to {target_channel.mention}: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Verification(bot))
