import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import aiosqlite
from config import BOTS_DIR, BOT_LOGS_DIR, BOT_CONFIGS_DIR, DB_PATH

BOT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
BOT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# In-memory process registry: bot_id -> subprocess.Popen
_processes: Dict[str, subprocess.Popen] = {}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                script_path TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                last_started TEXT,
                last_stopped TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_configs (
                bot_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (bot_id, key)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                ts TEXT NOT NULL
            )
        """)
        await db.commit()


async def register_bot(bot_id: str, name: str, script_path: str, description: str = "") -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO bots (id, name, script_path, description, created_at) VALUES (?,?,?,?,?)",
            (bot_id, name, script_path, description, datetime.utcnow().isoformat())
        )
        await db.commit()
    return await get_bot(bot_id)


async def get_bot(bot_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bots WHERE id=?", (bot_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            bot = dict(row)
            bot["status"] = "running" if _is_running(bot_id) else "stopped"
            bot["config"] = await _get_config(db, bot_id)
            return bot


async def list_bots() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bots ORDER BY name") as cur:
            rows = await cur.fetchall()
            result = []
            for row in rows:
                bot = dict(row)
                bot["status"] = "running" if _is_running(bot["id"]) else "stopped"
                bot["config"] = await _get_config(db, bot["id"])
                result.append(bot)
            return result


async def start_bot(bot_id: str) -> dict:
    bot = await get_bot(bot_id)
    if not bot:
        raise ValueError(f"Bot not found: {bot_id}")
    if _is_running(bot_id):
        raise RuntimeError("Bot already running")

    script = Path(bot["script_path"])
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")

    log_file = BOT_LOGS_DIR / f"{bot_id}.log"
    config = bot.get("config", {})

    # Pass config as env vars prefixed with BOT_
    env = {f"BOT_{k.upper()}": str(v) for k, v in config.items()}

    with open(log_file, "a") as lf:
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=lf,
            stderr=lf,
            env={**_current_env(), **env},
            cwd=str(script.parent),
        )
    _processes[bot_id] = proc

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bots SET last_started=? WHERE id=?",
            (datetime.utcnow().isoformat(), bot_id)
        )
        await db.commit()

    await _log(bot_id, "INFO", f"Bot started (pid={proc.pid})")
    return await get_bot(bot_id)


async def stop_bot(bot_id: str) -> dict:
    if not _is_running(bot_id):
        raise RuntimeError("Bot not running")
    proc = _processes[bot_id]
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    del _processes[bot_id]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bots SET last_stopped=? WHERE id=?",
            (datetime.utcnow().isoformat(), bot_id)
        )
        await db.commit()

    await _log(bot_id, "INFO", "Bot stopped")
    return await get_bot(bot_id)


async def update_config(bot_id: str, config: dict) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        for k, v in config.items():
            await db.execute(
                "INSERT OR REPLACE INTO bot_configs (bot_id, key, value) VALUES (?,?,?)",
                (bot_id, k, json.dumps(v))
            )
        await db.commit()
    return await get_bot(bot_id)


async def get_logs(bot_id: str, lines: int = 100) -> list:
    log_file = BOT_LOGS_DIR / f"{bot_id}.log"
    if not log_file.exists():
        return []
    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return [l.rstrip() for l in all_lines[-lines:]]


async def delete_bot(bot_id: str):
    if _is_running(bot_id):
        await stop_bot(bot_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bots WHERE id=?", (bot_id,))
        await db.execute("DELETE FROM bot_configs WHERE bot_id=?", (bot_id,))
        await db.commit()


# --- helpers ---

def _is_running(bot_id: str) -> bool:
    proc = _processes.get(bot_id)
    if not proc:
        return False
    return proc.poll() is None


async def _get_config(db: aiosqlite.Connection, bot_id: str) -> dict:
    async with db.execute(
        "SELECT key, value FROM bot_configs WHERE bot_id=?", (bot_id,)
    ) as cur:
        rows = await cur.fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}


async def _log(bot_id: str, level: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bot_logs (bot_id, level, message, ts) VALUES (?,?,?,?)",
            (bot_id, level, message, datetime.utcnow().isoformat())
        )
        await db.commit()


def _current_env() -> dict:
    import os
    return dict(os.environ)
