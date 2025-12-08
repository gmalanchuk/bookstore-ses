from fastapi import FastAPI
from src.database import lifespan

app = FastAPI(lifespan=lifespan)

@app.get("/books")
async def get_books():
    query = "SELECT * FROM products;"
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch(query)
    return rows
