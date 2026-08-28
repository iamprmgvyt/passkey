# -*- coding: utf-8 -*-
"""Passkey Dashboard — Enterprise Terms of Service & Privacy Policy."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

router = APIRouter(tags=["Legal"])

@router.get("/tos", response_class=HTMLResponse)
@router.get("/terms", response_class=HTMLResponse)
async def tos_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Terms of Service — Passkey Gatekeeper</title>
  {BASE_STYLE}
  <style>
    .legal-wrap {{ max-width: 860px; margin: 50px auto; padding: 0 20px; }}
    .legal-card {{ padding: 40px; border-radius: 20px; }}
    .legal-section {{ margin-bottom: 28px; }}
    .legal-section h2 {{ font-size: 1.3rem; font-weight: 800; color: #818cf8; margin-bottom: 8px; }}
    .legal-section p {{ color: var(--text-muted); font-size: 0.95rem; line-height: 1.7; margin: 0; }}
  </style>
</head>
<body>
  {NAV_BAR}
  <main class="legal-wrap">
    <div style="text-align:center;margin-bottom:36px;">
      <span class="badge-neon" style="margin-bottom:12px;">LEGAL AGREEMENT</span>
      <h1 style="font-size:2.5rem;font-weight:900;margin:8px 0 8px;">Terms of Service</h1>
      <p style="color:var(--text-dim);font-size:0.9rem;">Last Updated: August 2026</p>
    </div>

    <div class="glass-card legal-card">
      <div class="legal-section">
        <h2>1. Acceptance of Terms</h2>
        <p>By inviting Passkey Bot to your Discord server or using the Passkey Web Verification Gateway, you acknowledge that you have read, understood, and agree to be bound by these Terms and Discord's Developer Terms of Service.</p>
      </div>

      <div class="legal-section">
        <h2>2. Service Usage & Fair Play</h2>
        <p>Passkey provides automated verification, anti-raid protection, anti-alt detection, and moderation tooling. Users must not attempt to reverse-engineer, exploit, DDoS, or bypass security mechanisms implemented by the service.</p>
      </div>

      <div class="legal-section">
        <h2>3. Server Administrator Responsibilities</h2>
        <p>Server administrators are solely responsible for configuring verification penalties, quarantine policies, and moderation actions. Passkey operates as an autonomous enforcement tool under administrator guidelines.</p>
      </div>

      <div class="legal-section">
        <h2>4. Availability & SLA</h2>
        <p>We strive to maintain a 99.9% uptime SLA across our cloud infrastructure. However, services are provided on an "as is" and "as available" basis without warranties of any kind.</p>
      </div>
    </div>
  </main>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Privacy Policy — Passkey Gatekeeper</title>
  {BASE_STYLE}
  <style>
    .legal-wrap {{ max-width: 860px; margin: 50px auto; padding: 0 20px; }}
    .legal-card {{ padding: 40px; border-radius: 20px; }}
    .legal-section {{ margin-bottom: 28px; }}
    .legal-section h2 {{ font-size: 1.3rem; font-weight: 800; color: #38bdf8; margin-bottom: 8px; }}
    .legal-section p {{ color: var(--text-muted); font-size: 0.95rem; line-height: 1.7; margin: 0; }}
  </style>
</head>
<body>
  {NAV_BAR}
  <main class="legal-wrap">
    <div style="text-align:center;margin-bottom:36px;">
      <span class="badge-neon" style="margin-bottom:12px;">DATA PROTECTION</span>
      <h1 style="font-size:2.5rem;font-weight:900;margin:8px 0 8px;">Privacy Policy</h1>
      <p style="color:var(--text-dim);font-size:0.9rem;">Last Updated: August 2026</p>
    </div>

    <div class="glass-card legal-card">
      <div class="legal-section">
        <h2>1. Information We Collect</h2>
        <p>We only collect data strictly necessary for verification and defense: Discord User IDs, Server Guild IDs, one-time verification tokens, and anonymized cryptographic hashes for anti-alt detection.</p>
      </div>

      <div class="legal-section">
        <h2>2. Zero Data Selling</h2>
        <p>Passkey never sells, rents, or monetizes user data. All verification sessions are self-expiring and automatically purged from memory after 10 minutes.</p>
      </div>

      <div class="legal-section">
        <h2>3. Email Address Privacy</h2>
        <p>Email addresses entered during Email OTP verification are used solely to transmit the 6-digit one-time code and are never shared with third parties.</p>
      </div>

      <div class="legal-section">
        <h2>4. Cloud Security & Encryption</h2>
        <p>All database records are securely stored on Turso Cloud LibSQL with TLS 1.3 encryption in transit and at rest.</p>
      </div>
    </div>
  </main>
  {FOOTER}
</body>
</html>"""
    return HTMLResponse(html)
