# -*- coding: utf-8 -*-
"""Passkey Dashboard — Terms of Service."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER

router = APIRouter(tags=["Legal"])

@router.get("/tos", response_class=HTMLResponse)
async def tos_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}<title>Passkey — Terms of Service</title>{BASE_STYLE}
</head>
<body>
  {NAV_BAR}
  <div style="max-width:800px;margin:40px auto;padding:0 24px;">
    <h1>Terms of Service</h1>
    <p style="color:var(--text-muted);">By using Passkey Bot and Web Verification services, you agree to our fair use policy and Discord's Terms of Service.</p>
  </div>
  {FOOTER}
</body></html>"""
    return HTMLResponse(html)

@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}<title>Passkey — Privacy Policy</title>{BASE_STYLE}
</head>
<body>
  {NAV_BAR}
  <div style="max-width:800px;margin:40px auto;padding:0 24px;">
    <h1>Privacy Policy</h1>
    <p style="color:var(--text-muted);">Passkey does not sell personal user data. Session tokens are one-time and self-expiring upon verification completion.</p>
  </div>
  {FOOTER}
</body></html>"""
    return HTMLResponse(html)
