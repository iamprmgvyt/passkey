# -*- coding: utf-8 -*-
"""Passkey Dashboard — REST APIs & Health Checks."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["API"])

@router.get("/health")
@router.get("/api/health")
async def health_check(request: Request):
    """Health check endpoint for Render to keep the web service active."""
    bot = getattr(request.app.state, "bot", None)
    is_ready = bool(bot and bot.is_ready())
    return JSONResponse(
        content={
            "status": "healthy",
            "bot_ready": is_ready,
            "service": "Passkey Security & Gatekeeper"
        }
    )

@router.get("/api/summary")
async def api_summary(request: Request):
    bot = getattr(request.app.state, "bot", None)
    guild_count = len(bot.guilds) if bot and bot.is_ready() else 0
    user_count = sum(g.member_count or 0 for g in bot.guilds) if bot and bot.is_ready() else 0

    headers = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}
    return JSONResponse(
        content={
            "status": "online",
            "bot_name": "Passkey",
            "servers": guild_count,
            "users": user_count
        },
        headers=headers
    )
