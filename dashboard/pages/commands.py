# -*- coding: utf-8 -*-
"""Passkey Dashboard — Interactive Slash Commands Reference Directory."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER
from utils.config import Config

router = APIRouter()

COMMANDS_DATA = [
    {
        "category": "Verification",
        "commands": [
            {
                "name": "/setup",
                "aliases": [".setup", "/wizard"],
                "desc": "Launches the interactive 5-Step Paginated Setup Wizard with channel selection and deploy button.",
                "perms": "Administrator",
                "params": "None"
            },
            {
                "name": "/settings",
                "aliases": [".settings", "/config", "/panel"],
                "desc": "Opens the Master Control Panel with real-time dropdowns and 1-click AutoMod toggle buttons.",
                "perms": "Administrator",
                "params": "None"
            },
            {
                "name": "/verify",
                "aliases": [".verify"],
                "desc": "Requests an individual verification session link or prompt based on the server's configured mode.",
                "perms": "Everyone",
                "params": "None"
            },
            {
                "name": "/setmode",
                "aliases": [".setmode"],
                "desc": "Switches the verification engine between 9 modes (web, biometric, email, image_captcha, pattern, social, captcha, rules, button).",
                "perms": "Administrator",
                "params": "<mode: web|biometric|email|image_captcha|pattern|social|captcha|rules|button>"
            },
            {
                "name": "/setlang",
                "aliases": [".setlang", "/language"],
                "desc": "Sets the default server interface & email language across 10 global languages (English default).",
                "perms": "Administrator",
                "params": "<lang: en|vi|ja|ko|zh|es|fr|de|ru|pt>"
            },
            {
                "name": "/minage",
                "aliases": [".minage"],
                "desc": "Enforces a minimum Discord account age in days before members are allowed to verify.",
                "perms": "Administrator",
                "params": "<days: 0, 3, 7, 14, 30>"
            },
            {
                "name": "/setlog",
                "aliases": [".setlog"],
                "desc": "Assigns the security audit log channel for verification results, anti-alt alerts, and automod strikes.",
                "perms": "Administrator",
                "params": "<channel: #channel>"
            }
        ]
    },
    {
        "category": "AutoMod & Defense Shields",
        "commands": [
            {
                "name": ".antispam",
                "aliases": ["/antispam"],
                "desc": "Toggles dynamic message rate-limiting and burst spam protection on or off.",
                "perms": "Manage Guild",
                "params": "[on|off]"
            },
            {
                "name": ".antiinvite",
                "aliases": ["/antiinvite"],
                "desc": "Blocks unauthorized Discord server invitation links from non-moderator members.",
                "perms": "Manage Guild",
                "params": "[on|off]"
            },
            {
                "name": ".antiphish",
                "aliases": ["/antiphish"],
                "desc": "Scans and neutralizes malicious phishing domains, nitro scam links, and token grabbers.",
                "perms": "Manage Guild",
                "params": "[on|off]"
            },
            {
                "name": ".antialt",
                "aliases": ["/antialt"],
                "desc": "Enables multi-account detection using IP fingerprints and verified email hash matches.",
                "perms": "Manage Guild",
                "params": "[on|off]"
            },
            {
                "name": ".lockdown",
                "aliases": ["/lockdown"],
                "desc": "Instantly freezes and locks text channels during raid attacks to prevent spam floods.",
                "perms": "Manage Channels",
                "params": "[#channel]"
            },
            {
                "name": ".unlock",
                "aliases": ["/unlock"],
                "desc": "Restores normal messaging permissions to locked channels after threat neutralization.",
                "perms": "Manage Channels",
                "params": "[#channel]"
            }
        ]
    },
    {
        "category": "Moderation & System",
        "commands": [
            {
                "name": ".warn",
                "aliases": ["/warn"],
                "desc": "Issues a formal recorded moderation strike to a member with custom violation reason.",
                "perms": "Moderate Members",
                "params": "<@member> [reason]"
            },
            {
                "name": ".warnings",
                "aliases": ["/warnings"],
                "desc": "Displays the complete infraction history and active strikes for a specific user.",
                "perms": "Moderate Members",
                "params": "<@member>"
            },
            {
                "name": ".kick",
                "aliases": ["/kick"],
                "desc": "Kicks a member from the server with audit logging.",
                "perms": "Kick Members",
                "params": "<@member> [reason]"
            },
            {
                "name": ".ban",
                "aliases": ["/ban"],
                "desc": "Permanently bans a member from the server and purges recent messages.",
                "perms": "Ban Members",
                "params": "<@member> [reason]"
            },
            {
                "name": ".purge",
                "aliases": ["/purge", "/clear"],
                "desc": "Bulk-deletes a specified number of recent messages from the current channel.",
                "perms": "Manage Messages",
                "params": "<amount: 1-100>"
            },
            {
                "name": ".sync",
                "aliases": [".sync global", ".sync clean_all"],
                "desc": "Synchronizes and cleans slash commands across Discord clusters to avoid command duplication.",
                "perms": "Administrator",
                "params": "[global|clean_all]"
            }
        ]
    }
]

@router.get("/commands", response_class=HTMLResponse)
async def commands_page():
    sections_html = ""
    for cat in COMMANDS_DATA:
        cmds_html = ""
        for cmd in cat["commands"]:
            aliases_str = " ".join([f'<span class="badge-alias">{a}</span>' for a in cmd["aliases"]])
            cmds_html += f"""
            <div class="glass-card cmd-card">
              <div class="cmd-top">
                <div class="cmd-name-box">
                  <span class="cmd-name">{cmd["name"]}</span>
                  {aliases_str}
                </div>
                <span class="cmd-perm">{cmd["perms"]}</span>
              </div>
              <p class="cmd-desc">{cmd["desc"]}</p>
              <div class="cmd-param-box">
                <span style="font-size:0.76rem;color:var(--text-dim);font-weight:700;">SYNTAX:</span>
                <code>{cmd["name"]} {cmd["params"]}</code>
              </div>
            </div>
            """
        sections_html += f"""
        <div class="category-block">
          <h2 class="cat-title">🛡️ {cat["category"]}</h2>
          <div class="cmd-list">{cmds_html}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Commands Reference — Passkey Gatekeeper</title>
  {BASE_STYLE}
  <style>
    .page-wrap {{
      max-width: 1080px; margin: 50px auto; padding: 0 20px;
    }}
    .cat-title {{
      font-size: 1.5rem; font-weight: 800; margin: 40px 0 18px; color: #818cf8;
      border-bottom: 1px solid var(--border); padding-bottom: 8px;
    }}
    .cmd-list {{
      display: flex; flex-direction: column; gap: 16px;
    }}
    .cmd-card {{
      padding: 20px 24px; border-radius: 14px;
    }}
    .cmd-top {{
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;
    }}
    .cmd-name-box {{
      display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    }}
    .cmd-name {{
      font-family: var(--mono); font-weight: 800; font-size: 1.15rem; color: #38bdf8;
    }}
    .badge-alias {{
      font-family: var(--mono); font-size: 0.72rem; padding: 2px 8px; border-radius: 6px;
      background: rgba(255,255,255,0.06); color: var(--text-dim);
    }}
    .cmd-perm {{
      font-size: 0.74rem; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 10px; border-radius: 6px;
    }}
    .cmd-desc {{
      margin: 0 0 12px; color: var(--text-muted); font-size: 0.9rem; line-height: 1.5;
    }}
    .cmd-param-box {{
      display: flex; align-items: center; gap: 10px; background: rgba(15, 23, 42, 0.6);
      padding: 8px 14px; border-radius: 8px; font-family: var(--mono); font-size: 0.84rem;
    }}
    .cmd-param-box code {{ color: #a855f7; }}
  </style>
</head>
<body>
  {NAV_BAR}
  <main class="page-wrap">
    <div style="text-align:center;margin-bottom:40px;">
      <span class="badge-neon" style="margin-bottom:12px;">COMMAND DIRECTORY</span>
      <h1 style="font-size:2.6rem;font-weight:900;margin:8px 0 12px;">Passkey Slash &amp; Prefix Commands</h1>
      <p style="color:var(--text-muted);font-size:1.05rem;max-width:650px;margin:0 auto;">
        Complete command catalog for Discord server administrators, moderators, and members.
      </p>
    </div>

    {sections_html}
  </main>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
