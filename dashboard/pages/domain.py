# -*- coding: utf-8 -*-
"""Passkey Dashboard — /domain Multi-Node Threat Sandbox & Custom Domain Portal."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dashboard.layout import FAVICON, FONTS, BASE_STYLE, NAV_BAR, FOOTER
from utils.scanner_manager import dispatch_url_scan, SCANNER_NODES

router = APIRouter(tags=["Domain"])

@router.get("/domain", response_class=HTMLResponse)
async def domain_page(request: Request):
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
  {FAVICON}{FONTS}
  <title>Cyber Threat Intelligence &amp; Sandbox Scanner — Passkey</title>
  {BASE_STYLE}
  <style>
    .page-wrap {{ max-width: 1080px; margin: 50px auto; padding: 0 20px; }}
    .scan-card {{
      padding: 36px 32px; border-radius: 20px; margin-bottom: 40px;
    }}
    .scan-input-group {{
      display: flex; gap: 12px; margin: 24px 0 16px; flex-wrap: wrap;
    }}
    .scan-input {{
      flex: 1; min-width: 280px; background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border);
      color: #fff; padding: 14px 18px; border-radius: 12px; font-family: var(--mono); font-size: 0.95rem;
      outline: none; transition: border-color 0.2s;
    }}
    .scan-input:focus {{ border-color: #818cf8; }}
    .btn-scan {{
      background: var(--gradient-btn); color: #fff; border: none; padding: 14px 28px;
      border-radius: 12px; font-weight: 800; font-size: 0.95rem; cursor: pointer;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4); transition: all 0.2s;
    }}
    .btn-scan:hover {{ transform: translateY(-1px); }}
    .result-box {{
      display: none; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border);
      padding: 24px; border-radius: 14px; font-family: var(--mono); font-size: 0.88rem;
      margin-top: 24px; line-height: 1.7;
    }}
  </style>
</head>
<body>
  {NAV_BAR}
  <main class="page-wrap">
    <div style="text-align:center;margin-bottom:44px;">
      <span class="badge-neon" style="margin-bottom:12px;">THREAT INTELLIGENCE</span>
      <h1 style="font-size:2.5rem;font-weight:900;margin:8px 0 12px;">Cloud Sandbox Threat Scanner</h1>
      <p style="color:var(--text-muted);font-size:1.05rem;max-width:650px;margin:0 auto;">
        Inspect suspicious URLs, fake Nitro links, and malicious domains before allowing members to click.
      </p>
    </div>

    <div class="glass-card scan-card">
      <h2 style="font-size:1.35rem;font-weight:800;margin:0 0 8px;color:#818cf8;">🔍 URL Security Inspection</h2>
      <p style="color:var(--text-muted);font-size:0.9rem;margin:0;">
        Enter any domain or link to analyze against our global phishing &amp; threat intelligence cluster:
      </p>

      <div class="scan-input-group">
        <input type="text" id="target-url" class="scan-input" placeholder="https://discord-nitro-free-gift.xyz/claim">
        <button class="btn-scan" onclick="runScan()">⚡ Scan Threat Now</button>
      </div>

      <div id="scan-result" class="result-box"></div>
    </div>
  </main>
  {FOOTER}
  <script>
    async function runScan() {{
      const url = document.getElementById('target-url').value.trim();
      const resBox = document.getElementById('scan-result');
      if (!url) return;
      resBox.style.display = 'block';
      resBox.innerHTML = '<span style="color:#38bdf8;">🔄 Dispatching isolated sandbox container to inspect threat payload...</span>';
      try {{
        const res = await fetch('/api/scan?url=' + encodeURIComponent(url));
        const d = await res.json();
        const isThreat = (d.status === 'threat');
        resBox.innerHTML = 
          '<div><strong>Target URL:</strong> ' + d.url + '</div>' +
          '<div><strong>Security Verdict:</strong> <span style="font-weight:800;color:' + (isThreat ? '#f43f5e' : '#10b981') + '">' + d.verdict + '</span></div>' +
          '<div><strong>Cluster Node:</strong> ' + d.node_name + ' (' + d.latency + ')</div>' +
          '<div><strong>DOM Inspection:</strong> ' + d.dom_inspection + '</div>';
      }} catch (e) {{
        resBox.innerHTML = '<span style="color:#f43f5e;">❌ Failed to connect to sandbox cluster.</span>';
      }}
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(html)

@router.get("/api/scan")
async def api_scan(url: str = ""):
    return await dispatch_url_scan(url)
