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
    # Получаем user_id из cookies
    user_id = request.cookies.get("user_id")

    # Запрос с JOIN для получения названий вместо ID
    query = """
        SELECT 
            b.id, b.title, b.description, b.price, b.publication_year, 
            b.stock_quantity, b.cover_path, b.author_id,
            a.full_name as author_name,
            p.name as publisher_name,
            g.name as genre_name
        FROM books b
        JOIN authors a ON b.author_id = a.id
        JOIN publishers p ON b.publisher_id = p.id
        JOIN genres g ON b.genre_id = g.id
        WHERE b.id = $1;
    """

    # Запрос для получения отзывов
    reviews_query = """
        SELECT 
            r.id, r.rating, r.comment_text,
            u.full_name as user_name,
            r.user_id
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.book_id = $1
        ORDER BY r.id DESC;
    """

    async with app.state.db.acquire() as conn:
        row = await conn.fetchrow(query, book_id)
        reviews_rows = await conn.fetch(reviews_query, book_id)

    if not row:
        return HTMLResponse(content="Книга не знайдена", status_code=404)

    # Превращаем результат в словарь для удобства Jinja
    book_data = dict(row)
    reviews_data = [dict(r) for r in reviews_rows]

    # Проверяем, оставлял ли текущий пользователь отзыв
    user_has_review = False
    if user_id:
        user_has_review = any(r['user_id'] == int(user_id) for r in reviews_data)

    # Возвращаем шаблон (предполагается, что templates настроен)
    return templates.TemplateResponse(
        "book_detail.html",
        {
            "request": request,
            "book": book_data,
            "reviews": reviews_data,
            "user_id": user_id,
            "user_has_review": user_has_review
        }
    )


# Добавление отзыва
@app.post("/books/{book_id}/review")
async def add_review(
    request: Request,
    book_id: int,
    rating: int = Form(...),
    comment_text: str = Form("")
):
    # Получаем user_id из cookies
    user_id = request.cookies.get("user_id")

    # Если пользователь не залогинен, редиректим на логин
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем корректность рейтинга
    if rating < 1 or rating > 5:
        return RedirectResponse(url=f"/books/{book_id}", status_code=303)

    async with app.state.db.acquire() as conn:
        # Проверяем, не оставлял ли пользователь уже отзыв
        existing_review = await conn.fetchrow(
            "SELECT id FROM reviews WHERE book_id = $1 AND user_id = $2;",
            book_id, int(user_id)
        )

        if existing_review:
            # Обновляем существующий отзыв
            await conn.execute(
                """
                UPDATE reviews 
                SET rating = $1, comment_text = $2 
                WHERE book_id = $3 AND user_id = $4;
                """,
                rating, comment_text, book_id, int(user_id)
            )
        else:
            # Создаем новый отзыв
            await conn.execute(
                """
                INSERT INTO reviews (book_id, user_id, rating, comment_text)
                VALUES ($1, $2, $3, $4);
                """,
                book_id, int(user_id), rating, comment_text
            )

    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


# Інформація про автора
@app.get("/authors/{author_id}", response_class=HTMLResponse)
async def author_detail(request: Request, author_id: int):
    async with app.state.db.acquire() as conn:
        # Отримуємо інформацію про автора
        author_row = await conn.fetchrow(
            "SELECT id, full_name, description FROM authors WHERE id = $1;",
            author_id
        )

        if not author_row:
            return HTMLResponse(content="Автора не знайдено", status_code=404)

        # Отримуємо всі книги автора
        books_rows = await conn.fetch(
            """
            SELECT b.id, b.title, b.price, b.cover_path, g.name as genre_name
            FROM books b
            JOIN genres g ON b.genre_id = g.id
            WHERE b.author_id = $1
            ORDER BY b.title;
            """,
            author_id
        )

    author_data = dict(author_row)
    books_data = [dict(row) for row in books_rows]

    return templates.TemplateResponse(
        "author_detail.html",
        {"request": request, "author": author_data, "books": books_data}
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


# Добавление книги в корзину
@app.post("/cart/add/{book_id}")
async def add_to_cart(
        request: Request,
        book_id: int
):
    # Получаем user_id из cookies
    user_id = request.cookies.get("user_id")

    # Если пользователь не залогинен, редиректим на логин
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Проверяем, есть ли книга уже в корзине
        existing_item = await conn.fetchrow(
            "SELECT id, quantity FROM cart WHERE user_id = $1 AND book_id = $2;",
            int(user_id), book_id
        )

        if existing_item:
            # Увеличиваем количество на 1
            await conn.execute(
                "UPDATE cart SET quantity = quantity + 1 WHERE id = $1;",
                existing_item['id']
            )
        else:
            # Добавляем новую запись с quantity = 1
            await conn.execute(
                """
                INSERT INTO cart (user_id, book_id, quantity)
                VALUES ($1, $2, 1);
                """,
                int(user_id), book_id
            )

    # Редиректим обратно на страницу книги
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


# Страница корзины
@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    # Получаем user_id из cookies
    user_id = request.cookies.get("user_id")

    # Если пользователь не залогинен, редиректим на логин
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Получаем все книги из корзины с информацией о книге
        cart_items = await conn.fetch(
            """
            SELECT 
                c.id as cart_id,
                c.quantity,
                b.id as book_id,
                b.title,
                b.price,
                b.cover_path,
                a.full_name as author_name,
                (b.price * c.quantity) as total_price
            FROM cart c
            JOIN books b ON c.book_id = b.id
            JOIN authors a ON b.author_id = a.id
            WHERE c.user_id = $1
            ORDER BY c.added_at DESC;
            """,
            int(user_id)
        )

        cart_list = [dict(item) for item in cart_items]

        # Вычисляем общую стоимость
        total_cost = sum(item['total_price'] for item in cart_list)

        # Общее количество книг
        total_items = sum(item['quantity'] for item in cart_list)

        # Получаем историю заказов пользователя
        orders = await conn.fetch(
            """
            SELECT 
                o.id,
                o.created_at,
                p.amount,
                p.status,
                p.payment_method,
                COUNT(oi.id) as items_count
            FROM orders o
            JOIN payments p ON p.order_id = o.id
            JOIN order_items oi ON oi.order_id = o.id
            WHERE o.user_id = $1
            GROUP BY o.id, o.created_at, p.amount, p.status, p.payment_method
            ORDER BY o.created_at DESC;
            """,
            int(user_id)
        )
        orders_list = [dict(order) for order in orders]

    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart_list,
        "total_cost": total_cost,
        "total_items": total_items,
        "orders": orders_list
    })


# Удаление книги из корзины
@app.post("/cart/remove/{cart_id}")
async def remove_from_cart(request: Request, cart_id: int):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Удаляем товар из корзины (проверяем что он принадлежит пользователю)
        await conn.execute(
            "DELETE FROM cart WHERE id = $1 AND user_id = $2;",
            cart_id, int(user_id)
        )

    return RedirectResponse(url="/cart", status_code=303)


# Обновление количества книг в корзине
@app.post("/cart/update/{cart_id}")
async def update_cart_quantity(
    request: Request,
    cart_id: int,
    quantity: int = Form(...)
):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # Проверяем, что количество не меньше 1
    if quantity < 1:
        quantity = 1

    async with app.state.db.acquire() as conn:
        # Обновляем количество товара в корзине
        await conn.execute(
            """
            UPDATE cart 
            SET quantity = $1 
            WHERE id = $2 AND user_id = $3;
            """,
            quantity, cart_id, int(user_id)
        )

    return RedirectResponse(url="/cart", status_code=303)


# Страница оформления заказа
@app.post("/order/create", response_class=HTMLResponse)
async def order_create_page(request: Request):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Получаем товары из корзины
        cart_items = await conn.fetch(
            """
            SELECT 
                c.id as cart_id,
                c.quantity,
                b.id as book_id,
                b.title,
                b.price,
                b.cover_path,
                b.stock_quantity,
                a.full_name as author_name,
                (b.price * c.quantity) as total_price
            FROM cart c
            JOIN books b ON c.book_id = b.id
            JOIN authors a ON b.author_id = a.id
            WHERE c.user_id = $1
            ORDER BY c.added_at DESC;
            """,
            int(user_id)
        )

        if not cart_items:
            return RedirectResponse(url="/cart", status_code=303)

        cart_list = [dict(item) for item in cart_items]
        total_cost = sum(item['total_price'] for item in cart_list)
        total_items = sum(item['quantity'] for item in cart_list)

        # Получаем данные пользователя
        user = await conn.fetchrow(
            "SELECT full_name, email FROM users WHERE id = $1;",
            int(user_id)
        )

    return templates.TemplateResponse("checkout.html", {
        "request": request,
        "cart_items": cart_list,
        "total_cost": total_cost,
        "total_items": total_items,
        "user": dict(user) if user else {}
    })


# Подтверждение заказа
@app.post("/order/confirm")
async def order_confirm(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    payment_method: str = Form(...)
):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Получаем товары из корзины
        cart_items = await conn.fetch(
            """
            SELECT 
                c.id as cart_id,
                c.quantity,
                b.id as book_id,
                b.price,
                b.stock_quantity
            FROM cart c
            JOIN books b ON c.book_id = b.id
            WHERE c.user_id = $1;
            """,
            int(user_id)
        )

        if not cart_items:
            return RedirectResponse(url="/cart", status_code=303)

        # Проверяем наличие товаров на складе
        for item in cart_items:
            if item['quantity'] > item['stock_quantity']:
                return RedirectResponse(url="/cart", status_code=303)

        # Вычисляем общую сумму
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

        # Создаем заказ
        order = await conn.fetchrow(
            """
            INSERT INTO orders (user_id, created_at)
            VALUES ($1, CURRENT_TIMESTAMP)
            RETURNING id;
            """,
            int(user_id)
        )
        order_id = order['id']

        # Добавляем товары в заказ
        for item in cart_items:
            await conn.execute(
                """
                INSERT INTO order_items (order_id, book_id, quantity, price)
                VALUES ($1, $2, $3, $4);
                """,
                order_id, item['book_id'], item['quantity'], item['price']
            )

            # Уменьшаем количество на складе
            await conn.execute(
                """
                UPDATE books 
                SET stock_quantity = stock_quantity - $1 
                WHERE id = $2;
                """,
                item['quantity'], item['book_id']
            )

        # Создаем запись об оплате
        await conn.execute(
            """
            INSERT INTO payments (order_id, amount, payment_method, status)
            VALUES ($1, $2, $3, 'pending');
            """,
            order_id, total_amount, payment_method
        )

        # Очищаем корзину
        await conn.execute(
            "DELETE FROM cart WHERE user_id = $1;",
            int(user_id)
        )

    return RedirectResponse(url=f"/order/success/{order_id}", status_code=303)


# Страница успешного заказа
@app.get("/order/success/{order_id}", response_class=HTMLResponse)
async def order_success(request: Request, order_id: int):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    async with app.state.db.acquire() as conn:
        # Получаем информацию о заказе
        order = await conn.fetchrow(
            """
            SELECT o.id, o.created_at, p.amount, p.payment_method, p.status
            FROM orders o
            JOIN payments p ON p.order_id = o.id
            WHERE o.id = $1 AND o.user_id = $2;
            """,
            order_id, int(user_id)
        )

        if not order:
            return HTMLResponse(content="Замовлення не знайдено", status_code=404)

        # Получаем товары заказа
        order_items = await conn.fetch(
            """
            SELECT 
                oi.quantity,
                oi.price,
                b.title,
                b.cover_path,
                a.full_name as author_name,
                (oi.price * oi.quantity) as total_price
            FROM order_items oi
            JOIN books b ON oi.book_id = b.id
            JOIN authors a ON b.author_id = a.id
            WHERE oi.order_id = $1;
            """,
            order_id
        )

    return templates.TemplateResponse("order_success.html", {
        "request": request,
        "order": dict(order),
        "order_items": [dict(item) for item in order_items]
    })
