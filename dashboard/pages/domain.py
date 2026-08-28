# -*- coding: utf-8 -*-
"""Passkey Dashboard — /domain Multi-Node Threat Scanner Portal."""
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
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  {FAVICON}{FONTS}
  <title>Passkey — Threat Intelligence Sandbox</title>
  {BASE_STYLE}
  <style>
    .container {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
    .scan-box {{
      background: var(--card); border: 1px solid var(--border); border-radius: 16px;
      padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}
    .scan-input-group {{
      display: flex; gap: 10px; margin: 20px 0;
    }}
    .scan-input {{
      flex: 1; background: #090b10; border: 1px solid var(--border); color: #fff;
      padding: 14px 18px; border-radius: 10px; font-family: var(--mono); font-size: 0.9rem;
    }}
    .btn-scan {{
      background: var(--indigo); color: #fff; border: none; padding: 14px 28px;
      border-radius: 10px; font-weight: 800; cursor: pointer;
    }}
  </style>
</head>
<body>
  {NAV_BAR}
  <div class="container">
    <div class="scan-box">
      <h1 style="font-size:1.8rem;font-weight:900;margin-top:0;">Multi-Node Cloud Sandbox Scanner</h1>
      <p style="color:var(--text-muted);font-size:0.92rem;">
        Detonate and analyze suspicious URLs across isolated Chromium containers in VN-SG and US-VA clusters.
      </p>

      <div class="scan-input-group">
        <input type="text" id="target-url" class="scan-input" placeholder="https://example-nitro-gift.xyz/claim">
        <button class="btn-scan" onclick="runScan()">Scan Threat</button>
      </div>

      <div id="scan-result" style="display:none;background:#090b10;padding:20px;border-radius:10px;font-family:var(--mono);font-size:0.85rem;margin-top:20px;"></div>
    </div>
  </div>
  {FOOTER}
  <script>
    async function runScan() {{
      const url = document.getElementById('target-url').value.trim();
      const resBox = document.getElementById('scan-result');
      if (!url) return;
      resBox.style.display = 'block';
      resBox.innerHTML = '🔄 Dispatching sandbox container to VN-SG node...';
      try {{
        const res = await fetch('/api/scan?url=' + encodeURIComponent(url));
        const d = await res.json();
        resBox.innerHTML = '<strong>Target:</strong> ' + d.url + '<br>' +
          '<strong>Verdict:</strong> <span style="color:' + (d.status === 'threat' ? '#f43f5e' : '#10b981') + '">' + d.verdict + '</span><br>' +
          '<strong>Node:</strong> ' + d.node_name + ' (' + d.latency + ')<br>' +
          '<strong>Inspection:</strong> ' + d.dom_inspection;
      }} catch (e) {{
        resBox.innerHTML = '❌ Scan error connecting to cluster.';
      }}
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(html)

@router.get("/api/scan")
async def api_scan(url: str = ""):
    return await dispatch_url_scan(url)
