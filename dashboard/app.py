# -*- coding: utf-8 -*-
"""Passkey Dashboard — FastAPI Application Entrypoint."""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("passkey.dashboard")

app = FastAPI(title="Passkey Gateway", docs_url=None, redoc_url=None)

class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

app.add_middleware(HeaderMiddleware)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

PAGE_MODULE_ROUTERS = [
    ("dashboard.manage", "manage_router"),
    ("dashboard.pages.landing", "router"),
    ("dashboard.pages.verify", "router"),
    ("dashboard.pages.domain", "router"),
    ("dashboard.pages.commands", "router"),
    ("dashboard.pages.stats", "router"),
    ("dashboard.pages.api", "router"),
    ("dashboard.pages.tos", "router"),
    ("dashboard.pages.privacy", "router"),
]

for mod_name, router_attr in PAGE_MODULE_ROUTERS:
    try:
        import importlib
        m = importlib.import_module(mod_name)
        r = getattr(m, router_attr)
        app.include_router(r)
        log.info(f"Registered router: {mod_name}")
    except Exception as e:
        log.error(f"Failed to register router {mod_name}: {e}")

def reload_dashboard() -> dict:
    import importlib, sys
    count = 0
    for mod_name, _ in PAGE_MODULE_ROUTERS:
        if mod_name in sys.modules:
            try:
                importlib.reload(sys.modules[mod_name])
                count += 1
            except Exception:
                pass
    return {"ok": True, "reloaded_count": count}
