import os
import asyncpg
from fastapi import FastAPI
from contextlib import asynccontextmanager

from sql.all_tables import INIT_ALL_TABLES

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/bookstore")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(DATABASE_URL)
    async with app.state.db.acquire() as conn:
        # створюємо всі таблиці, якщо їх немає
        await conn.execute(INIT_ALL_TABLES)
        print("All tables created (if not exist)")

    yield

    await app.state.db.close()
    print("Disconnected from database")
