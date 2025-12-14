import os
import asyncpg
from fastapi import FastAPI
from contextlib import asynccontextmanager

from sql.all_tables import INIT_ALL_TABLES
from sql.seed_data import SEED_DATA

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/bookstore")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(DATABASE_URL)

    async with app.state.db.acquire() as conn:
        # Створюємо всі таблиці, якщо їх ще немає
        await conn.execute(INIT_ALL_TABLES)
        print("Tables created")

        # Перевіряємо, чи порожня таблиця authors
        # Якщо кількість записів = 0, то база ще не була заповнена
        authors_count = await conn.fetchval("SELECT COUNT(*) FROM authors;")

        if authors_count == 0:
            print("Database empty → Seeding initial data...")
            await conn.execute(SEED_DATA)
            print("Seed data inserted")
        else:
            print("Seed already exists → skipping")

    yield

    await app.state.db.close()
    print("Disconnected from DB")
