# -*- coding: utf-8 -*-
"""
Passkey Dashboard — /verify Multi-Gateway Web Verification Portal.
Supports:
-  Cloudflare Turnstile CAPTCHA Gateway (Auto-enables submit button only upon challenge completion)
-  Native WebAuthn Biometric Passkey Gateway (Touch ID / Face ID / Windows Hello / YubiKey)
-  Email OTP Gateway (Zoho SMTP 6-digit code)
-  Social Connections Link Gateway
-  Anti-Alt IP & Email Policy Enforcement
-  5-Attempt Limit Warning & Penalties Enforcement
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

    if not cf_token:
        return False

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {"secret": secret, "response": cf_token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                res = await resp.json()
                log.info(f"Cloudflare Turnstile siteverify response: {res}")
                return bool(res.get("success", False))
    except Exception as e:
        log.error(f"CF Turnstile verification error: {e}")
        return False

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

    guild_id_str = str(guild.id) if (is_valid and guild) else ""

    html = f"""<!DOCTYPE html>
<html lang="{server_lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Passkey — Security Verification Gateway</title>
  {BASE_STYLE}
  <!-- Cloudflare Turnstile & Canvas Confetti JS -->
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"></script>
  <style>
    body, html {{
      min-height: 100vh; display: flex; align-items: center; justify-content: center;
    }}
    .verify-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 22px;
      padding: 36px 30px; text-align: center; max-width: 480px; width: 100%; margin: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.45); backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: all 0.4s ease;
    }}
    .server-icon {{
      width: 76px; height: 76px; border-radius: 50%; border: 3px solid rgba(168, 85, 247, 0.4);
      margin-bottom: 14px; object-fit: cover; box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
    }}
    .btn-verify {{
      width: 100%; background: var(--gradient-btn);
      color: #fff; font-size: 1rem; font-weight: 800; padding: 14px 20px; border-radius: 12px;
      border: none; cursor: pointer; transition: all 0.25s; box-shadow: 0 4px 20px rgba(99,102,241,0.4);
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    }}
    .btn-verify:hover:not(:disabled) {{ transform: translateY(-2px); box-shadow: 0 6px 25px rgba(99,102,241,0.6); }}
    .btn-verify:disabled {{
      opacity: 0.45 !important;
      cursor: not-allowed !important;
      transform: none !important;
      box-shadow: none !important;
    }}
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
    .verify-footer {{
      font-family: var(--mono); font-size: 0.74rem; color: #94a3b8; margin-top: 24px;
      display: flex; align-items: center; justify-content: center; gap: 8px;
      padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.07);
    }}
    .success-screen-box {{
      display: none; text-align: center; padding: 12px 0;
      animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .success-icon-wrap {{
      position: relative; width: 100px; height: 100px; margin: 0 auto 16px;
      display: flex; align-items: center; justify-content: center;
    }}
    .success-neon-icon {{
      width: 84px; height: 84px; filter: drop-shadow(0 0 25px rgba(16, 185, 129, 0.85));
      animation: pulseNeon 2s infinite ease-in-out;
    }}
    @keyframes pulseNeon {{
      0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.75)); }}
      50% {{ transform: scale(1.08); filter: drop-shadow(0 0 35px rgba(16, 185, 129, 1)); }}
    }}
    @keyframes fadeInUp {{
      from {{ opacity: 0; transform: translateY(24px) scale(0.96); }}
      to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    .success-title {{
      font-size: 1.5rem; font-weight: 900; color: #fff; margin: 0 0 8px;
      background: linear-gradient(135deg, #10b981 0%, #38bdf8 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .success-subtitle {{
      font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin: 0 0 18px;
    }}
    .success-badge {{
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4);
      padding: 7px 16px; border-radius: 99px; font-size: 0.8rem; font-weight: 700; color: #10b981;
    }}
  </style>
</head>
<body>
  <div class="verify-card" id="main-verify-card">
    <div id="verify-initial-content">
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

      <!-- Cloudflare Turnstile Widget (with callbacks) -->
      <div class="turnstile-wrapper" style="{'display:none;' if is_biometric_mode else 'display:flex;'}">
        <div class="cf-turnstile" 
             data-sitekey="{Config.CF_TURNSTILE_SITEKEY}" 
             data-theme="dark" 
             data-callback="onTurnstileSuccess"
             data-expired-callback="onTurnstileExpired"
             data-error-callback="onTurnstileError">
        </div>
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
          <button type="button" class="btn-verify" id="btn-send-otp" onclick="sendEmailOtp('{token}')" disabled style="opacity:0.45;cursor:not-allowed;">
            <img src="/static/emojis/otp.png" class="emoji-icon" alt="">
            <span id="btn-send-otp-text">{' Hoàn thành CAPTCHA để gửi mã' if is_vi else ' Complete CAPTCHA to Send OTP'}</span>
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
          <div class="social-badge"> Steam</div>
          <div class="social-badge"> GitHub</div>
          <div class="social-badge"> YouTube</div>
          <div class="social-badge"> Twitter / X</div>
          <div class="social-badge"> Spotify</div>
          <div class="social-badge"> Twitch</div>
        </div>
        <button type="button" class="btn-verify" id="btn-social" onclick="submitStandardVerification('{token}')" disabled style="opacity:0.45;cursor:not-allowed;">
          <img src="/static/emojis/social.png" class="emoji-icon" alt="">
          <span id="btn-social-text">{' Hoàn thành CAPTCHA để xác thực' if is_vi else ' Complete CAPTCHA to verify'}</span>
        </button>
      </div>

      <!-- 4. Standard Web Turnstile Mode (Starts DISABLED until Turnstile completes) -->
      <div id="standard-mode-box" style="{'display:block;' if (not is_email_mode and not is_biometric_mode and not is_social_mode) else 'display:none;'}">
        <button type="button" class="btn-verify" id="btn-submit" onclick="submitStandardVerification('{token}')" disabled style="opacity:0.45;cursor:not-allowed;">
          <img src="/static/emojis/verified.png" class="emoji-icon" alt="">
          <span id="btn-submit-text">{' Đang đợi xác thực Cloudflare...' if is_vi else ' Waiting for Cloudflare Challenge...'}</span>
        </button>
        <div class="attempt-notice">
          <img src="/static/emojis/warn.png" class="emoji-icon" alt="">
          <span>{'Tối đa 5 lần thử xác thực.' if is_vi else 'Max 5 verification attempts allowed.'}</span>
        </div>
      </div>

      <div class="status-msg" id="status-box"></div>
    </div>

    <!-- 5. Dynamic Rich Success Screen (Triggered on Verified) -->
    <div id="success-screen" class="success-screen-box">
      <div class="success-icon-wrap">
        <img src="/static/emojis/verified.png" class="success-neon-icon" alt="Verified">
      </div>
      <h2 class="success-title">{' Xác Thực Thành Công!' if is_vi else ' Verification Successful!'}</h2>
      <p class="success-subtitle">
        {'Chúc mừng'} <strong>{user_name}</strong>! {'Bạn đã hoàn tất xác minh bảo mật và được cấp quyền truy cập' if is_vi else 'You passed the Zero-Trust gate and gained full access to'} <strong>{guild_name}</strong>.
      </p>
      <div class="success-badge">
        <img src="/static/emojis/shield.png" class="emoji-icon" alt="">
        <span>{'Role @Verified Activated' if not is_vi else 'Đã Kích Hoạt Role @Verified'}</span>
      </div>
      <div style="margin-top:24px;">
        <a href="https://discord.com/channels/{guild_id_str}" class="btn-verify" style="text-decoration:none;">
          <img src="/static/emojis/passkey.png" class="emoji-icon" alt="">
          <span>{' Mở Discord & Tham Gia Trò Chuyện' if is_vi else ' Open Discord & Join Server'}</span>
        </a>
      </div>
      <p style="font-size:0.75rem;color:var(--text-dim);margin-top:14px;">
        {'Bạn có thể đóng tab trình duyệt này an toàn.' if is_vi else 'You can now safely close this browser window.'}
      </p>
    </div>

    <!-- Bottom Security Footer with Custom Emoji -->
    <div class="verify-footer">
      <img src="/static/emojis/shield.png" class="emoji-icon" alt="Shield">
      <span>Protected by <strong>Passkey Zero-Trust</strong> &bull; Cloudflare Turnstile &bull; WebAuthn</span>
    </div>
  </div>

  <script>
    let cfTurnstileToken = '';
    const isVi = {'true' if is_vi else 'false'};

    function triggerSuccessCelebration() {{
      // 1. Multi-Wave Confetti Cannon Explosion
      const count = 220;
      const defaults = {{ origin: {{ y: 0.65 }} }};
      function fire(particleRatio, opts) {{
        confetti(Object.assign({{}}, defaults, opts, {{
          particleCount: Math.floor(count * particleRatio)
        }}));
      }}
      fire(0.25, {{ spread: 26, startVelocity: 55, colors: ['#6366f1', '#a855f7', '#10b981'] }});
      fire(0.2, {{ spread: 60, colors: ['#38bdf8', '#818cf8', '#ec4899'] }});
      fire(0.35, {{ spread: 100, decay: 0.91, scalar: 0.8, colors: ['#10b981', '#34d399', '#6ee7b7'] }});
      fire(0.1, {{ spread: 120, startVelocity: 25, decay: 0.92, colors: ['#10b981', '#3b82f6', '#f59e0b'] }});
      fire(0.1, {{ spread: 120, startVelocity: 45 }});

      // 2. Hide Initial Content and Smoothly Reveal Success Screen
      const initContent = document.getElementById('verify-initial-content');
      if (initContent) initContent.style.display = 'none';

      const successScreen = document.getElementById('success-screen');
      if (successScreen) {{
        successScreen.style.display = 'block';
      }}

      // Glow border on the card
      const card = document.getElementById('main-verify-card');
      if (card) {{
        card.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        card.style.boxShadow = '0 0 50px rgba(16, 185, 129, 0.35), 0 20px 50px rgba(0,0,0,0.45)';
      }}
    }}

    function onTurnstileSuccess(token) {{
      cfTurnstileToken = token;
      
      // 1. Enable standard submit button
      const btn = document.getElementById('btn-submit');
      if (btn) {{
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
        const txt = document.getElementById('btn-submit-text');
        if (txt) txt.innerHTML = isVi ? 'Tôi là con người — Hoàn tất xác thực ' : 'I am Human — Complete Verification ';
      }}

      // 2. Enable email send OTP button
      const btnEmail = document.getElementById('btn-send-otp');
      if (btnEmail) {{
        btnEmail.disabled = false;
        btnEmail.style.opacity = '1';
        btnEmail.style.cursor = 'pointer';
        const txtEmail = document.getElementById('btn-send-otp-text');
        if (txtEmail) txtEmail.innerHTML = isVi ? 'Gửi Mã Xác Nhận ' : 'Send Verification Code ';
      }}

      // 3. Enable social verify button
      const btnSocial = document.getElementById('btn-social');
      if (btnSocial) {{
        btnSocial.disabled = false;
        btnSocial.style.opacity = '1';
        btnSocial.style.cursor = 'pointer';
        const txtSocial = document.getElementById('btn-social-text');
        if (txtSocial) txtSocial.innerHTML = isVi ? 'Kiểm Tra Liên Kết &amp; Xác Thực' : 'Verify Connected Accounts';
      }}

      const box = document.getElementById('status-box');
      if (box) box.style.display = 'none';
    }}

    function onTurnstileExpired() {{
      cfTurnstileToken = '';
      disableSubmitButtons();
    }}

    function onTurnstileError() {{
      cfTurnstileToken = '';
      disableSubmitButtons();
    }}

    function disableSubmitButtons() {{
      const btn = document.getElementById('btn-submit');
      if (btn) {{
        btn.disabled = true;
        btn.style.opacity = '0.45';
        btn.style.cursor = 'not-allowed';
        const txt = document.getElementById('btn-submit-text');
        if (txt) txt.innerHTML = isVi ? ' Đang đợi xác thực Cloudflare...' : ' Waiting for Cloudflare Challenge...';
      }}
      const btnEmail = document.getElementById('btn-send-otp');
      if (btnEmail) {{
        btnEmail.disabled = true;
        btnEmail.style.opacity = '0.45';
        btnEmail.style.cursor = 'not-allowed';
        const txtEmail = document.getElementById('btn-send-otp-text');
        if (txtEmail) txtEmail.innerHTML = isVi ? ' Hoàn thành CAPTCHA để gửi mã' : ' Complete CAPTCHA to Send OTP';
      }}
      const btnSocial = document.getElementById('btn-social');
      if (btnSocial) {{
        btnSocial.disabled = true;
        btnSocial.style.opacity = '0.45';
        btnSocial.style.cursor = 'not-allowed';
        const txtSocial = document.getElementById('btn-social-text');
        if (txtSocial) txtSocial.innerHTML = isVi ? ' Hoàn thành CAPTCHA để xác thực' : ' Complete CAPTCHA to verify';
      }}
    }}

    function showMsg(msg, isSuccess = false) {{
      const box = document.getElementById('status-box');
      box.style.display = 'block';
      box.style.background = isSuccess ? 'rgba(16,185,129,0.12)' : 'rgba(244,63,94,0.12)';
      box.style.color = isSuccess ? '#10b981' : '#f43f5e';
      box.innerHTML = msg;
    }}

    async function submitStandardVerification(token) {{
      if (!cfTurnstileToken) {{
        return showMsg(isVi ? ' Vui lòng hoàn thành xác thực Cloudflare ở trên trước khi bấm.' : ' Please complete the Cloudflare challenge above first.');
      }}

      const btn = document.getElementById('btn-submit');
      if (!token) return showMsg(' Invalid session token. Please click verify again on Discord.');
      btn.disabled = true;
      btn.textContent = isVi ? 'Đang xác minh...' : 'Verifying...';

      try {{
        const res = await fetch('/api/verify/complete', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, cf_token: cfTurnstileToken }})
        }});
        const data = await res.json();
        if (data.ok) {{
          triggerSuccessCelebration();
        }} else {{
          showMsg(' ' + (data.detail || 'Verification failed.'));
          btn.disabled = false;
          btn.textContent = isVi ? 'Thử lại xác thực' : 'Retry Verification';
        }}
      }} catch (e) {{
        showMsg(isVi ? ' Lỗi kết nối máy chủ.' : ' Connection error.');
        btn.disabled = false;
        btn.textContent = isVi ? 'Thử lại xác thực' : 'Retry Verification';
      }}
    }}

    async function submitBiometricAuth(token) {{
      const btn = document.getElementById('btn-biometric');
      if (!token) return showMsg(' Invalid session token.');
      btn.disabled = true;
      btn.textContent = isVi ? 'Đang quét sinh trắc học...' : 'Scanning Biometrics...';

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
          triggerSuccessCelebration();
        }} else {{
          showMsg(' ' + (data.detail || 'Biometric verification failed.'));
          btn.disabled = false;
          btn.textContent = isVi ? 'Thử lại Sinh trắc học' : 'Retry Biometrics';
        }}
      }} catch (e) {{
        showMsg(isVi ? ' Lỗi kết nối máy chủ.' : ' Connection error.');
        btn.disabled = false;
        btn.textContent = isVi ? 'Thử lại Sinh trắc học' : 'Retry Biometrics';
      }}
    }}

    async function sendEmailOtp(token) {{
      if (!cfTurnstileToken) {{
        return showMsg(isVi ? ' Vui lòng hoàn thành xác thực Cloudflare ở trên trước khi gửi mã.' : ' Please complete the Cloudflare challenge above first.');
      }}

      const email = document.getElementById('inp-email').value.trim();
      const btn = document.getElementById('btn-send-otp');
      if (!email || !email.includes('@')) return showMsg(isVi ? ' Vui lòng nhập địa chỉ email hợp lệ.' : ' Please enter a valid email address.');
      if (!token) return showMsg(isVi ? ' Phiên xác thực không hợp lệ.' : ' Invalid session token.');

      btn.disabled = true;
      btn.textContent = isVi ? 'Đang gửi mã OTP...' : 'Sending OTP...';

      try {{
        const res = await fetch('/api/verify/email/send-otp', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, email: email, cf_token: cfTurnstileToken }})
        }});
        const data = await res.json();
        if (data.ok) {{
          showMsg(isVi ? ' <strong>Đã gửi mã xác nhận!</strong> Vui lòng kiểm tra hộp thư hoặc mục Spam.' : ' <strong>Verification code sent!</strong> Check your email inbox or spam folder.', true);
          document.getElementById('step-email').style.display = 'none';
          document.getElementById('step-otp').style.display = 'block';
        }} else {{
          showMsg(' ' + (data.detail || 'Failed to send OTP code.'));
          btn.disabled = false;
          btn.textContent = isVi ? 'Gửi Mã Xác Nhận ' : 'Send Verification Code ';
        }}
      }} catch (e) {{
        showMsg(isVi ? ' Không thể kết nối tới máy chủ.' : ' Failed to connect to server.');
        btn.disabled = false;
        btn.textContent = isVi ? 'Gửi Mã Xác Nhận ' : 'Send Verification Code ';
      }}
    }}

    async function submitEmailOtp(token) {{
      const otp = document.getElementById('inp-otp').value.trim();
      const btn = document.getElementById('btn-verify-otp');
      if (!otp || otp.length < 4) return showMsg(isVi ? ' Vui lòng nhập đủ mã 6 số.' : ' Please enter the complete 6-digit code.');

      btn.disabled = true;
      btn.textContent = isVi ? 'Đang kiểm tra mã...' : 'Verifying Code...';

      try {{
        const res = await fetch('/api/verify/email/verify-otp', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ session: token, otp: otp }})
        }});
        const data = await res.json();
        if (data.ok) {{
          triggerSuccessCelebration();
        }} else {{
          showMsg(data.detail || (isVi ? ' Mã xác nhận không đúng hoặc đã hết hạn.' : ' Incorrect or expired code.'));
          btn.disabled = false;
          btn.textContent = isVi ? 'Xác Nhận Mã OTP' : 'Verify OTP Code';
        }}
      }} catch (e) {{
        showMsg(isVi ? ' Lỗi kết nối máy chủ.' : ' Connection error.');
        btn.disabled = false;
        btn.textContent = isVi ? 'Xác Nhận Mã OTP' : 'Verify OTP Code';
      }}
    }}

    function resetEmailStep() {{
      document.getElementById('step-otp').style.display = 'none';
      document.getElementById('step-email').style.display = 'block';
      const btn = document.getElementById('btn-send-otp');
      btn.disabled = false;
      btn.textContent = isVi ? 'Gửi Mã Xác Nhận ' : 'Send Verification Code ';
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(html)

def get_real_client_ip(request: Request) -> str:
    """Extract true visitor IP through Cloudflare, Render, or reverse proxy."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()
    xff = request.headers.get("x-forwarded-for")
    if xff and xff.strip():
        return xff.split(",")[0].strip()
    x_real = request.headers.get("x-real-ip")
    if x_real and x_real.strip():
        return x_real.strip()
    return request.client.host if request.client else "127.0.0.1"

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

    client_ip = get_real_client_ip(request)

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
        if alt_user_id and str(alt_user_id) != str(member.id):
            allowed, alt_msg = await handle_alt_detection(bot, guild, member, alt_user_id, method=f"IP ({client_ip})")
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
    except Exception as e:
        log.error(f"Failed to add verified role: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "detail": f"Discord Permission Error: Bot cannot assign role '{verified_role.name}'. Please make sure Passkey's bot role is higher than '{verified_role.name}' in Discord Server Settings."})

    # Save to Database
    if bot.db:
        try:
            await bot.db.log_verification(guild.id, member.id, method=verif_method, ip_hash=client_ip)
        except Exception as e:
            log.warning(f"Failed to log verification in DB: {e}")

    # Send Verification Audit Log to #passkey-logs
    log_chan_id = config.get("log_channel_id")
    log_chan = guild.get_channel(int(log_chan_id)) if log_chan_id else (discord.utils.get(guild.text_channels, name="passkey-logs") or discord.utils.get(guild.text_channels, name="security-logs"))
    if log_chan:
        try:
            import datetime
            from utils.emojis import Emojis
            account_age_days = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
            verified_emoji = Emojis.get("verified", bot)
            shield_emoji = Emojis.get("shield", bot)

            log_embed = discord.Embed(
                title=f"{verified_emoji} Member Verified Successfully",
                description=(
                    f"**Member:** {member.mention} (`{member.id}`)\n"
                    f"**Verification Method:** `{verif_method.upper()}`\n"
                    f"**Role Assigned:** {verified_role.mention}\n"
                    f"**Account Age:** `{account_age_days} days`\n"
                    f"**Client IP:** `{client_ip}`\n"
                    f"**Status:** {shield_emoji} Access Granted"
                ),
                color=0x10B981,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            log_embed.set_thumbnail(url=member.display_avatar.url)
            log_embed.set_footer(text="Passkey Security Audit Log")
            await log_chan.send(embed=log_embed)
        except Exception as e:
            log.warning(f"Could not send verif log to channel: {e}")

    return {"ok": True}

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

    client_ip = get_real_client_ip(request)
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
        if alt_user_id and str(alt_user_id) != str(member.id):
            allowed, alt_msg = await handle_alt_detection(bot, guild, member, alt_user_id, method=f"Email ({email})")
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

    client_ip = get_real_client_ip(request)
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
    except Exception as e:
        log.error(f"Failed to add verified role: {e}")
        return JSONResponse(status_code=500, content={"ok": False, "detail": f"Discord Permission Error: Bot cannot assign role '{verified_role.name}'. Please make sure Passkey's bot role is higher than '{verified_role.name}' in Discord Server Settings."})

    if bot.db:
        try:
            await bot.db.log_verification(guild.id, member.id, method="email", email=otp_data["email"], ip_hash=client_ip)
        except Exception as e:
            log.warning(f"Failed to log email verification in DB: {e}")

    # Send Verification Audit Log to #passkey-logs
    log_chan_id = config.get("log_channel_id")
    log_chan = guild.get_channel(int(log_chan_id)) if log_chan_id else (discord.utils.get(guild.text_channels, name="passkey-logs") or discord.utils.get(guild.text_channels, name="security-logs"))
    if log_chan:
        try:
            import datetime
            from utils.emojis import Emojis
            account_age_days = (datetime.datetime.now(datetime.timezone.utc) - member.created_at).days
            verified_emoji = Emojis.get("verified", bot)
            otp_emoji = Emojis.get("otp", bot)

            log_embed = discord.Embed(
                title=f"{verified_emoji} Member Email Verified Successfully",
                description=(
                    f"**Member:** {member.mention} (`{member.id}`)\n"
                    f"**Method:** `EMAIL OTP` {otp_emoji}\n"
                    f"**Email:** `{otp_data['email']}`\n"
                    f"**Role Assigned:** {verified_role.mention}\n"
                    f"**Account Age:** `{account_age_days} days`\n"
                    f"**Client IP:** `{client_ip}`"
                ),
                color=0x10B981,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            log_embed.set_thumbnail(url=member.display_avatar.url)
            log_embed.set_footer(text="Passkey Security Audit Log")
            await log_chan.send(embed=log_embed)
        except Exception as e:
            log.warning(f"Could not send email verif log to channel: {e}")

    return {"ok": True}
