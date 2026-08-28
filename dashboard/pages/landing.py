# -*- coding: utf-8 -*-
"""Passkey Dashboard — / Landing Page."""
import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

router = APIRouter(tags=["Landing"])

POPULAR_COMMANDS = [
    {
        "id": "CMD-01",
        "name": ".setup",
        "category": "Verification",
        "perm": "Administrator",
        "desc": "One-click auto setup: creates #verify channel, configures @Verified role, and posts the interactive verification button.",
        "usage": ".setup"
    },
    {
        "id": "CMD-02",
        "name": ".verify",
        "category": "Verification",
        "perm": "Everyone",
        "desc": "Generates a direct personal 1-click verification link.",
        "usage": ".verify"
    },
    {
        "id": "CMD-03",
        "name": ".antialt on/off",
        "category": "Anti-Alt Shield",
        "perm": "Administrator",
        "desc": "Toggles salted browser fingerprinting and duplicate IP quarantine.",
        "usage": ".antialt [on/off]"
    },
    {
        "id": "CMD-04",
        "name": ".scan",
        "category": "Threat Scanner",
        "perm": "Everyone",
        "desc": "Dispatches a suspicious link to the isolated Chromium VPS sandbox cluster.",
        "usage": ".scan <url>"
    },
    {
        "id": "CMD-05",
        "name": ".warn",
        "category": "Moderation",
        "perm": "Manage Messages",
        "desc": "Issues a formal infraction warning to a member.",
        "usage": ".warn @user [reason]"
    },
    {
        "id": "CMD-06",
        "name": ".kick / .ban",
        "category": "Moderation",
        "perm": "Kick/Ban Members",
        "desc": "Removes malicious or rule-violating members from the guild.",
        "usage": ".kick @user | .ban @user"
    }
]

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guild_count = len(bot.guilds) if bot and bot.is_ready() else 31
    user_count = len(bot.users) if bot and bot.is_ready() else 1084

    cmd_cards_html = ""
    for c in POPULAR_COMMANDS:
        cid = c["id"]
        cname = c["name"]
        ccat = c["category"]
        cmd_cards_html += f"""
        <div class="cmd-item-box" onclick="openCmdModal('{cid}')">
          <div style="display:flex;flex-direction:column;gap:4px;">
            <span class="cmd-name">{cname}</span>
            <span style="font-size:0.75rem;color:var(--text-dim);">{ccat}</span>
          </div>
          <span class="cmd-id-tag">{cid}</span>
        </div>
        """

    commands_json_escaped = json.dumps(POPULAR_COMMANDS).replace("'", "\'")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Passkey — Next-Gen Discord Verification &amp; Threat Intelligence</title>
  {BASE_STYLE}
  <style>
    .container {{ max-width: 1140px; margin: 0 auto; padding: 0 24px; }}
    
    .hero-wrap {{
      padding: clamp(50px, 8vw, 88px) 0 clamp(40px, 6vw, 68px);
      text-align: center;
      background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 60%);
      border-bottom: 1px solid var(--border);
    }}
    .hero-badge {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 6px 16px; background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 999px;
      font-family: var(--mono); font-size: 0.76rem; font-weight: 700;
      color: #818cf8; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 20px;
    }}
    .hero-title {{
      font-size: clamp(2.4rem, 6vw, 3.8rem);
      font-weight: 900; line-height: 1.15; letter-spacing: -0.03em;
      margin-bottom: 18px;
    }}
    .hero-title span {{
      background: linear-gradient(135deg, #6366f1 0%, #10b981 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .hero-desc {{
      font-size: clamp(1.05rem, 2.4vw, 1.2rem);
      color: var(--text-muted); max-width: 680px; margin: 0 auto 36px;
    }}
    .hero-actions {{
      display: flex; justify-content: center; gap: 14px; flex-wrap: wrap; margin-bottom: 44px;
    }}
    .btn-main {{
      display: inline-flex; align-items: center; gap: 10px;
      padding: 14px 28px; border-radius: 12px; font-size: 0.95rem;
      font-weight: 800; text-decoration: none; cursor: pointer; transition: all 0.2s;
    }}
    .btn-main-indigo {{
      background: #6366f1; color: #fff; box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }}
    .btn-main-indigo:hover {{
      background: #4f46e5; transform: translateY(-2px);
    }}
    .btn-main-glass {{
      background: rgba(255, 255, 255, 0.05); color: var(--text); border: 1px solid var(--border);
    }}

    .hero-stats-row {{
      display: flex; justify-content: center; gap: clamp(16px, 4vw, 44px);
      flex-wrap: wrap; padding-top: 24px; border-top: 1px dashed rgba(255, 255, 255, 0.1);
    }}
    .stat-pill {{ display: flex; flex-direction: column; align-items: center; }}
    .stat-pill-val {{ font-family: var(--mono); font-size: 1.5rem; font-weight: 800; color: var(--text); }}

    /* Bento Grid */
    .bento-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 40px; }}
    @media (max-width: 850px) {{ .bento-grid {{ grid-template-columns: 1fr; }} }}
    .bento-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 16px;
      padding: 28px; display: flex; flex-direction: column; justify-content: space-between;
    }}
    .bento-card h3 {{ font-size: 1.2rem; font-weight: 800; margin-bottom: 8px; }}
    .bento-card p {{ color: var(--text-muted); font-size: 0.88rem; line-height: 1.6; }}

    /* Commands */
    .cmd-grid {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin-top: 24px;
    }}
    .cmd-item-box {{
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 16px 18px; cursor: pointer; transition: all 0.2s ease;
      display: flex; align-items: center; justify-content: space-between;
    }}
    .cmd-item-box:hover {{
      background: var(--card-hover); border-color: #6366f1; transform: translateY(-2px);
    }}
    .cmd-id-tag {{
      font-family: var(--mono); font-size: 0.68rem; font-weight: 800;
      color: #818cf8; background: rgba(99, 102, 241, 0.12); padding: 3px 8px; border-radius: 6px;
    }}
    .cmd-name {{ font-family: var(--mono); font-size: 0.88rem; font-weight: 700; color: var(--text); }}

    /* Modal */
    .modal-backdrop {{
      position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
      z-index: 9999; display: none; align-items: center; justify-content: center; padding: 20px;
    }}
    .modal-box {{
      background: var(--card); border: 1px solid var(--border); border-radius: 16px;
      padding: 28px; max-width: 500px; width: 100%; position: relative;
    }}
    .modal-close-btn {{
      position: absolute; top: 18px; right: 18px; background: none; border: none;
      color: var(--text-dim); font-size: 1.3rem; cursor: pointer;
    }}
  </style>
</head>
<body>
  {NAV_BAR}

  <section class="hero-wrap">
    <div class="container">
      <div class="hero-badge">
        <span>🔑</span> NEXT-GEN DISCORD GATEKEEPER
      </div>
      <h1 class="hero-title">
        The Ultimate Verification Bot For <span>Discord</span>.
      </h1>
      <p class="hero-desc">
        1-Click Web Turnstile verification, anti-alt fingerprinting, and multi-node cloud sandbox link threat scanning.
      </p>

      <div class="hero-actions">
        <a href="https://discord.com/oauth2/authorize?client_id=1399740322883567646&permissions=1395293285622&integration_type=0&scope=bot+applications.commands" target="_blank" class="btn-main btn-main-indigo">
          <span>+ Add Passkey to Discord</span>
        </a>
        <a href="/domain" class="btn-main btn-main-glass">
          <span>Threat Scanner</span>
        </a>
        <a href="/commands" class="btn-main btn-main-glass">
          <span>Commands</span>
        </a>
      </div>

      <div class="hero-stats-row">
        <div class="stat-pill">
          <span class="stat-pill-val" id="s-guilds">{guild_count}</span>
          <span style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;">Protected Servers</span>
        </div>
        <div class="stat-pill">
          <span class="stat-pill-val" style="color:var(--emerald);" id="s-users">{user_count:,}</span>
          <span style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;">Members Guarded</span>
        </div>
        <div class="stat-pill">
          <span class="stat-pill-val" style="color:#818cf8;">&lt; 200ms</span>
          <span style="font-size:0.75rem;color:var(--text-dim);text-transform:uppercase;">Verification Speed</span>
        </div>
      </div>
    </div>
  </section>

  <!-- Bento Features -->
  <section class="container" style="padding: 60px 24px;">
    <div style="text-align:center;">
      <h2 style="font-size:clamp(1.8rem, 4vw, 2.4rem);font-weight:900;margin-bottom:8px;">Why Communities Run On Passkey</h2>
      <p style="color:var(--text-muted);">Purpose-built gatekeeper stopping spam bots, raid scripts, and phishing links.</p>
    </div>

    <div class="bento-grid">
      <div class="bento-card">
        <h3>1-Click Web Verification</h3>
        <p>Smooth Cloudflare Turnstile web gateway granting @Verified role to real users in &lt; 200ms.</p>
      </div>
      <div class="bento-card">
        <h3>Anti-Alt &amp; IP Fingerprint</h3>
        <p>Detects duplicate account logins and quarantined bad actors across communities.</p>
      </div>
      <div class="bento-card">
        <h3>Cloud Threat Sandbox</h3>
        <p>Live Chromium container sandbox clusters (VN-SG &bull; US-VA) detonating suspicious links.</p>
      </div>
    </div>
  </section>

  <!-- Commands Explorer -->
  <section class="container" style="padding: 20px 24px 80px;">
    <div style="text-align:center;">
      <h2 style="font-size:1.8rem;font-weight:900;margin-bottom:8px;">Command Explorer</h2>
      <p style="color:var(--text-muted);font-size:0.9rem;">Click any command to inspect usage and permissions.</p>
    </div>

    <div class="cmd-grid">
      {cmd_cards_html}
    </div>
  </section>

  <!-- MODAL -->
  <div class="modal-backdrop" id="cmd-modal" onclick="closeCmdModal(event)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <button class="modal-close-btn" onclick="closeCmdModal()">&times;</button>
      <span class="cmd-id-tag" id="m-id">CMD-01</span>
      <h3 style="font-size:1.3rem;font-weight:800;margin:8px 0;" id="m-name">.setup</h3>
      <p style="color:var(--text-muted);font-size:0.88rem;" id="m-desc">Description</p>
      <div style="background:rgba(0,0,0,0.2);padding:10px;border-radius:8px;margin:12px 0;">
        <code style="font-family:var(--mono);color:#818cf8;" id="m-usage">.setup</code>
      </div>
      <div style="font-size:0.8rem;color:var(--text-dim);">
        Permission Required: <strong id="m-perm" style="color:var(--text);">Administrator</strong>
      </div>
    </div>
  </div>

  {FOOTER}

  <script>
    const popularCommands = {commands_json_escaped};
    function openCmdModal(cmdId) {{
      const cmd = popularCommands.find(c => c.id === cmdId);
      if (!cmd) return;
      document.getElementById('m-id').textContent = cmd.id;
      document.getElementById('m-name').textContent = cmd.name;
      document.getElementById('m-desc').textContent = cmd.desc;
      document.getElementById('m-usage').textContent = cmd.usage;
      document.getElementById('m-perm').textContent = cmd.perm;
      document.getElementById('cmd-modal').style.display = 'flex';
    }}
    function closeCmdModal(e) {{
      if (!e || e.target === document.getElementById('cmd-modal') || e.target.classList.contains('modal-close-btn')) {{
        document.getElementById('cmd-modal').style.display = 'none';
      }}
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(html)
