# -*- coding: utf-8 -*-
"""Passkey Dashboard — /commands page."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

router = APIRouter(tags=["Commands"])

@router.get("/commands", response_class=HTMLResponse)
async def commands_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}
  <title>Passkey — Command Reference</title>
  {BASE_STYLE}
  <style>
    .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
    .section-title {{
      font-size: 1.3rem; font-weight: 800; color: #818cf8; margin: 32px 0 16px;
      display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 8px;
    }}
    .cmd-grid {{
      display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 16px;
    }}
    .cmd-card {{
      background: var(--card); border: 1px solid var(--border); border-radius: 12px;
      padding: 18px; display: flex; flex-direction: column; justify-content: space-between;
      transition: transform 0.2s;
    }}
    .cmd-card:hover {{ transform: translateY(-2px); }}
    .cmd-name {{ font-family: var(--mono); color: var(--indigo); font-size: 1rem; font-weight: 700; margin-bottom: 6px; }}
    .cmd-desc {{ color: var(--text-muted); font-size: 0.85rem; margin-bottom: 12px; flex-grow: 1; }}
    .badge {{
      font-family: var(--mono); font-size: 0.72rem; padding: 4px 8px; border-radius: 6px; width: fit-content;
    }}
    .badge-admin {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .badge-mod {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-user {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
  </style>
</head>
<body>
  {NAV_BAR}
  <div class="container">
    <h1 style="font-size:2.2rem;font-weight:900;margin-bottom:6px;">Passkey Command Manual</h1>
    <p style="color:var(--text-muted);margin-bottom:20px;">Comprehensive command guide for Passkey Bot. All commands support both Slash Commands (<code>/</code>) and Prefix (<code>.</code>).</p>

    <!-- Verification Section -->
    <div class="section-title">🔑 Verification & Gatekeeper</div>
    <div class="cmd-grid">
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/setup [mode]</div>
          <div class="cmd-desc">Auto-provisions #verify channel and @Verified role with persistent verification buttons.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/setmode &lt;mode&gt;</div>
          <div class="cmd-desc">Switches gatekeeper mode between Web Portal, 1-Click Button, or Math CAPTCHA modal.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/setlog &lt;#channel&gt;</div>
          <div class="cmd-desc">Sets the audit log channel for verification entries and security alerts.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/minage &lt;days&gt;</div>
          <div class="cmd-desc">Sets minimum Discord account age requirement to prevent fresh raid alts.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/verify</div>
          <div class="cmd-desc">Requests direct verification prompt or web link for the member.</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
    </div>

    <!-- AutoMod Section -->
    <div class="section-title">🛡️ AutoMod & Threat Defense</div>
    <div class="cmd-grid">
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/automod</div>
          <div class="cmd-desc">View real-time status of Anti-Spam, Anti-Invite, Anti-Phishing & Anti-Mention shields.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/automod_toggle</div>
          <div class="cmd-desc">Enable or disable specific AutoMod protection filters.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/antialt &lt;on|off&gt;</div>
          <div class="cmd-desc">Toggles salted IP fingerprinting and alt account detection.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/lockdown &lt;on|off&gt;</div>
          <div class="cmd-desc">Emergency raid freeze — quickly locks or unlocks channel chat permissions.</div>
        </div>
        <span class="badge badge-admin">Administrator</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/scan &lt;url&gt;</div>
          <div class="cmd-desc">Detonates and tests suspicious links in multi-node VPS Chromium sandboxes.</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
    </div>

    <!-- Moderation Section -->
    <div class="section-title">🔨 Moderation System</div>
    <div class="cmd-grid">
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/timeout &lt;@user&gt; &lt;time&gt;</div>
          <div class="cmd-desc">Applies Discord native timeout (e.g. 10m, 1h, 1d) restricting user interaction.</div>
        </div>
        <span class="badge badge-mod">Moderate Members</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/untimeout &lt;@user&gt;</div>
          <div class="cmd-desc">Lifts an active timeout from a member immediately.</div>
        </div>
        <span class="badge badge-mod">Moderate Members</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/warn &lt;@user&gt; &lt;reason&gt;</div>
          <div class="cmd-desc">Issues an official warning and records it in the server database.</div>
        </div>
        <span class="badge badge-mod">Manage Messages</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/warnings &lt;@user&gt;</div>
          <div class="cmd-desc">Displays comprehensive infraction history for a user.</div>
        </div>
        <span class="badge badge-mod">Manage Messages</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/purge &lt;amount&gt;</div>
          <div class="cmd-desc">Bulk deletes messages with optional user filter.</div>
        </div>
        <span class="badge badge-mod">Manage Messages</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/kick & /ban & /unban</div>
          <div class="cmd-desc">Member removal and ban management commands.</div>
        </div>
        <span class="badge badge-mod">Kick / Ban Members</span>
      </div>
    </div>

    <!-- Utilities Section -->
    <div class="section-title">📊 Info & Utilities</div>
    <div class="cmd-grid">
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/serverinfo</div>
          <div class="cmd-desc">Displays comprehensive statistics and telemetry for the current guild.</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/userinfo [@user]</div>
          <div class="cmd-desc">Detailed user profile (joined date, created date, roles, avatar).</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/avatar [@user]</div>
          <div class="cmd-desc">Fetches high-resolution profile picture with download link.</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
      <div class="cmd-card">
        <div>
          <div class="cmd-name">/botinfo & /ping</div>
          <div class="cmd-desc">Bot latency, RAM/CPU consumption, uptime, and system status.</div>
        </div>
        <span class="badge badge-user">Everyone</span>
      </div>
    </div>
  </div>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
