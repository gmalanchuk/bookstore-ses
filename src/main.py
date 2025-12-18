import hashlib
from urllib.parse import quote

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, Response

from src.database import lifespan

app = FastAPI(lifespan=lifespan)

# Шаблони
templates = Jinja2Templates(directory="templates")

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/covers", StaticFiles(directory="covers"), name="covers")


# Головна сторінка з фільтрацією
@app.get("/books", response_class=HTMLResponse)
async def get_books(
        request: Request,
        genre_id: int = None,
        author_id: int = None
):
    # Базовий запит
    query = """
        SELECT b.id, b.title, b.price, b.author_id, b.cover_path,
               a.full_name as author_name, g.name as genre_name
        FROM books b
        JOIN authors a ON b.author_id = a.id
        JOIN genres g ON b.genre_id = g.id
        WHERE 1=1
    """
    params = []

    # Додаємо фільтри якщо вони вказані
    if genre_id is not None:
        params.append(genre_id)
        query += f" AND b.genre_id = ${len(params)}"

    if author_id is not None:
        params.append(author_id)
        query += f" AND b.author_id = ${len(params)}"

    query += " ORDER BY b.title;"

    async with app.state.db.acquire() as conn:
        # Отримуємо книги з фільтрами
        rows = await conn.fetch(query, *params)
        books = [dict(row) for row in rows]

        # Отримуємо всіх авторів для випадаючого списку
        authors = await conn.fetch(
            "SELECT id, full_name FROM authors ORDER BY full_name;"
        )
        authors_list = [dict(a) for a in authors]

        # Отримуємо всі жанри для випадаючого списку
        genres = await conn.fetch(
            "SELECT id, name FROM genres ORDER BY name;"
        )
        genres_list = [dict(g) for g in genres]

    return templates.TemplateResponse("books.html", {
        "request": request,
        "books": books,
        "authors": authors_list,
        "genres": genres_list,
        "selected_genre": genre_id,
        "selected_author": author_id
    })


# Інформація про книгу
@app.get("/books/{book_id}", response_class=HTMLResponse)
async def book_detail(request: Request, book_id: int):
    # Запрос с JOIN для получения названий вместо ID
    query = """
        SELECT 
            b.id, b.title, b.description, b.price, b.publication_year, 
            b.stock_quantity, b.cover_path,
            a.full_name as author_name,
            p.name as publisher_name,
            g.name as genre_name
        FROM books b
        JOIN authors a ON b.author_id = a.id
        JOIN publishers p ON b.publisher_id = p.id
        JOIN genres g ON b.genre_id = g.id
        WHERE b.id = $1;
    """

    async with app.state.db.acquire() as conn:
        row = await conn.fetchrow(query, book_id)

    if not row:
        return HTMLResponse(content="Книга не знайдена", status_code=404)

    # Превращаем результат в словарь для удобства Jinja
    book_data = dict(row)

    # Возвращаем шаблон (предполагается, что templates настроен)
    return templates.TemplateResponse(
        "book_detail.html",
        {"request": request, "book": book_data}
    )


# Страница регистрации
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# Обработка регистрации
@app.post("/register")
async def register(
        request: Request,
        full_name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)
):
    async with app.state.db.acquire() as conn:
        # Проверяем, существует ли email
        existing_user = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1;", email
        )

        if existing_user:
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": "Цей email вже зареєстрований"}
            )

        # Создаем нового пользователя
        await conn.execute(
            """
            INSERT INTO users (full_name, email, password, role)
            VALUES ($1, $2, $3, 'customer');
            """,
            full_name, email, password
        )

    # Перенаправляем на страницу логина
    return RedirectResponse(url="/login", status_code=303)


# Страница логина
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    async with app.state.db.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, full_name, email, role 
            FROM users 
            WHERE email = $1 AND password = $2;
            """,
            email, password
        )

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Невірний email або пароль"}
        )

    # Создаем cookie с user_id и кодируем имя в URL-безопасный формат
    redirect = RedirectResponse(url="/books", status_code=303)
    redirect.set_cookie(key="user_id", value=str(user['id']))
    redirect.set_cookie(key="user_name", value=quote(user['full_name']))

    return redirect


# Logout
@app.get("/logout")
async def logout():
    redirect = RedirectResponse(url="/books", status_code=303)
    redirect.delete_cookie(key="user_id")
    redirect.delete_cookie(key="user_name")
    return redirect