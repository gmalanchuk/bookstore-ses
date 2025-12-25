import os
import asyncpg
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.sql.all_tables import INIT_ALL_TABLES
from src.sql.seed_data import SEED_DATA

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@postgres:5432/bookstore")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(DATABASE_URL)

    async with app.state.db.acquire() as conn:
        # Створюємо всі таблиці, якщо їх ще немає
        await conn.execute(INIT_ALL_TABLES)
        print("Таблиці створено")

        # Перевіряємо, чи порожня таблиця authors
        # Якщо кількість записів = 0, то база ще не була заповнена
        authors_count = await conn.fetchval("SELECT COUNT(*) FROM authors;")

        if authors_count == 0:
            print("База даних порожня → Заповнюємо початковими даними...")
            await conn.execute(SEED_DATA)
            print("Початкові дані додано")
        else:
            print("Дані вже існують → пропускаємо")

    yield

    await app.state.db.close()
    print("Відʼєднано від бази даних")
