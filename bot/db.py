import json
import time
from pathlib import Path

import aiosqlite

from bot.guild_config import GuildConfig, LlmRuntimeConfig


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                guild_id INTEGER,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                thread_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            );

            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                server_mode TEXT NOT NULL DEFAULT 'default',
                ticket_category_id INTEGER,
                staff_role_id INTEGER,
                support_channel_ids TEXT NOT NULL DEFAULT '[]',
                faq_context TEXT NOT NULL DEFAULT '',
                updated_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS support_threads (
                thread_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS terms_agreements (
                user_id INTEGER PRIMARY KEY,
                terms_version TEXT NOT NULL,
                agreed_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pending_consult (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                thread_id INTEGER,
                ticket_id INTEGER,
                content TEXT NOT NULL,
                server_mode TEXT NOT NULL,
                custom_prompt TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_user_status
                ON tickets(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_messages_ticket
                ON messages(ticket_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_messages_thread
                ON messages(thread_id, created_at);
            """
        )
        await self._migrate()
        await self._conn.commit()

    async def _migrate(self):
        cursor = await self._conn.execute("PRAGMA table_info(tickets)")
        cols = {row[1] for row in await cursor.fetchall()}
        if "guild_id" not in cols:
            await self._conn.execute("ALTER TABLE tickets ADD COLUMN guild_id INTEGER")

        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_guild_user ON tickets(guild_id, user_id, status)"
        )

        cursor = await self._conn.execute("PRAGMA table_info(guild_settings)")
        gcols = {row[1] for row in await cursor.fetchall()}
        if "server_mode" not in gcols:
            await self._conn.execute(
                "ALTER TABLE guild_settings ADD COLUMN server_mode TEXT NOT NULL DEFAULT 'lumentia'"
            )

    async def close(self):
        await self._conn.close()

    def _row_to_guild_config(self, row) -> GuildConfig:
        channels = json.loads(row["support_channel_ids"] or "[]")
        return GuildConfig(
            guild_id=row["guild_id"],
            ticket_category_id=row["ticket_category_id"],
            staff_role_id=row["staff_role_id"],
            support_channel_ids=[int(x) for x in channels],
            custom_prompt=row["faq_context"] or "",
        )

    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        cursor = await self._conn.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_guild_config(row)

    async def save_guild_config(self, config: GuildConfig):
        now = time.time()
        await self._conn.execute(
            """
            INSERT INTO guild_settings
                (guild_id, ticket_category_id, staff_role_id, support_channel_ids, faq_context, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                ticket_category_id = excluded.ticket_category_id,
                staff_role_id = excluded.staff_role_id,
                support_channel_ids = excluded.support_channel_ids,
                faq_context = excluded.faq_context,
                updated_at = excluded.updated_at
            """,
            (
                config.guild_id,
                config.ticket_category_id,
                config.staff_role_id,
                json.dumps(config.support_channel_ids),
                config.custom_prompt,
                now,
            ),
        )
        await self._conn.commit()

    async def set_ticket_category(self, guild_id: int, category_id: int | None):
        cfg = await self.get_guild_config(guild_id) or GuildConfig(guild_id=guild_id)
        cfg.ticket_category_id = category_id
        await self.save_guild_config(cfg)

    async def set_staff_role(self, guild_id: int, role_id: int | None):
        cfg = await self.get_guild_config(guild_id) or GuildConfig(guild_id=guild_id)
        cfg.staff_role_id = role_id
        await self.save_guild_config(cfg)

    async def add_support_channel(self, guild_id: int, channel_id: int) -> bool:
        cfg = await self.get_guild_config(guild_id) or GuildConfig(guild_id=guild_id)
        if channel_id in cfg.support_channel_ids:
            return False
        cfg.support_channel_ids.append(channel_id)
        await self.save_guild_config(cfg)
        return True

    async def remove_support_channel(self, guild_id: int, channel_id: int) -> bool:
        cfg = await self.get_guild_config(guild_id)
        if not cfg or channel_id not in cfg.support_channel_ids:
            return False
        cfg.support_channel_ids.remove(channel_id)
        await self.save_guild_config(cfg)
        return True

    async def close_stale_ticket(self, channel_id: int):
        await self.close_ticket(channel_id)

    async def set_custom_prompt(self, guild_id: int, text: str):
        cfg = await self.get_guild_config(guild_id) or GuildConfig(guild_id=guild_id)
        cfg.custom_prompt = text
        await self.save_guild_config(cfg)

    async def get_bot_setting(self, key: str) -> str | None:
        cursor = await self._conn.execute(
            "SELECT value FROM bot_settings WHERE key = ?",
            (key,),
        )
        row = await cursor.fetchone()
        return row["value"] if row else None

    async def set_bot_setting(self, key: str, value: str):
        await self._conn.execute(
            """
            INSERT INTO bot_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await self._conn.commit()

    async def get_llm_runtime(self, defaults: LlmRuntimeConfig) -> LlmRuntimeConfig:
        base = await self.get_bot_setting("ollama_base_url")
        model = await self.get_bot_setting("ollama_model")
        max_tokens = await self.get_bot_setting("ollama_max_tokens")
        temperature = await self.get_bot_setting("ollama_temperature")

        return LlmRuntimeConfig(
            base_url=base if base else defaults.base_url,
            model=model if model else defaults.model,
            max_tokens=int(max_tokens) if max_tokens else defaults.max_tokens,
            temperature=float(temperature) if temperature else defaults.temperature,
        )

    async def create_ticket(self, channel_id: int, guild_id: int, user_id: int) -> int:
        now = time.time()
        cursor = await self._conn.execute(
            "INSERT INTO tickets (channel_id, guild_id, user_id, status, created_at) VALUES (?, ?, ?, 'open', ?)",
            (channel_id, guild_id, user_id, now),
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def get_open_ticket_by_user(self, guild_id: int, user_id: int):
        cursor = await self._conn.execute(
            """
            SELECT * FROM tickets
            WHERE guild_id = ? AND user_id = ? AND status = 'open'
            ORDER BY created_at DESC LIMIT 1
            """,
            (guild_id, user_id),
        )
        return await cursor.fetchone()

    async def get_ticket_by_channel(self, channel_id: int):
        cursor = await self._conn.execute(
            "SELECT * FROM tickets WHERE channel_id = ? LIMIT 1",
            (channel_id,),
        )
        return await cursor.fetchone()

    async def close_ticket(self, channel_id: int):
        await self._conn.execute(
            "UPDATE tickets SET status = 'closed' WHERE channel_id = ?",
            (channel_id,),
        )
        await self._conn.commit()

    async def add_message(
        self,
        role: str,
        content: str,
        ticket_id: int | None = None,
        thread_id: int | None = None,
    ):
        await self._conn.execute(
            "INSERT INTO messages (ticket_id, thread_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, thread_id, role, content, time.time()),
        )
        await self._conn.commit()

    async def clear_support_thread_owner(self, thread_id: int):
        await self._conn.execute(
            "DELETE FROM support_threads WHERE thread_id = ?",
            (thread_id,),
        )
        await self._conn.commit()

    async def has_terms_agreed(self, user_id: int, terms_version: str) -> bool:
        cursor = await self._conn.execute(
            "SELECT terms_version FROM terms_agreements WHERE user_id = ? LIMIT 1",
            (user_id,),
        )
        row = await cursor.fetchone()
        return bool(row and row["terms_version"] == terms_version)

    async def set_terms_agreed(self, user_id: int, terms_version: str):
        await self._conn.execute(
            """
            INSERT INTO terms_agreements (user_id, terms_version, agreed_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                terms_version = excluded.terms_version,
                agreed_at = excluded.agreed_at
            """,
            (user_id, terms_version, time.time()),
        )
        await self._conn.commit()

    async def set_pending_consult(
        self,
        user_id: int,
        guild_id: int,
        channel_id: int,
        content: str,
        server_mode: str,
        thread_id: int | None = None,
        ticket_id: int | None = None,
        custom_prompt: str = "",
    ):
        await self._conn.execute(
            """
            INSERT INTO pending_consult
                (user_id, guild_id, channel_id, thread_id, ticket_id, content, server_mode, custom_prompt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                guild_id = excluded.guild_id,
                channel_id = excluded.channel_id,
                thread_id = excluded.thread_id,
                ticket_id = excluded.ticket_id,
                content = excluded.content,
                server_mode = excluded.server_mode,
                custom_prompt = excluded.custom_prompt,
                created_at = excluded.created_at
            """,
            (user_id, guild_id, channel_id, thread_id, ticket_id, content, server_mode, custom_prompt, time.time()),
        )
        await self._conn.commit()

    async def get_pending_consult(self, user_id: int):
        cursor = await self._conn.execute(
            "SELECT * FROM pending_consult WHERE user_id = ? LIMIT 1",
            (user_id,),
        )
        return await cursor.fetchone()

    async def clear_pending_consult(self, user_id: int):
        await self._conn.execute(
            "DELETE FROM pending_consult WHERE user_id = ?",
            (user_id,),
        )
        await self._conn.commit()

    async def set_support_thread_owner(self, thread_id: int, guild_id: int, user_id: int):
        await self._conn.execute(
            """
            INSERT INTO support_threads (thread_id, guild_id, user_id, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET user_id = excluded.user_id
            """,
            (thread_id, guild_id, user_id, time.time()),
        )
        await self._conn.commit()

    async def get_support_thread_owner(self, thread_id: int) -> int | None:
        cursor = await self._conn.execute(
            "SELECT user_id FROM support_threads WHERE thread_id = ? LIMIT 1",
            (thread_id,),
        )
        row = await cursor.fetchone()
        return int(row["user_id"]) if row else None

    async def get_messages(
        self,
        ticket_id: int | None = None,
        thread_id: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        if ticket_id is not None:
            cursor = await self._conn.execute(
                """
                SELECT role, content FROM messages
                WHERE ticket_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (ticket_id, limit),
            )
        elif thread_id is not None:
            cursor = await self._conn.execute(
                """
                SELECT role, content FROM messages
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (thread_id, limit),
            )
        else:
            return []

        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
