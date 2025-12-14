SEED_DATA = """
    INSERT INTO users (id, full_name, email, role, password) VALUES
    (1, 'Іван Петренко', 'ivan@example.com', 'customer', 'pass1'),
    (2, 'Олена Ковальчук', 'olena@example.com', 'customer', 'pass2'),
    (3, 'Марія Іваськів', 'maria@example.com', 'customer', 'pass3'),
    (4, 'Андрій Синюк', 'andriy@example.com', 'customer', 'pass4'),
    (5, 'Юрій Бойко', 'yurii@example.com', 'customer', 'pass5'),
    (6, 'Катерина Горова', 'katya@example.com', 'customer', 'pass6'),
    (7, 'Ігор Малик', 'ihor@example.com', 'customer', 'pass7'),
    (8, 'Олеся Дончук', 'olesya@example.com', 'customer', 'pass8'),
    (9, 'Назар Паламар', 'nazar@example.com', 'customer', 'pass9'),
    (10, 'Admin', 'admin@example.com', 'admin', 'adminpass');

    INSERT INTO authors (id, full_name, description) VALUES
    (1, 'Тарас Шевченко', 'Український поет, письменник і художник.'),
    (2, 'Леся Українка', 'Поетеса, драматург, громадська діячка.'),
    (3, 'Іван Франко', 'Письменник, поет, мислитель.'),
    (4, 'Михайло Коцюбинський', 'Майстер психологічної прози.'),
    (5, 'Іван Нечуй-Левицький', 'Класик української прози.'),
    (6, 'Іван Багряний', 'Письменник і політичний діяч.'),
    (7, 'Всеволод Нестайко', 'Відомий дитячий письменник.'),
    (8, 'Сергій Жадан', 'Сучасний український письменник.'),
    (9, 'Ліна Костенко', 'Поетеса, дисидентка.'),
    (10, 'Микола Хвильовий', 'Представник українського модернізму.');

    INSERT INTO products (title, description, author_id, publisher, genre, type, price, publication_year, stock_quantity, cover_path) VALUES
    ('Кобзар', 'Збірка поезій.', 1, 'А-БА-БА-ГА-ЛА-МА-ГА', 'Poetry', 'Hardcover', 450, 1840, 100, '/covers/5713_1.jpg'),
    ('Гайдамаки', 'Історична поема.', 1, 'Folio', 'Poetry', 'Paperback', 220, 1841, 60, '/covers/5713_1.jpg'),
    ('Лісова пісня', 'Драма-феєрія.', 2, 'Folio', 'Drama', 'Paperback', 180, 1911, 80, '/covers/5713_1.jpg'),
    ('Камінний господар', 'Філософська драма.', 2, 'КСД', 'Drama', 'Hardcover', 260, 1912, 40, '/covers/5713_1.jpg'),
    ('Захар Беркут', 'Історична повість.', 3, 'А-БА-БА-ГА-ЛА-МА-ГА', 'Historical', 'Hardcover', 300, 1883, 90, '/covers/5713_1.jpg'),
    ('Мойсей', 'Філософська поема.', 3, 'Folio', 'Poetry', 'Paperback', 200, 1905, 50, '/covers/5713_1.jpg'),
    ('Борислав сміється', 'Соціальний роман.', 3, 'КСД', 'Novel', 'Paperback', 240, 1882, 70, '/covers/5713_1.jpg'),
    ('Тіні забутих предків', 'Повість про кохання.', 4, 'Видавництво Старого Лева', 'Fiction', 'Hardcover', 260, 1911, 65, '/covers/5713_1.jpg'),
    ('Fata Morgana', 'Соціально-психологічна повість.', 4, 'Folio', 'Fiction', 'Paperback', 190, 1904, 45, '/covers/5713_1.jpg'),
    ('Кайдашева сімʼя', 'Побутова повість.', 5, 'Folio', 'Fiction', 'Paperback', 160, 1878, 120, '/covers/5713_1.jpg'),
    ('Микола Джеря', 'Соціальна повість.', 5, 'Znannia', 'Fiction', 'Paperback', 140, 1876, 55, '/covers/5713_1.jpg'),
    ('Тигролови', 'Пригодницький роман.', 6, 'Наш Формат', 'Adventure', 'Hardcover', 310, 1944, 85, '/covers/5713_1.jpg'),
    ('Сад Гетсиманський', 'Роман про репресії.', 6, 'КСД', 'Novel', 'Hardcover', 330, 1950, 40, '/covers/5713_1.jpg'),
    ('Тореадори з Васюківки', 'Дитячі пригоди.', 7, 'А-БА-БА-ГА-ЛА-МА-ГА', 'Children', 'Hardcover', 380, 1973, 150, '/covers/5713_1.jpg'),
    ('Одиниця з обманом', 'Шкільні пригоди.', 7, 'Школа', 'Children', 'Paperback', 200, 1984, 90, '/covers/5713_1.jpg'),
    ('Ворошиловград', 'Сучасний роман.', 8, 'Meridian Czernowitz', 'Novel', 'Paperback', 240, 2010, 50, '/covers/5713_1.jpg'),
    ('Інтернат', 'Роман про війну.', 8, 'Meridian Czernowitz', 'Novel', 'Hardcover', 320, 2017, 70, '/covers/5713_1.jpg'),
    ('Записки українського самашедшого', 'Сучасний роман.', 9, 'А-БА-БА-ГА-ЛА-МА-ГА', 'Novel', 'Hardcover', 360, 2010, 60, '/covers/5713_1.jpg'),
    ('Я (Романтика)', 'Психологічна новела.', 10, 'Folio', 'Fiction', 'Paperback', 130, 1924, 75, '/covers/5713_1.jpg');

    INSERT INTO reviews (product_id, user_id, rating, comment_text) VALUES
    (1, 1, 5, 'Чудова книга, прочитав із захопленням!'),
    (2, 2, 4, 'Сподобалось, але було місцями складно.'),
    (3, 3, 5, 'Один із найкращих творів української літератури.'),
    (4, 4, 3, 'Добре, але не моє.'),
    (5, 5, 5, 'Дуже емоційна та атмосферна історія.'),
    (6, 6, 4, 'Сильний текст, рекомендую.'),
    (7, 7, 5, 'Класика, яку варто прочитати кожному.'),
    (8, 8, 5, 'Весела та повчальна книга.'),
    (9, 9, 5, 'Глибокий та чуттєвий роман.'),
    (10, 1, 4, 'Сподобалось, але місцями важке читання.');
"""

# INSERT INTO orders (user_id, product_id) VALUES
# (1, 3),
# (2, 5),
# (3, 7),
# (4, 2),
# (5, 1),
# (6, 10),
# (7, 8),
# (8, 4),
# (9, 6),
# (10, 9);
#
# INSERT INTO payments (order_id, amount, payment_method, status) VALUES
# (1, 320.00, 'card', 'completed'),
# (2, 250.00, 'paypal', 'pending'),
# (3, 270.00, 'mono', 'completed'),
# (4, 180.00, 'card', 'completed'),
# (5, 450.00, 'paypal', 'completed'),
# (6, 300.00, 'mono', 'pending'),
# (7, 380.00, 'card', 'completed'),
# (8, 150.00, 'paypal', 'completed'),
# (9, 290.00, 'mono', 'completed'),
# (10, 220.00, 'card', 'completed');
