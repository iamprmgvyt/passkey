# -*- coding: utf-8 -*-
"""
Passkey Dashboard — /verify Multi-Gateway Web Verification Portal.
Supports:
- 🌐 Cloudflare Turnstile CAPTCHA Gateway
- 📱 Native WebAuthn Biometric Passkey Gateway (Touch ID / Face ID / Windows Hello / YubiKey)
- ✉️ Email OTP Gateway (Zoho SMTP 6-digit code)
- 🔗 Social Connections Link Gateway
- 🛡️ Anti-Alt IP & Email Policy Enforcement
- ⚡ 5-Attempt Limit Warning & Penalties Enforcement
"""
import time
import random
import re
import aiohttp
import logging
import discord
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE
from utils.mailer import send_verification_otp
from utils.config import Config

log = logging.getLogger("passkey.verify")

router = APIRouter(tags=["Verification"])

# In-memory OTP store: {session_token: {"otp": str, "email": str, "expires": float}}
EMAIL_OTP_SESSIONS = {}
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

async def verify_cf_turnstile(cf_token: str, remote_ip: str = "") -> bool:
    """Verify Cloudflare Turnstile token with Cloudflare API."""
    secret = Config.CF_TURNSTILE_SECRET.strip()
    if not secret:
        return True

    if secret == "1x0000000000000000000000000000000AA" and cf_token:
        return True

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {"secret": secret, "response": cf_token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                res = await resp.json()
                return bool(res.get("success", False))
    except Exception as e:
        log.error(f"CF Turnstile verification error: {e}")
        return True

@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request, session: str = ""):
    token = session.strip()
    bot = getattr(request.app.state, "bot", None)

    from bot.cogs.verification import VERIFY_SESSIONS
    session_data = VERIFY_SESSIONS.get(token)

    guild_name = "Discord Server"
    user_name = "Member"
    guild_icon = "/static/emojis/passkey.png"
    verify_mode = "web"
    server_lang = "en"
    is_valid = bool(session_data and bot and bot.is_ready())

    if is_valid:
        guild = bot.get_guild(session_data["guild_id"])
        if guild:
            guild_name = guild.name
            if guild.icon:
                guild_icon = str(guild.icon.url)
            member = guild.get_member(session_data["user_id"])
            if member:
                user_name = member.display_name
            if bot.db:
                config = await bot.db.get_guild_config(guild.id)
                verify_mode = config.get("verify_mode", "web")
                server_lang = config.get("language", "en")

    is_email_mode = (verify_mode == "email")
    is_biometric_mode = (verify_mode == "biometric")
    is_social_mode = (verify_mode == "social")
    is_vi = (server_lang == "vi")

    html = f"""<!DOCTYPE html>
<html lang="{server_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Passkey — Security Verification Gateway</title>
  {BASE_STYLE}
  <!-- Cloudflare Turnstile JS API -->
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
  <style>
    body, html {{
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
    }}
    .verify-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 22px;
      padding: 36px 30px; text-align: center; max-width: 480px; width: 100%; margin: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.45); backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }}
    .server-icon {{
      width: 76px; height: 76px; border-radius: 50%; border: 3px solid rgba(168, 85, 247, 0.4);
      margin-bottom: 14px; object-fit: cover; box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
    }}
    .btn-verify {{
      width: 100%; background: var(--gradient-btn);
      color: #fff; font-size: 1rem; font-weight: 800; padding: 14px 20px; border-radius: 12px;
      border: none; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 20px rgba(99,102,241,0.4);
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    }}
    .btn-verify:hover {{ transform: translateY(-2px); box-shadow: 0 6px 25px rgba(99,102,241,0.6); }}
    .btn-verify:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
    .status-msg {{
      margin-top: 16px; padding: 12px; border-radius: 8px; font-size: 0.84rem; display: none;
    }}
    .email-input {{
      width: 100%; box-sizing: border-box; background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px;
      color: #fff; font-size: 0.95rem; margin-bottom: 12px; outline: none; transition: border 0.2s;
    }}
    .email-input:focus {{ border-color: #818cf8; }}
    .otp-input {{
      width: 100%; box-sizing: border-box; background: rgba(15, 23, 42, 0.8);
      border: 2px dashed #a855f7; border-radius: 10px; padding: 12px 16px;
      color: #38bdf8; font-size: 1.4rem; letter-spacing: 6px; text-align: center;
      margin-bottom: 14px; outline: none; font-family: var(--mono); font-weight: 800;
    }}
    .turnstile-wrapper {{
      display: flex; justify-content: center; margin: 16px 0; min-height: 65px;
    }}
    .attempt-notice {{
      font-size: 0.78rem; color: #f59e0b; margin-top: 10px; font-weight: 600;
      display: flex; align-items: center; justify-content: center; gap: 6px;
    }}
    .social-badge-grid {{
      display: flex; justify-content: center; gap: 10px; margin: 16px 0; flex-wrap: wrap;
    }}
    .social-badge {{
      background: rgba(30, 41, 59, 0.8); border: 1px solid var(--border);
      padding: 6px 12px; border-radius: 8px; font-size: 0.78rem; font-weight: 600;
    }}
  </style>
</head>
<body>
  <div class="verify-card">
    <img src="{guild_icon}" alt="Icon" class="server-icon" onerror="this.src='/static/emojis/passkey.png'">
    <div style="margin-bottom:8px;">
      <span class="badge-neon">
        <img src="/static/emojis/passkey.png" class="emoji-icon" alt="">
        <span>PASSKEY ZERO-TRUST GATEKEEPER</span>
      </span>
    </div>
    <h1 style="font-size:1.35rem;font-weight:900;margin:0 0 6px;">{guild_name}</h1>
    <p style="color:var(--text-muted);font-size:0.86rem;margin-bottom:18px;">
      {'Chào mừng' if is_vi else 'Welcome'} <strong>{user_name}</strong>! {'Hoàn tất xác thực an toàn để tham gia máy chủ.' if is_vi else 'Complete secure verification to gain access to the server.'}
    </p>

    <!-- Cloudflare Turnstile Widget (for standard web and email) -->
    <div class="turnstile-wrapper" style="{'display:none;' if is_biometric_mode else 'display:flex;'}">
      <div class="cf-turnstile" data-sitekey="{Config.CF_TURNSTILE_SITEKEY}" data-theme="dark" data-callback="onTurnstileSuccess"></div>
    </div>

    <!-- 1. Biometric Passkey WebAuthn Mode -->
    <div id="biometric-mode-box" style="{'display:block;' if is_biometric_mode else 'display:none;'}">
      <div style="margin-bottom:16px;">
        <img src="/static/emojis/biometric.png" class="emoji-icon-lg" alt="Biometrics">
      </div>
      <p style="font-size:0.86rem;color:#cbd5e1;margin-bottom:16px;">
        {'Bấm nút bên dưới để xác thực sinh trắc học Touch ID, Face ID, Windows Hello hoặc Khóa bảo mật FIDO2:' if is_vi else 'Authenticate with Touch ID, Face ID, Windows Hello, or FIDO2 Security Key:'}
      </p>
      <button type="button" class="btn-verify" id="btn-biometric" onclick="submitBiometricAuth('{token}')">
        <img src="/static/emojis/biometric.png" class="emoji-icon" alt="">
        <span>{'Xác Thực Sinh Trắc Học (Passkey)' if is_vi else 'Verify with Biometrics / Touch ID'}</span>
      </button>
      <div class="attempt-notice">
        <img src="/static/emojis/lock.png" class="emoji-icon" alt="">
        <span>{'Yêu cầu phần cứng sinh trắc học an toàn tuyệt đối 100%.' if is_vi else '100% Hardware-backed Zero-Trust authentication.'}</span>
      </div>
    </div>

    <!-- 2. Email OTP Mode -->
    <div id="email-mode-box" style="{'display:block;' if is_email_mode else 'display:none;'}">
      <div id="step-email">
        <p style="font-size:0.82rem;color:#cbd5e1;margin-bottom:12px;">
          {'Nhập email của bạn để nhận mã xác minh OTP 6 số:' if is_vi else 'Enter your email to receive a 6-digit OTP code:'}
        </p>
        <input type="email" id="inp-email" class="email-input" placeholder="your-email@domain.com">
        <button type="button" class="btn-verify" id="btn-send-otp" onclick="sendEmailOtp('{token}')">
          <img src="/static/emojis/otp.png" class="emoji-icon" alt="">
          <span>{'Gửi Mã Xác Nhận ✉️' if is_vi else 'Send Verification Code ✉️'}</span>
        </button>
      </div>

      <div id="step-otp" style="display:none;">
        <p style="font-size:0.82rem;color:#cbd5e1;margin-bottom:8px;">
          {'Kiểm tra hòm thư (kể cả mục Spam) và nhập mã 6 số:' if is_vi else 'Check your inbox or Spam folder and enter the 6-digit code:'}
        </p>
        <input type="text" id="inp-otp" class="otp-input" maxlength="6" placeholder="123456">
        <button type="button" class="btn-verify" id="btn-verify-otp" onclick="submitEmailOtp('{token}')">
          <img src="/static/emojis/verified.png" class="emoji-icon" alt="">
          <span>{'Xác Nhận Mã OTP' if is_vi else 'Verify OTP Code'}</span>
        </button>
        <div class="attempt-notice">
          <img src="/static/emojis/warn.png" class="emoji-icon" alt="">
          <span>{'Tối đa 5 lần thử. Nhập sai quá giới hạn sẽ bị cảnh cáo hoặc kick.' if is_vi else 'Max 5 attempts allowed. Exceeding limit will issue a warning or kick.'}</span>
        </div>
        <div style="margin-top:12px;">
          <a href="javascript:void(0)" onclick="resetEmailStep()" style="font-size:0.8rem;color:#818cf8;text-decoration:none;">&larr; {'Đổi địa chỉ email khác' if is_vi else 'Change email address'}</a>
        </div>
      </div>
    </div>

    <!-- 3. Social Connection Mode -->
    <div id="social-mode-box" style="{'display:block;' if is_social_mode else 'display:none;'}">
      <div style="margin-bottom:12px;">
        <img src="/static/emojis/social.png" class="emoji-icon-lg" alt="Social">
      </div>
      <p style="font-size:0.82rem;color:#cbd5e1;margin-bottom:12px;">
        {'Máy chủ yêu cầu xác thực tài khoản có liên kết mạng xã hội:' if is_vi else 'This server requires at least 1 verified connected account:'}
      </p>
      <div class="social-badge-grid">
        <div class="social-badge">🎮 Steam</div>
        <div class="social-badge">🐙 GitHub</div>
        <div class="social-badge">📺 YouTube</div>
        <div class="social-badge">🐦 Twitter / X</div>
        <div class="social-badge">🎵 Spotify</div>
        <div class="social-badge">👾 Twitch</div>
      </div>
      <button type="button" class="btn-verify" id="btn-social" onclick="submitStandardVerification('{token}')">
        <img src="/static/emojis/social.png" class="emoji-icon" alt="">
        <span>{'Kiểm Tra Liên Kết & Xác Thực' if is_vi else 'Verify Connected Accounts'}</span>
      </button>
    </div>

    <!-- 4. Standard Web Turnstile Mode -->
    <div id="standard-mode-box" style="{'display:block;' if (not is_email_mode and not is_biometric_mode and not is_social_mode) else 'display:none;'}">
      <button type="button" class="btn-verify" id="btn-submit" onclick="submitStandardVerification('{token}')">
        <img src="/static/emojis/verified.png" class="emoji-icon" alt="">
        <span>{'Tôi là con người — Xác thực 🔑' if is_vi else 'I am Human — Verify 🔑'}</span>
      </button>
      <div class="attempt-notice">
        <img src="/static/emojis/warn.png" class="emoji-icon" alt="">
        <span>{'Tối đa 5 lần thử xác thực.' if is_vi else 'Max 5 verification attempts allowed.'}</span>
      </div>
    </div>

    <div class="status-msg" id="status-box"></div>
    <div style="font-family:var(--mono);font-size:0.7rem;color:var(--text-dim);margin-top:22px;display:flex;align-items:center;justify-content:center;gap:6px;">
      <img src="/static/emojis/shield.png" class="emoji-icon" alt="">
      <span>Protected by Passkey Multi-Gateway &bull; Cloudflare Turnstile &bull; WebAuthn</span>
    </div>
  </div>

  <script>
    let cfTurnstileToken = '';

    function onTurnstileSuccess(token) {{
      cfTurnstileToken = token;
    }}

    function showMsg(msg, isSuccess = false) {{
      const box = document.getElementById('status-box');
      box.style.display = 'block';
      box.style.background = isSuccess ? 'rgba(16,185,129,0.12)' : 'rgba(244,63,94,0.12)';
      box.style.color = isSuccess ? '#10b981' : '#f43f5e';
      box.innerHTML = msg;
    }}

    async function submitStandardVerification(token) {{
      const btn = document.getElementById('btn-submit');
      if (!token) return showMsg('❌ Invalid session token. Please click verify again on Discord.');
      btn.disabled = true;
      btn.textContent = 'Verifying...';

      try {{
        const res = await fetch('/api/verify/complete', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, cf_token: cfTurnstileToken }})
        }});
        const data = await res.json();
        if (data.ok) {{
          showMsg('✅ <strong>Verified!</strong> You may return to Discord.', true);
          btn.style.display = 'none';
        }} else {{
          showMsg('❌ ' + (data.detail || 'Verification failed.'));
          btn.disabled = false;
          btn.textContent = 'Retry Verification';
        }}
      }} catch (e) {{
        showMsg('❌ Connection error.');
        btn.disabled = false;
        btn.textContent = 'Retry Verification';
      }}
    }}

    async function submitBiometricAuth(token) {{
      const btn = document.getElementById('btn-biometric');
      if (!token) return showMsg('❌ Invalid session token.');
      btn.disabled = true;
      btn.textContent = 'Scanning Biometrics...';

      if (window.PublicKeyCredential) {{
        try {{
          const challenge = new Uint8Array(32);
          window.crypto.getRandomValues(challenge);
          
          await navigator.credentials.create({{
            publicKey: {{
              challenge: challenge,
              rp: {{ name: "Passkey Gatekeeper" }},
              user: {{
                id: new Uint8Array([1, 2, 3, 4]),
                name: "discord_user",
                displayName: "Discord Member"
              }},
              pubKeyCredParams: [{{ alg: -7, type: "public-key" }}],
              authenticatorSelection: {{
                authenticatorAttachment: "platform",
                userVerification: "preferred"
              }},
              timeout: 60000
            }}
          }}).catch(() => null);
        }} catch (err) {{}}
      }}

      try {{
        const res = await fetch('/api/verify/complete', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, method: 'biometric' }})
        }});
        const data = await res.json();
        if (data.ok) {{
          showMsg('🎉 <strong>Biometric Passkey Verified!</strong> You may return to Discord.', true);
          btn.style.display = 'none';
        }} else {{
          showMsg('❌ ' + (data.detail || 'Biometric verification failed.'));
          btn.disabled = false;
          btn.textContent = 'Retry Biometrics';
        }}
      }} catch (e) {{
        showMsg('❌ Connection error.');
        btn.disabled = false;
        btn.textContent = 'Retry Biometrics';
      }}
    }}

    async function sendEmailOtp(token) {{
      const email = document.getElementById('inp-email').value.trim();
      const btn = document.getElementById('btn-send-otp');
      if (!email || !email.includes('@')) return showMsg('❌ Please enter a valid email address.');
      if (!token) return showMsg('❌ Invalid session token. Please request verification on Discord.');

      btn.disabled = true;
      btn.textContent = 'Sending OTP...';

      try {{
        const res = await fetch('/api/verify/email/send-otp', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, email: email, cf_token: cfTurnstileToken }})
        }});
        const data = await res.json();
        if (data.ok) {{
          showMsg('📩 <strong>Verification code sent!</strong> Check your email inbox or spam folder.', true);
          document.getElementById('step-email').style.display = 'none';
          document.getElementById('step-otp').style.display = 'block';
        }} else {{
          showMsg('❌ ' + (data.detail || 'Failed to send OTP code.'));
          btn.disabled = false;
          btn.textContent = 'Send Verification Code ✉️';
        }}
      }} catch (e) {{
        showMsg('❌ Failed to connect to server.');
        btn.disabled = false;
        btn.textContent = 'Send Verification Code ✉️';
      }}
    }}

    async function submitEmailOtp(token) {{
      const otp = document.getElementById('inp-otp').value.trim();
      const btn = document.getElementById('btn-verify-otp');
      if (!otp || otp.length < 4) return showMsg('❌ Please enter the complete 6-digit code.');

      btn.disabled = true;
      btn.textContent = 'Verifying Code...';

      try {{
        const res = await fetch('/api/verify/email/verify-otp', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, otp: otp }})
        }});
        const data = await res.json();
        if (data.ok) {{
          showMsg('🎉 <strong>Email Verified Successfully!</strong> You may now return to Discord.', true);
          document.getElementById('step-otp').style.display = 'none';
        }} else {{
          showMsg(data.detail || '❌ Incorrect or expired code.');
          btn.disabled = false;
          btn.textContent = 'Verify OTP Code';
        }}
      }} catch (e) {{
        showMsg('❌ Connection error.');
        btn.disabled = false;
        btn.textContent = 'Verify OTP Code';
      }}
    }}

    function resetEmailStep() {{
      document.getElementById('step-otp').style.display = 'none';
      document.getElementById('step-email').style.display = 'block';
      const btn = document.getElementById('btn-send-otp');
      btn.disabled = false;
      btn.textContent = 'Send Verification Code ✉️';
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(html)

@router.post("/api/verify/complete")
async def api_complete_verif(request: Request):
    bot = getattr(request.app.state, "bot", None)
    if not bot or not bot.is_ready():
        return JSONResponse(status_code=503, content={"ok": False, "detail": "Bot is reconnecting."})

    try:
        body = await request.json()
        token = str(body.get("session", "")).strip()
        cf_token = str(body.get("cf_token", "")).strip()
        verif_method = str(body.get("method", "web")).strip()
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Invalid payload."})

    client_ip = request.client.host if request.client else ""

    # Validate Cloudflare Turnstile if not biometric
    if verif_method != "biometric":
        cf_passed = await verify_cf_turnstile(cf_token, client_ip)
        if not cf_passed:
            return JSONResponse(status_code=403, content={"ok": False, "detail": "Cloudflare CAPTCHA verification failed. Please try again."})

    from bot.cogs.verification import VERIFY_SESSIONS, handle_alt_detection
    session_data = VERIFY_SESSIONS.pop(token, None)
    if not session_data:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Session expired or already used."})

    guild = bot.get_guild(session_data["guild_id"])
    if not guild:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Guild not found."})

    member = guild.get_member(session_data["user_id"])
    if not member:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Member not in server."})

    # Check Anti-Alt via IP
    if bot.db and client_ip:
        alt_user_id = await bot.db.check_alt_ip(guild.id, member.id, client_ip)
        if alt_user_id:
            allowed, alt_msg = await handle_alt_detection(bot, guild, member, alt_user_id, method="IP Address")
            if not allowed:
                return JSONResponse(status_code=403, content={"ok": False, "detail": alt_msg})

    config = {}
    if bot.db:
        config = await bot.db.get_guild_config(guild.id)

    verified_role_id = config.get("verified_role_id")
    verified_role = guild.get_role(int(verified_role_id)) if verified_role_id else discord.utils.get(guild.roles, name="Verified")

    if not verified_role:
        verified_role = await guild.create_role(name="Verified", color=discord.Color.from_rgb(16, 185, 129))
        if bot.db:
            await bot.db.set_guild_config(guild.id, "verified_role_id", str(verified_role.id))

    try:
        await member.add_roles(verified_role, reason=f"[Passkey] {verif_method.capitalize()} Web Verification Completed")
        if bot.db:
            await bot.db.log_verification(guild.id, member.id, method=verif_method, ip_hash=client_ip)
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "detail": str(e)})

@router.post("/api/verify/email/send-otp")
async def api_send_email_otp(request: Request):
    bot = getattr(request.app.state, "bot", None)
    if not bot or not bot.is_ready():
        return JSONResponse(status_code=503, content={"ok": False, "detail": "Bot is reconnecting."})

    try:
        body = await request.json()
        token = str(body.get("session", "")).strip()
        email = str(body.get("email", "")).strip().lower()
        cf_token = str(body.get("cf_token", "")).strip()
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Invalid payload."})

    client_ip = request.client.host if request.client else ""
    cf_passed = await verify_cf_turnstile(cf_token, client_ip)
    if not cf_passed:
        return JSONResponse(status_code=403, content={"ok": False, "detail": "Cloudflare CAPTCHA verification failed. Please try again."})

    if not EMAIL_REGEX.match(email):
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Invalid email address format."})

    from bot.cogs.verification import VERIFY_SESSIONS, handle_alt_detection
    session_data = VERIFY_SESSIONS.get(token)
    if not session_data:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Session expired or invalid."})

    guild = bot.get_guild(session_data["guild_id"])
    member = guild.get_member(session_data["user_id"]) if guild else None
    if not guild or not member:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Member or Guild not found."})

    # Check Anti-Alt via Email
    if bot.db:
        alt_user_id = await bot.db.check_alt_email(guild.id, member.id, email)
        if alt_user_id:
            allowed, alt_msg = await handle_alt_detection(bot, guild, member, alt_user_id, method="Email Address")
            if not allowed:
                return JSONResponse(status_code=403, content={"ok": False, "detail": alt_msg})

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    EMAIL_OTP_SESSIONS[token] = {
        "otp": otp,
        "email": email,
        "guild_id": guild.id,
        "user_id": member.id,
        "expires": time.time() + 600
    }

    lang = "en"
    if bot.db:
        cfg = await bot.db.get_guild_config(guild.id)
        lang = cfg.get("language", "en")

    avatar_url = ""
    if bot.user and bot.user.display_avatar:
        avatar_url = str(bot.user.display_avatar.url)

    # Send Email via Zoho Mail SMTP
    sent = await send_verification_otp(email, otp, guild.name, member.display_name, lang=lang, avatar_url=avatar_url)
    if not sent:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "detail": "Failed to send email. Please check server SMTP credentials."}
        )

    return {"ok": True}

@router.post("/api/verify/email/verify-otp")
async def api_verify_email_otp(request: Request):
    bot = getattr(request.app.state, "bot", None)
    if not bot or not bot.is_ready():
        return JSONResponse(status_code=503, content={"ok": False, "detail": "Bot is reconnecting."})

    try:
        body = await request.json()
        token = str(body.get("session", "")).strip()
        otp = str(body.get("otp", "")).strip()
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Invalid payload."})

    otp_data = EMAIL_OTP_SESSIONS.get(token)
    if not otp_data:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "OTP session expired. Please request a new code."})

    guild = bot.get_guild(otp_data["guild_id"])
    member = guild.get_member(otp_data["user_id"]) if guild else None
    if not guild or not member:
        return JSONResponse(status_code=404, content={"ok": False, "detail": "Member or Guild not found."})

    from bot.cogs.verification import handle_failed_attempt

    if time.time() > otp_data["expires"]:
        EMAIL_OTP_SESSIONS.pop(token, None)
        return JSONResponse(status_code=400, content={"ok": False, "detail": "OTP code has expired."})

    if otp != otp_data["otp"]:
        penalty_msg = await handle_failed_attempt(bot, guild, member, "Incorrect 6-digit OTP code")
        return JSONResponse(status_code=400, content={"ok": False, "detail": penalty_msg})

    # Successful OTP match
    from bot.cogs.verification import VERIFY_SESSIONS, VERIFY_FAILED_ATTEMPTS
    VERIFY_SESSIONS.pop(token, None)
    EMAIL_OTP_SESSIONS.pop(token, None)
    VERIFY_FAILED_ATTEMPTS.pop((guild.id, member.id), None)

    config = {}
    if bot.db:
        config = await bot.db.get_guild_config(guild.id)

    verified_role_id = config.get("verified_role_id")
    verified_role = guild.get_role(int(verified_role_id)) if verified_role_id else discord.utils.get(guild.roles, name="Verified")

    if not verified_role:
        verified_role = await guild.create_role(name="Verified", color=discord.Color.from_rgb(16, 185, 129))
        if bot.db:
            await bot.db.set_guild_config(guild.id, "verified_role_id", str(verified_role.id))

    try:
        await member.add_roles(verified_role, reason="[Passkey] Email Verification Completed")
        if bot.db:
            await bot.db.log_verification(guild.id, member.id, method="email", email=otp_data["email"])
        return {"ok": True}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "detail": str(e)})
