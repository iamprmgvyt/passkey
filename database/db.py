# -*- coding: utf-8 -*-
"""
Passkey Bot — Database Management.
Supports:
- Turso Cloud SQLite (LibSQL over HTTPS) with 10GB free cloud storage.
- Local SQLite3 fallback when Turso is not configured.
- Email verification logging & Anti-Alt detection via IP and Email.
- Multi-language setting per server ('vi', 'en').
"""
import os
import json
import sqlite3
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from utils.config import Config

log = logging.getLogger("passkey.db")

class Database:
    def __init__(self, db_url: str = ""):
        self.db_path = "passkey.db"
        self.turso_url = Config.TURSO_DATABASE_URL.strip()
        self.turso_token = Config.TURSO_AUTH_TOKEN.strip()
        
        # Convert libsql:// to https:// for reliable HTTP protocol
        if self.turso_url.startswith("libsql://"):
            self.turso_url = "https://" + self.turso_url[len("libsql://"):]

        self.use_turso = bool(self.turso_url and self.turso_token)
        self.turso_client = None
        self.sqlite_conn = None

    async def connect(self):
        if self.use_turso:
            try:
                import libsql_client
                self.turso_client = libsql_client.create_client(
                    url=self.turso_url,
                    auth_token=self.turso_token
                )
                await self._init_turso_tables()
                log.info(f"Connected to Turso Cloud SQLite: {self.turso_url}")
                return
            except Exception as e:
                log.error(f"Failed to connect to Turso Cloud ({e}). Falling back to local SQLite.")
                self.use_turso = False

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._init_sqlite)
        log.info("Passkey local SQLite database initialized successfully.")

    async def _init_turso_tables(self):
        tables = [
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id TEXT PRIMARY KEY,
                verified_role_id TEXT,
                verify_channel_id TEXT,
                log_channel_id TEXT,
                verify_mode TEXT DEFAULT 'web',
                language TEXT DEFAULT 'en',
                antialt_enabled INTEGER DEFAULT 1,
                min_age_days INTEGER DEFAULT 0,
                automod_spam INTEGER DEFAULT 1,
                automod_invites INTEGER DEFAULT 1,
                automod_phishing INTEGER DEFAULT 1,
                automod_mentions INTEGER DEFAULT 1,
                allowed_email_domains TEXT DEFAULT '',
                config_json TEXT DEFAULT '{}'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                verified_at REAL,
                ip_hash TEXT,
                email TEXT DEFAULT '',
                method TEXT DEFAULT 'web',
                status TEXT DEFAULT 'verified'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                moderator_id TEXT,
                reason TEXT,
                timestamp REAL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS global_stats (
                key TEXT PRIMARY KEY,
                val INTEGER DEFAULT 0
            )
            """
        ]
        for query in tables:
            try:
                await self.turso_client.execute(query)
            except Exception:
                pass

    def _init_sqlite(self):
        self.sqlite_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row
        cur = self.sqlite_conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id TEXT PRIMARY KEY,
            verified_role_id TEXT,
            verify_channel_id TEXT,
            log_channel_id TEXT,
            verify_mode TEXT DEFAULT 'web',
            language TEXT DEFAULT 'en',
            antialt_enabled INTEGER DEFAULT 1,
            min_age_days INTEGER DEFAULT 0,
            automod_spam INTEGER DEFAULT 1,
            automod_invites INTEGER DEFAULT 1,
            automod_phishing INTEGER DEFAULT 1,
            automod_mentions INTEGER DEFAULT 1,
            allowed_email_domains TEXT DEFAULT '',
            config_json TEXT DEFAULT '{}'
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS verification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            verified_at REAL,
            ip_hash TEXT,
            email TEXT DEFAULT '',
            method TEXT DEFAULT 'web',
            status TEXT DEFAULT 'verified'
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            moderator_id TEXT,
            reason TEXT,
            timestamp REAL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS global_stats (
            key TEXT PRIMARY KEY,
            val INTEGER DEFAULT 0
        )
        """)
        self.sqlite_conn.commit()

    # --- Guild Configuration ---

    async def get_guild_config(self, guild_id: int) -> dict:
        default_cfg = {
            "guild_id": str(guild_id),
            "verify_mode": "web",
            "language": "en",
            "antialt_enabled": 1,
            "antialt_action": "quarantine",  # log, quarantine, kick, ban, ignore
            "min_age_days": 0,
            "automod_spam": 1,
            "automod_invites": 1,
            "automod_phishing": 1,
            "automod_mentions": 1,
            "allowed_email_domains": ""
        }

        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "SELECT * FROM guild_settings WHERE guild_id = ?",
                    [str(guild_id)]
                )
                if not res.rows:
                    return default_cfg
                row_dict = dict(zip(res.columns, res.rows[0]))
                try:
                    row_dict.update(json.loads(row_dict.get("config_json") or "{}"))
                except Exception:
                    pass
                return row_dict
            except Exception as e:
                log.error(f"Turso error in get_guild_config: {e}")
                return default_cfg

        def _get():
            cur = self.sqlite_conn.cursor()
            cur.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
            row = cur.fetchone()
            if not row:
                return default_cfg
            cfg = dict(row)
            try:
                cfg.update(json.loads(cfg.get("config_json") or "{}"))
            except Exception:
                pass
            return cfg

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)

    async def set_guild_config(self, guild_id: int, key: str, value: Any):
        direct_cols = [
            "verified_role_id", "verify_channel_id", "log_channel_id",
            "verify_mode", "language", "antialt_enabled", "antialt_action", "min_age_days",
            "automod_spam", "automod_invites", "automod_phishing", "automod_mentions",
            "allowed_email_domains"
        ]

        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "SELECT * FROM guild_settings WHERE guild_id = ?",
                    [str(guild_id)]
                )
                cfg_dict = {}
                if res.rows:
                    row_dict = dict(zip(res.columns, res.rows[0]))
                    try:
                        cfg_dict = json.loads(row_dict.get("config_json") or "{}")
                    except Exception:
                        pass
                cfg_dict[key] = value

                if res.rows:
                    if key in direct_cols:
                        await self.turso_client.execute(
                            f"UPDATE guild_settings SET {key} = ?, config_json = ? WHERE guild_id = ?",
                            [value, json.dumps(cfg_dict), str(guild_id)]
                        )
                    else:
                        await self.turso_client.execute(
                            "UPDATE guild_settings SET config_json = ? WHERE guild_id = ?",
                            [json.dumps(cfg_dict), str(guild_id)]
                        )
                else:
                    if key in direct_cols:
                        await self.turso_client.execute(
                            f"INSERT INTO guild_settings (guild_id, {key}, config_json) VALUES (?, ?, ?)",
                            [str(guild_id), value, json.dumps(cfg_dict)]
                        )
                    else:
                        await self.turso_client.execute(
                            "INSERT INTO guild_settings (guild_id, config_json) VALUES (?, ?)",
                            [str(guild_id), json.dumps(cfg_dict)]
                        )
                return
            except Exception as e:
                log.error(f"Turso error in set_guild_config: {e}")

        def _set():
            cur = self.sqlite_conn.cursor()
            cur.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (str(guild_id),))
            row = cur.fetchone()
            
            cfg_dict = {}
            if row and row["config_json"]:
                try:
                    cfg_dict = json.loads(row["config_json"])
                except Exception:
                    pass
            cfg_dict[key] = value

            if row:
                if key in direct_cols:
                    cur.execute(f"UPDATE guild_settings SET {key} = ?, config_json = ? WHERE guild_id = ?", 
                                (value, json.dumps(cfg_dict), str(guild_id)))
                else:
                    cur.execute("UPDATE guild_settings SET config_json = ? WHERE guild_id = ?", 
                                (json.dumps(cfg_dict), str(guild_id)))
            else:
                if key in direct_cols:
                    cur.execute(f"INSERT INTO guild_settings (guild_id, {key}, config_json) VALUES (?, ?, ?)", 
                                (str(guild_id), value, json.dumps(cfg_dict)))
                else:
                    cur.execute("INSERT INTO guild_settings (guild_id, config_json) VALUES (?, ?)", 
                                (str(guild_id), json.dumps(cfg_dict)))
            self.sqlite_conn.commit()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _set)

    # --- Verification logs & Anti-Alt ---

    async def log_verification(self, guild_id: int, user_id: int, ip_hash: str = "", method: str = "web", email: str = ""):
        if self.use_turso:
            try:
                await self.turso_client.execute(
                    "INSERT INTO verification_logs (guild_id, user_id, verified_at, ip_hash, email, method, status) VALUES (?, ?, ?, ?, ?, ?, 'verified')",
                    [str(guild_id), str(user_id), time.time(), ip_hash, email.lower().strip(), method]
                )
                await self.turso_client.execute(
                    "INSERT INTO global_stats (key, val) VALUES ('total_verifications', 1) ON CONFLICT(key) DO UPDATE SET val = val + 1"
                )
                return
            except Exception as e:
                log.error(f"Turso error in log_verification: {e}")

        def _log():
            cur = self.sqlite_conn.cursor()
            cur.execute("""
            INSERT INTO verification_logs (guild_id, user_id, verified_at, ip_hash, email, method, status)
            VALUES (?, ?, ?, ?, ?, ?, 'verified')
            """, (str(guild_id), str(user_id), time.time(), ip_hash, email.lower().strip(), method))
            cur.execute("""
            INSERT INTO global_stats (key, val) VALUES ('total_verifications', 1)
            ON CONFLICT(key) DO UPDATE SET val = val + 1
            """)
            self.sqlite_conn.commit()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _log)

    async def check_alt_ip(self, guild_id: int, user_id: int, ip_hash: str) -> Optional[str]:
        if not ip_hash:
            return None

        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "SELECT user_id FROM verification_logs WHERE guild_id = ? AND ip_hash = ? AND user_id != ? ORDER BY id DESC LIMIT 1",
                    [str(guild_id), ip_hash, str(user_id)]
                )
                if res.rows:
                    return str(res.rows[0][0])
                return None
            except Exception as e:
                log.error(f"Turso error in check_alt_ip: {e}")
                return None

        def _check():
            cur = self.sqlite_conn.cursor()
            cur.execute("""
            SELECT user_id FROM verification_logs 
            WHERE guild_id = ? AND ip_hash = ? AND user_id != ? 
            ORDER BY id DESC LIMIT 1
            """, (str(guild_id), ip_hash, str(user_id)))
            row = cur.fetchone()
            return row["user_id"] if row else None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _check)

    async def check_alt_email(self, guild_id: int, user_id: int, email: str) -> Optional[str]:
        if not email:
            return None
        clean_email = email.lower().strip()

        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "SELECT user_id FROM verification_logs WHERE guild_id = ? AND email = ? AND user_id != ? ORDER BY id DESC LIMIT 1",
                    [str(guild_id), clean_email, str(user_id)]
                )
                if res.rows:
                    return str(res.rows[0][0])
                return None
            except Exception as e:
                log.error(f"Turso error in check_alt_email: {e}")
                return None

        def _check():
            cur = self.sqlite_conn.cursor()
            cur.execute("""
            SELECT user_id FROM verification_logs 
            WHERE guild_id = ? AND email = ? AND user_id != ? 
            ORDER BY id DESC LIMIT 1
            """, (str(guild_id), clean_email, str(user_id)))
            row = cur.fetchone()
            return row["user_id"] if row else None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _check)

    # --- Warnings system ---

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                    [str(guild_id), str(user_id), str(moderator_id), reason, time.time()]
                )
                await self.turso_client.execute(
                    "INSERT INTO global_stats (key, val) VALUES ('total_warnings', 1) ON CONFLICT(key) DO UPDATE SET val = val + 1"
                )
                return getattr(res, "last_insert_rowid", 1) or 1
            except Exception as e:
                log.error(f"Turso error in add_warning: {e}")
                return 1

        def _add():
            cur = self.sqlite_conn.cursor()
            cur.execute("""
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """, (str(guild_id), str(user_id), str(moderator_id), reason, time.time()))
            cur.execute("""
            INSERT INTO global_stats (key, val) VALUES ('total_warnings', 1)
            ON CONFLICT(key) DO UPDATE SET val = val + 1
            """)
            self.sqlite_conn.commit()
            return cur.lastrowid

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _add)

    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "SELECT id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id ASC",
                    [str(guild_id), str(user_id)]
                )
                return [dict(zip(res.columns, row)) for row in res.rows]
            except Exception as e:
                log.error(f"Turso error in get_warnings: {e}")
                return []

        def _get():
            cur = self.sqlite_conn.cursor()
            cur.execute("""
            SELECT id, moderator_id, reason, timestamp FROM warnings
            WHERE guild_id = ? AND user_id = ?
            ORDER BY id ASC
            """, (str(guild_id), str(user_id)))
            return [dict(r) for r in cur.fetchall()]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get)

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
                    [str(guild_id), str(user_id)]
                )
                return getattr(res, "rows_affected", 0) or 0
            except Exception as e:
                log.error(f"Turso error in clear_warnings: {e}")
                return 0

        def _clear():
            cur = self.sqlite_conn.cursor()
            cur.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id)))
            deleted = cur.rowcount
            self.sqlite_conn.commit()
            return deleted

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _clear)

    async def delete_warning(self, warn_id: int, guild_id: int) -> bool:
        if self.use_turso:
            try:
                res = await self.turso_client.execute(
                    "DELETE FROM warnings WHERE id = ? AND guild_id = ?",
                    [warn_id, str(guild_id)]
                )
                return (getattr(res, "rows_affected", 0) or 0) > 0
            except Exception as e:
                log.error(f"Turso error in delete_warning: {e}")
                return False

        def _del():
            cur = self.sqlite_conn.cursor()
            cur.execute("DELETE FROM warnings WHERE id = ? AND guild_id = ?", (warn_id, str(guild_id)))
            deleted = cur.rowcount > 0
            self.sqlite_conn.commit()
            return deleted

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _del)

    async def get_global_stats(self) -> dict:
        if self.use_turso:
            try:
                res = await self.turso_client.execute("SELECT key, val FROM global_stats")
                return {row[0]: row[1] for row in res.rows}
            except Exception as e:
                log.error(f"Turso error in get_global_stats: {e}")
                return {}

        def _stats():
            cur = self.sqlite_conn.cursor()
            cur.execute("SELECT key, val FROM global_stats")
            rows = cur.fetchall()
            return {r["key"]: r["val"] for r in rows}

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _stats)
