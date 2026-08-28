# -*- coding: utf-8 -*-
"""Passkey Dashboard — Server Management Panel."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

manage_router = APIRouter(tags=["Manage"])

@manage_router.get("/manage", response_class=HTMLResponse)
async def manage_page(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guilds = bot.guilds if bot and bot.is_ready() else []

    guild_rows = ""
    for g in guilds:
        icon = g.icon.url if g.icon else "/static/passkey.png"
        guild_rows += f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <img src="{icon}" style="width:40px;height:40px;border-radius:50%;" onerror="this.src='/static/passkey.png'">
            <div>
              <div style="font-weight:800;">{g.name}</div>
              <div style="font-size:0.78rem;color:var(--text-dim);">{g.member_count} members</div>
            </div>
          </div>
          <a href="https://discord.com/channels/{g.id}" target="_blank" style="background:var(--indigo);color:#fff;padding:8px 16px;border-radius:8px;text-decoration:none;font-weight:700;font-size:0.85rem;">Open Discord</a>
        </div>
        """

    if not guild_rows:
        guild_rows = '<div style="color:var(--text-muted);padding:20px;">No guilds currently loaded or bot is starting up.</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}<title>Passkey — Manage Servers</title>{BASE_STYLE}
</head>
<body>
  {NAV_BAR}
  <div style="max-width:1000px;margin:40px auto;padding:0 24px;">
    <h1 style="font-size:2rem;font-weight:900;">Server Management</h1>
    <p style="color:var(--text-muted);margin-bottom:24px;">Active servers running Passkey Gatekeeper.</p>
    <div>
      {guild_rows}
    </div>
  </div>
  {FOOTER}
</body></html>"""
    return HTMLResponse(html)
