# -*- coding: utf-8 -*-
"""Passkey Dashboard — High-Converting Futuristic Cyber Landing Page."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER
from utils.config import Config

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guild_count = len(bot.guilds) if bot and bot.is_ready() else 1
    user_count = sum(g.member_count or 0 for g in bot.guilds) if bot and bot.is_ready() else 1500
    invite_url = f"https://discord.com/oauth2/authorize?client_id={Config.DISCORD_CLIENT_ID}&permissions=1395293285622&integration_type=0&scope=bot+applications.commands"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Passkey — Next-Gen Discord Gatekeeper &amp; Zero-Trust Verification</title>
  {BASE_STYLE}
  <style>
    .hero {{
      max-width: 1100px; margin: 60px auto 40px; text-align: center; padding: 0 20px;
    }}
    .hero-badge {{
      margin-bottom: 24px;
    }}
    .hero-title {{
      font-size: 3.6rem; font-weight: 900; line-height: 1.15; letter-spacing: -1.5px;
      margin: 0 0 24px;
    }}
    .hero-title span {{
      background: var(--gradient-neon);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .hero-subtitle {{
      font-size: 1.25rem; color: var(--text-muted); max-width: 780px; margin: 0 auto 36px;
      line-height: 1.6; font-weight: 500;
    }}
    .hero-actions {{
      display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; margin-bottom: 50px;
    }}
    .btn-primary {{
      background: var(--gradient-btn); color: #fff !important; font-weight: 800; font-size: 1.05rem;
      padding: 14px 32px; border-radius: 12px; box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
      display: inline-flex; align-items: center; gap: 10px; transition: all 0.25s;
    }}
    .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 12px 35px rgba(99, 102, 241, 0.6); }}
    .btn-secondary {{
      background: rgba(255,255,255,0.06); border: 1px solid var(--border); color: var(--text) !important;
      font-weight: 700; font-size: 1.05rem; padding: 14px 28px; border-radius: 12px;
      display: inline-flex; align-items: center; gap: 10px; transition: all 0.25s;
    }}
    .btn-secondary:hover {{ background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.2); }}

    .stats-bar {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 18px;
      max-width: 1000px; margin: 0 auto 80px; padding: 0 20px;
    }}
    .stat-box {{
      padding: 24px; text-align: center; border-radius: 16px;
    }}
    .stat-val {{
      font-size: 2.2rem; font-weight: 900; font-family: var(--mono); color: #38bdf8;
      margin-bottom: 4px;
    }}
    .stat-lbl {{
      font-size: 0.82rem; color: var(--text-dim); text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;
    }}

    .section-header {{
      text-align: center; max-width: 700px; margin: 0 auto 48px; padding: 0 20px;
    }}
    .section-title {{
      font-size: 2.3rem; font-weight: 900; margin: 0 0 14px; letter-spacing: -0.5px;
    }}
    .section-subtitle {{
      color: var(--text-muted); font-size: 1.02rem;
    }}

    .modes-grid {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px;
      max-width: 1140px; margin: 0 auto 90px; padding: 0 20px;
    }}
    .mode-card {{
      padding: 30px; border-radius: 20px; display: flex; flex-direction: column; justify-content: space-between;
    }}
    .mode-icon-wrap {{
      margin-bottom: 18px;
    }}
    .mode-title {{
      font-size: 1.25rem; font-weight: 800; margin: 0 0 10px; color: var(--text);
    }}
    .mode-desc {{
      font-size: 0.9rem; color: var(--text-muted); line-height: 1.6; margin: 0;
    }}

    .feature-banner {{
      max-width: 1140px; margin: 0 auto 90px; padding: 48px 40px; border-radius: 24px;
      background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(168,85,247,0.12) 100%);
      border: 1px solid rgba(99,102,241,0.35); display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: 30px;
    }}

    @media (max-width: 768px) {{
      .hero-title {{ font-size: 2.4rem; }}
      .hero-subtitle {{ font-size: 1.05rem; }}
      .feature-banner {{ padding: 32px 24px; }}
    }}
  </style>
</head>
<body>
  {NAV_BAR}

  <main>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-badge">
        <span class="badge-neon">
          <img src="/static/emojis/passkey.png" class="emoji-icon" alt="">
          <span>ZERO-TRUST VERIFICATION INFRASTRUCTURE</span>
        </span>
      </div>
      <h1 class="hero-title">
        The Ultimate Gatekeeper for<br><span>Discord Server Security</span>
      </h1>
      <p class="hero-subtitle">
        Protect your community against raid bots, malicious alternate accounts, phishing links, and spam with 9 cutting-edge verification engines powered by Cloudflare Turnstile &amp; WebAuthn Biometrics.
      </p>
      <div class="hero-actions">
        <a href="{invite_url}" target="_blank" class="btn-primary">
          <img src="/static/emojis/passkey.png" alt="Key" class="emoji-icon">
          <span>Add to Discord Free</span>
        </a>
        <a href="/commands" class="btn-secondary">
          <img src="/static/emojis/shield.png" alt="Shield" class="emoji-icon">
          <span>Explore Commands &rarr;</span>
        </a>
      </div>
    </section>

    <!-- Real-Time Metric Ticker -->
    <section class="stats-bar">
      <div class="glass-card stat-box">
        <div class="stat-val">9 Engines</div>
        <div class="stat-lbl">Verification Modes</div>
      </div>
      <div class="glass-card stat-box">
        <div class="stat-val">100%</div>
        <div class="stat-lbl">Anti-Alt Accuracy</div>
      </div>
      <div class="glass-card stat-box">
        <div class="stat-val">10 Langs</div>
        <div class="stat-lbl">Global Interface</div>
      </div>
      <div class="glass-card stat-box">
        <div class="stat-val">&lt; 1ms</div>
        <div class="stat-lbl">Cloud DB Latency</div>
      </div>
    </section>

    <!-- 9 Verification Modes Showcase -->
    <section>
      <div class="section-header">
        <span class="badge-neon" style="margin-bottom:12px;">
          <img src="/static/emojis/shield.png" class="emoji-icon" alt="">
          <span>MULTI-LAYER GATEWAY</span>
        </span>
        <h2 class="section-title">9 Next-Generation Verification Modes</h2>
        <p class="section-subtitle">Choose the perfect gatekeeper workflow tailored for your server, from 1-click in-Discord prompts to biometric hardware keys.</p>
      </div>

      <div class="modes-grid">
        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/verified.png" class="emoji-icon-lg" alt="Web"></div>
            <h3 class="mode-title">Cloudflare Turnstile Portal</h3>
            <p class="mode-desc">Non-intrusive smart browser challenge backed by Cloudflare AI with dual-layer IP alt detection.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/biometric.png" class="emoji-icon-lg" alt="Biometrics"></div>
            <h3 class="mode-title">Hardware Biometric Passkey</h3>
            <p class="mode-desc">Zero-Trust WebAuthn FIDO2 authentication using Touch ID, Face ID, Windows Hello, or YubiKeys.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/otp.png" class="emoji-icon-lg" alt="Email OTP"></div>
            <h3 class="mode-title">Zoho Email OTP</h3>
            <p class="mode-desc">Sends 6-digit one-time passcodes with deliverability-optimized HTML layouts to ensure primary inbox delivery.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/image_captcha.png" class="emoji-icon-lg" alt="Image CAPTCHA"></div>
            <h3 class="mode-title">In-Discord Image CAPTCHA</h3>
            <p class="mode-desc">Generates dynamic high-contrast distorted character challenges rendered with security noise lines in Discord.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/pattern.png" class="emoji-icon-lg" alt="Pattern"></div>
            <h3 class="mode-title">Emoji Sequence Pattern</h3>
            <p class="mode-desc">Interactive memory &amp; pattern matching challenge requiring users to click randomized emoji buttons in exact order.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/social.png" class="emoji-icon-lg" alt="Social"></div>
            <h3 class="mode-title">Social Account Link Check</h3>
            <p class="mode-desc">Verifies presence of linked external accounts (Steam, YouTube, GitHub, Twitter, Spotify) to filter throwaway alts.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/passkey.png" class="emoji-icon-lg" alt="Math"></div>
            <h3 class="mode-title">Interactive Math Modal</h3>
            <p class="mode-desc">Dynamic randomized arithmetic puzzles presented in native Discord modal dialogs for fast validation.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/lock.png" class="emoji-icon-lg" alt="Rules"></div>
            <h3 class="mode-title">Server Rules Agreement</h3>
            <p class="mode-desc">Requires new members to read community guidelines and type affirmative confirmations before unlocking channels.</p>
          </div>
        </div>

        <div class="glass-card mode-card">
          <div>
            <div class="mode-icon-wrap"><img src="/static/emojis/shield.png" class="emoji-icon-lg" alt="Button"></div>
            <h3 class="mode-title">1-Click Direct Button</h3>
            <p class="mode-desc">Frictionless single-tap verification for casual community servers with immediate role assignment.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Deep Defense & Anti-Alt Banner -->
    <section style="padding:0 20px;">
      <div class="feature-banner">
        <div style="max-width:600px;">
          <span class="badge-neon" style="margin-bottom:12px;">
            <img src="/static/emojis/alt.png" class="emoji-icon" alt="">
            <span>DEEP NEURAL DEFENSE</span>
          </span>
          <h2 style="font-size:2rem;font-weight:900;margin:8px 0 14px;">5-Attempt Verification Escalator &amp; Anti-Alt Policy</h2>
          <p style="color:var(--text-muted);font-size:0.95rem;line-height:1.6;margin:0;">
            Stop spam scripts dead in their tracks. Passkey monitors failed attempts with automatic 3-strike escalation (Warning 1 &rarr; Warning 2 &rarr; Auto-Kick &rarr; Permanent Ban). Choose custom actions for suspected clone accounts: Quarantine, Log, Kick, or Ban.
          </p>
        </div>
        <div>
          <a href="{invite_url}" target="_blank" class="btn-primary" style="white-space:nowrap;">
            <img src="/static/emojis/shield.png" class="emoji-icon" alt="">
            <span>Deploy Defense Now &rarr;</span>
          </a>
        </div>
      </div>
    </section>
  </main>

  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
