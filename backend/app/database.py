import asyncpg
from typing import AsyncGenerator
from app.config import settings

class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=settings.database_url,
                    min_size=2,
                    max_size=10,
                    statement_cache_size=0  # Critical for pgBouncer compatibility
                )
            except Exception as e:
                print(f"Error initializing db pool: {e}")
                raise e

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_conn(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if not self.pool:
            raise RuntimeError("Database connection pool is not initialized")
        async with self.pool.acquire() as conn:
            yield conn

db = Database()
