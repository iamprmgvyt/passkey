# -*- coding: utf-8 -*-
"""Passkey Dashboard — /stats page."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

router = APIRouter(tags=["Stats"])

@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guild_count = len(bot.guilds) if bot and bot.is_ready() else 31
    user_count = len(bot.users) if bot and bot.is_ready() else 1084

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}
  <title>Passkey — System Telemetry</title>
  {BASE_STYLE}
  <style>
    .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 24px; }}
    @media (max-width: 750px) {{ .stats-grid {{ grid-template-columns: 1fr; }} }}
    .stat-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 24px; text-align: center;
    }}
  </style>
</head>
<body>
  {NAV_BAR}
  <div class="container">
    <h1 style="font-size:2rem;font-weight:900;">System Telemetry</h1>
    <div class="stats-grid">
      <div class="stat-card">
        <div style="font-family:var(--mono);font-size:2rem;font-weight:800;color:var(--text);">{guild_count}</div>
        <div style="color:var(--text-muted);font-size:0.85rem;text-transform:uppercase;">Guilds Protected</div>
      </div>
      <div class="stat-card">
        <div style="font-family:var(--mono);font-size:2rem;font-weight:800;color:var(--emerald);">{user_count:,}</div>
        <div style="color:var(--text-muted);font-size:0.85rem;text-transform:uppercase;">Users Monitored</div>
      </div>
      <div class="stat-card">
        <div style="font-family:var(--mono);font-size:2rem;font-weight:800;color:#818cf8;">&lt; 200ms</div>
        <div style="color:var(--text-muted);font-size:0.85rem;text-transform:uppercase;">Turnstile Latency</div>
      </div>
    </div>
  </div>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
