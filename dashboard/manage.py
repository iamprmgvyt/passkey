# -*- coding: utf-8 -*-
"""Passkey Dashboard — Server Management Panel."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER
from utils.config import Config

manage_router = APIRouter(tags=["Manage"])

@manage_router.get("/manage", response_class=HTMLResponse)
async def manage_page(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guilds = bot.guilds if bot and bot.is_ready() else []

    guild_rows = ""
    for g in guilds:
        icon = g.icon.url if g.icon else "/static/passkey.png"
        guild_rows += f"""
        <div class="glass-card guild-item">
          <div style="display:flex;align-items:center;gap:16px;">
            <img src="{icon}" class="guild-avatar" onerror="this.src='/static/passkey.png'">
            <div>
              <div style="font-weight:800;font-size:1.1rem;color:var(--text);">{g.name}</div>
              <div style="font-size:0.82rem;color:var(--text-dim);font-family:var(--mono);">
                {g.member_count:,} members &bull; ID: {g.id}
              </div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span class="badge-neon" style="color:#10b981;border-color:rgba(16,185,129,0.3);background:rgba(16,185,129,0.1);">● PROTECTED</span>
            <a href="https://discord.com/channels/{g.id}" target="_blank" class="btn-manage">Open in Discord</a>
          </div>
        </div>
        """

    if not guild_rows:
        invite_url = f"https://discord.com/oauth2/authorize?client_id={Config.DISCORD_CLIENT_ID}&permissions=1395293285622&integration_type=0&scope=bot+applications.commands"
        guild_rows = f"""
        <div class="glass-card" style="text-align:center;padding:50px 20px;">
          <div style="font-size:3rem;margin-bottom:12px;">🛡️</div>
          <h2 style="font-size:1.4rem;font-weight:800;margin:0 0 8px;">No Discord Servers Connected Yet</h2>
          <p style="color:var(--text-muted);font-size:0.95rem;max-width:500px;margin:0 auto 24px;">
            Invite Passkey Bot to your server to activate Zero-Trust verification and defense shields.
          </p>
          <a href="{invite_url}" target="_blank" class="nav-btn" style="display:inline-flex;">+ Add Passkey to Server</a>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Manage Servers — Passkey Gatekeeper</title>
  {BASE_STYLE}
  <style>
    .page-wrap {{ max-width: 1080px; margin: 50px auto; padding: 0 20px; }}
    .guild-item {{
      padding: 20px 24px; border-radius: 16px; display: flex; justify-content: space-between;
      align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 14px;
    }}
    .guild-avatar {{
      width: 48px; height: 48px; border-radius: 12px; object-fit: cover;
      border: 1px solid var(--border);
    }}
    .btn-manage {{
      background: rgba(255,255,255,0.08); border: 1px solid var(--border); color: var(--text);
      padding: 8px 18px; border-radius: 10px; font-weight: 700; font-size: 0.85rem; text-decoration: none;
      transition: all 0.2s;
    }}
    .btn-manage:hover {{ background: rgba(255,255,255,0.16); border-color: rgba(255,255,255,0.3); }}
  </style>
</head>
<body>
  {NAV_BAR}
  <main class="page-wrap">
    <div style="text-align:center;margin-bottom:40px;">
      <span class="badge-neon" style="margin-bottom:12px;">ACTIVE CLUSTERS</span>
      <h1 style="font-size:2.5rem;font-weight:900;margin:8px 0 12px;">Protected Server Management</h1>
      <p style="color:var(--text-muted);font-size:1.05rem;max-width:600px;margin:0 auto;">
        View and manage your active communities protected by Passkey Gatekeeper.
      </p>
    </div>

    <div>
      {guild_rows}
    </div>
  </main>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
