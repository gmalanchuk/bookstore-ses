from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.database import lifespan

app = FastAPI(lifespan=lifespan)

# Шаблони
templates = Jinja2Templates(directory="templates")

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")


# Головна сторінка
@app.get("/books", response_class=HTMLResponse)
async def get_books(request: Request):
    query = "SELECT id, title, price, author_id FROM products;"
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch(query)
    books = [dict(row) for row in rows]
    return templates.TemplateResponse("books.html", {"request": request, "books": books})


# Інформація про книгу
@app.get("/books/{book_id}", response_class=HTMLResponse)
async def book_detail(request: Request, book_id: int):
    query = "SELECT * FROM products WHERE id = $1;"
    async with app.state.db.acquire() as conn:
        row = await conn.fetchrow(query, book_id)

    if not row:
        return HTMLResponse(content="Book not found", status_code=404)

    book = dict(row)
    return templates.TemplateResponse("book_detail.html", {"request": request, "book": book})
