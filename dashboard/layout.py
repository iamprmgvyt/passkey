# -*- coding: utf-8 -*-
"""Passkey Dashboard — Global Layout, Custom Neon Aesthetic & Theme System."""

FAVICON = '<link rel="icon" type="image/png" href="/static/passkey.png">'
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600;700;800&display=swap" rel="stylesheet">'

BASE_STYLE = """
<style>
:root {
  --bg: #07090e;
  --bg-gradient: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.18) 0%, rgba(7, 9, 14, 1) 75%);
  --card: rgba(18, 22, 34, 0.78);
  --card-hover: rgba(28, 33, 50, 0.95);
  --card-solid: #111420;
  --border: rgba(255, 255, 255, 0.09);
  --border-glow: rgba(99, 102, 241, 0.45);
  --indigo: #6366f1;
  --purple: #a855f7;
  --cyan: #06b6d4;
  --emerald: #10b981;
  --amber: #f59e0b;
  --rose: #f43f5e;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --mono: 'JetBrains Mono', monospace;
  --display: 'Plus Jakarta Sans', sans-serif;
  --gradient-neon: linear-gradient(135deg, #a855f7 0%, #6366f1 50%, #06b6d4 100%);
  --gradient-btn: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #06b6d4 100%);
}

[data-theme="light"] {
  --bg: #f8fafc;
  --bg-gradient: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.08) 0%, rgba(248, 250, 252, 1) 75%);
  --card: rgba(255, 255, 255, 0.92);
  --card-hover: #ffffff;
  --card-solid: #ffffff;
  --border: #e2e8f0;
  --border-glow: rgba(99, 102, 241, 0.3);
  --text: #0f172a;
  --text-muted: #475569;
  --text-dim: #64748b;
}

* { box-sizing: border-box; }
body, html {
  margin: 0; padding: 0;
  font-family: var(--display);
  background: var(--bg);
  background-image: var(--bg-gradient);
  background-attachment: fixed;
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}

a { color: var(--indigo); text-decoration: none; transition: all 0.2s; }
a:hover { color: var(--cyan); }

/* Custom Neon Passkey Emojis Styling */
.emoji-icon {
  width: 22px; height: 22px; vertical-align: -4px; border-radius: 6px;
  display: inline-block; object-fit: cover;
}
.emoji-icon-md {
  width: 32px; height: 32px; vertical-align: -6px; border-radius: 8px;
  display: inline-block; object-fit: cover;
}
.emoji-icon-lg {
  width: 52px; height: 52px; border-radius: 14px; display: inline-block; object-fit: cover;
  border: 1px solid rgba(168, 85, 247, 0.35); box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 28px;
  max-width: 1200px;
  margin: 0 auto;
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--text);
  font-weight: 900;
  font-size: 1.25rem;
  letter-spacing: -0.5px;
}
.nav-brand img {
  width: 36px; height: 36px; border-radius: 10px;
  border: 1px solid rgba(168, 85, 247, 0.3);
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.25);
}
.nav-brand span {
  background: var(--gradient-neon);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 22px;
}
.nav-links a {
  color: var(--text-muted);
  font-size: 0.92rem;
  font-weight: 600;
}
.nav-links a:hover { color: var(--text); }
.nav-btn {
  background: var(--gradient-btn) !important;
  color: #fff !important;
  padding: 10px 20px !important;
  border-radius: 10px;
  font-weight: 800 !important;
  font-size: 0.9rem !important;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.nav-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5);
}
.theme-toggle-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s;
}
.theme-toggle-btn:hover {
  background: rgba(255,255,255,0.12);
}

.badge-neon {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  border-radius: 9999px;
  font-size: 0.76rem;
  font-weight: 800;
  font-family: var(--mono);
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.35);
  color: #818cf8;
}

.glass-card {
  background: var(--card);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border);
  border-radius: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-card:hover {
  border-color: var(--border-glow);
  background: var(--card-hover);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.35);
}

@media (max-width: 768px) {
  .nav-bar { padding: 14px 18px; }
  .nav-links { gap: 12px; }
  .nav-links a:not(.nav-btn):not(#theme-btn) { display: none; }
}
</style>
"""

NAV_BAR = """
<header class="nav-bar">
  <a href="/" class="nav-brand">
    <img src="/static/emojis/passkey.png" alt="Passkey Logo">
    <span>PASSKEY</span>
  </a>
  <div class="nav-links">
    <a href="/commands"><img src="/static/emojis/shield.png" class="emoji-icon" alt=""> Commands</a>
    <a href="/domain"><img src="/static/emojis/warn.png" class="emoji-icon" alt=""> Threat Scanner</a>
    <a href="/stats"><img src="/static/emojis/verified.png" class="emoji-icon" alt=""> Telemetry</a>
    <a href="/manage"><img src="/static/emojis/lock.png" class="emoji-icon" alt=""> Dashboard</a>
    <button type="button" class="theme-toggle-btn" onclick="toggleTheme()" id="theme-btn">🌓 Theme</button>
    <a href="https://discord.com/oauth2/authorize?client_id=1452522495965134908&permissions=1395293285622&integration_type=0&scope=bot+applications.commands" target="_blank" class="nav-btn">
      <img src="/static/emojis/passkey.png" style="width:20px;height:20px;border-radius:4px;" alt="">
      <span>Add to Discord</span>
    </a>
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
<footer style="border-top:1px solid var(--border);padding:48px 24px 36px;color:var(--text-muted);font-size:0.88rem;max-width:1200px;margin:60px auto 0;">
  <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:32px;margin-bottom:40px;">
    <div>
      <div style="display:flex;align-items:center;gap:10px;font-weight:900;font-size:1.1rem;color:var(--text);margin-bottom:12px;">
        <img src="/static/emojis/passkey.png" alt="Logo" style="width:28px;height:28px;border-radius:8px;">
        <span>PASSKEY GATEKEEPER</span>
      </div>
      <p style="font-size:0.84rem;color:var(--text-dim);line-height:1.6;">
        Next-Generation Zero-Trust Discord Gatekeeper. Cloudflare Turnstile, WebAuthn Biometrics, Email OTP, and Deep Neural Anti-Alt Defenses.
      </p>
    </div>
    <div>
      <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:0.9rem;">GATEKEEPER</div>
      <div style="display:flex;flex-direction:column;gap:8px;font-size:0.85rem;">
        <a href="/commands"><img src="/static/emojis/shield.png" class="emoji-icon" alt=""> Slash Commands</a>
        <a href="/stats"><img src="/static/emojis/verified.png" class="emoji-icon" alt=""> Global Telemetry</a>
        <a href="/domain"><img src="/static/emojis/warn.png" class="emoji-icon" alt=""> Threat Scanner</a>
        <a href="/manage"><img src="/static/emojis/lock.png" class="emoji-icon" alt=""> Server Dashboard</a>
      </div>
    </div>
    <div>
      <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:0.9rem;">RESOURCES</div>
      <div style="display:flex;flex-direction:column;gap:8px;font-size:0.85rem;">
        <a href="https://discord.com/oauth2/authorize?client_id=1452522495965134908&permissions=1395293285622&integration_type=0&scope=bot+applications.commands" target="_blank"><img src="/static/emojis/passkey.png" class="emoji-icon" alt=""> Invite Bot</a>
        <a href="https://passkey-verify.onrender.com/verify"><img src="/static/emojis/verified.png" class="emoji-icon" alt=""> Verification Gateway</a>
        <a href="/tos">Terms of Service</a>
        <a href="/privacy">Privacy Policy</a>
      </div>
    </div>
    <div>
      <div style="font-weight:800;color:var(--text);margin-bottom:12px;font-size:0.9rem;">INFRASTRUCTURE</div>
      <div style="font-size:0.84rem;color:var(--text-dim);line-height:1.7;">
        <div>Cloud Engine: <strong>Tokyo AWS Cluster</strong></div>
        <div>Database: <strong>Turso Cloud LibSQL</strong></div>
        <div>SMTP Carrier: <strong>Zoho Mail Enterprise</strong></div>
        <div>Bot SLA: <strong>99.98% High-Availability</strong></div>
      </div>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;padding-top:24px;border-top:1px solid var(--border);font-size:0.8rem;color:var(--text-dim);">
    <div>&copy; 2026 Passkey Security. All rights reserved.</div>
    <div style="display:flex;gap:20px;">
      <a href="/tos" style="color:var(--text-dim);">Terms</a>
      <a href="/privacy" style="color:var(--text-dim);">Privacy</a>
      <a href="/stats" style="color:var(--text-dim);">Telemetry</a>
    </div>
  </div>
</footer>
"""
