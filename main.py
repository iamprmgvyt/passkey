# -*- coding: utf-8 -*-
"""Passkey Bot & Web Portal — Dual Async Service Runner."""
import asyncio
import aiohttp
import uvicorn
import logging
from bot.core import bot
from dashboard.app import app
from utils.config import Config
from utils.logger import setup_logger

log = setup_logger()

async def run_bot():
    token = Config.BOT_TOKEN
    if not token or token == "YOUR_DISCORD_BOT_TOKEN":
        log.warning("BOT_TOKEN is not set in .env! Bot gateway will not start until configured.")
        return
    log.info("Starting Passkey Discord Bot Gateway...")
    await bot.start(token)

async def run_dashboard():
    log.info(f"Starting Passkey Web Dashboard on port {Config.DASHBOARD_PORT} (Base URL: {Config.DASHBOARD_URL})...")
    app.state.bot = bot
    config = uvicorn.Config(app=app, host="0.0.0.0", port=Config.DASHBOARD_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_render_keepalive():
    """Keepalive pinger to prevent Render free instances from idling."""
    await asyncio.sleep(30)
    url = Config.DASHBOARD_URL
    if not url or "localhost" in url or "127.0.0.1" in url:
        return

    health_url = f"{url}/health"
    log.info(f"Render keep-alive task started for: {health_url}")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    log.info(f"[KeepAlive] Health ping {health_url} -> Status {resp.status}")
        except Exception as e:
            log.warning(f"[KeepAlive] Ping failed: {e}")
        await asyncio.sleep(600)  # Ping every 10 minutes

async def main():
    await asyncio.gather(
        run_bot(),
        run_dashboard(),
        run_render_keepalive()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Passkey services shut down gracefully.")
