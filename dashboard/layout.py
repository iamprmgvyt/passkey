# -*- coding: utf-8 -*-
"""Passkey Dashboard — Global Layout, Custom SVG Icons & Theme System."""

FAVICON = '<link rel="icon" type="image/png" href="/static/passkey.png">'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">'

BASE_STYLE = """
<style>
:root {
  --bg: #090b10;
  --card: #12141e;
  --card-hover: #181a27;
  --border: rgba(255, 255, 255, 0.08);
  --indigo: #6366f1;
  --emerald: #10b981;
  --amber: #f59e0b;
  --rose: #f43f5e;
  --cyan: #06b6d4;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --mono: 'JetBrains Mono', monospace;
  --display: 'Plus Jakarta Sans', sans-serif;
}

[data-theme="light"] {
  --bg: #f8fafc;
  --card: #ffffff;
  --card-hover: #f1f5f9;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #334155;
  --text-dim: #64748b;
}

[data-theme="light"] body,
[data-theme="light"] html {
  background: #f8fafc !important;
  color: #0f172a !important;
}

* { box-sizing: border-box; }
body {
  margin: 0; padding: 0;
  font-family: var(--display);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  max-width: 1140px;
  margin: 0 auto;
  border-bottom: 1px solid var(--border);
}
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text);
  font-weight: 800;
  font-size: 1.15rem;
}
.nav-brand img {
  width: 32px; height: 32px; border-radius: 8px;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
}
.nav-links a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  transition: color 0.2s;
}
.nav-links a:hover { color: var(--text); }
.nav-btn {
  background: var(--indigo);
  color: #fff !important;
  padding: 8px 18px;
  border-radius: 8px;
  font-weight: 700 !important;
}
.theme-toggle-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
}
</style>
"""

NAV_BAR = """
<header class="nav-bar">
  <a href="/" class="nav-brand">
    <img src="/static/passkey.png" alt="Passkey Logo" onerror="this.src='/static/aegix.png'">
    <span>PASSKEY</span>
  </a>
  <div class="nav-links">
    <a href="/domain">Threat Scanner</a>
    <a href="/commands">Commands</a>
    <a href="/stats">Live Stats</a>
    <a href="/manage">Manage</a>
    <button type="button" class="theme-toggle-btn" onclick="toggleTheme()" id="theme-btn">🌓 Theme</button>
    <a href="https://discord.com/oauth2/authorize?client_id=1399740322883567646&permissions=1395293285622&integration_type=0&scope=bot+applications.commands" target="_blank" class="nav-btn">+ Add Bot</a>
  </div>
</header>
<script>
  function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('pk_theme', next);
  }
  (function() {
    const saved = localStorage.getItem('pk_theme');
    if (saved) document.documentElement.setAttribute('data-theme', saved);
  })();
</script>
"""

FOOTER = """
<footer style="border-top:1px solid var(--border);padding:36px 24px;text-align:center;color:var(--text-muted);font-size:0.85rem;max-width:1140px;margin:0 auto;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
    <div><strong>PASSKEY</strong> &bull; Next-Gen Discord Verification &amp; Web Security</div>
    <div style="display:flex;gap:18px;">
      <a href="/tos" style="color:var(--text-muted);text-decoration:none;">Terms</a>
      <a href="/privacy" style="color:var(--text-muted);text-decoration:none;">Privacy</a>
      <a href="/stats" style="color:var(--text-muted);text-decoration:none;">Stats</a>
      <a href="/domain" style="color:var(--text-muted);text-decoration:none;">Threat Scanner</a>
    </div>
  </div>
</footer>
"""
