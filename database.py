import aiosqlite
from config import DB_NAME

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Foydalanuvchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT,
                language TEXT DEFAULT 'uz',
                bonus_points INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Kategoriyalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT NOT NULL,
                name_ru TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)

        # Dorilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description_uz TEXT,
                description_ru TEXT,
                category_id INTEGER,
                price INTEGER NOT NULL,
                unit TEXT DEFAULT 'dona',
                in_stock INTEGER DEFAULT 1,
                requires_recipe INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        # Buyurtmalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                bonus_used INTEGER DEFAULT 0,
                delivery_type TEXT DEFAULT 'pickup',
                delivery_address TEXT,
                payment_method TEXT DEFAULT 'cash',
                status TEXT DEFAULT 'new',
                admin_note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)

        # Buyurtma tarkibi
        await db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                medicine_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (medicine_id) REFERENCES medicines(id)
            )
        """)

        # Retseptlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                photo_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                admin_reply TEXT,
                total_price INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)

        # Maslahatlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        """)

        await db.commit()
        print("✅ Ma'lumotlar bazasi tayyor!")


# ===================== USER FUNCTIONS =====================

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return await cursor.fetchone()

async def create_user(telegram_id: int, full_name: str, phone: str, language: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, full_name, phone, language) VALUES (?, ?, ?, ?)",
            (telegram_id, full_name, phone, language)
        )
        await db.commit()

async def update_user_language(telegram_id: int, language: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET language = ? WHERE telegram_id = ?",
            (language, telegram_id)
        )
        await db.commit()

async def get_user_bonus(telegram_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT bonus_points FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

async def update_bonus(telegram_id: int, amount_spent: int, bonus_used: int = 0):
    earned = amount_spent // 10000
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users 
            SET bonus_points = bonus_points + ? - ?,
                total_spent = total_spent + ?
            WHERE telegram_id = ?
        """, (earned, bonus_used, amount_spent, telegram_id))
        await db.commit()
    return earned


# ===================== MEDICINE FUNCTIONS =====================

async def get_all_categories():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM categories WHERE is_active = 1"
        )
        return await cursor.fetchall()

async def get_medicines_by_category(category_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM medicines WHERE category_id = ? AND in_stock = 1",
            (category_id,)
        )
        return await cursor.fetchall()

async def search_medicines(query: str):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM medicines WHERE name LIKE ? AND in_stock = 1",
            (f"%{query}%",)
        )
        return await cursor.fetchall()

async def get_medicine(medicine_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM medicines WHERE id = ?", (medicine_id,)
        )
        return await cursor.fetchone()

async def add_medicine(name, desc_uz, desc_ru, category_id, price, unit, requires_recipe):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO medicines (name, description_uz, description_ru, category_id, price, unit, requires_recipe)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, desc_uz, desc_ru, category_id, price, unit, requires_recipe))
        await db.commit()

async def update_medicine_price(medicine_id: int, new_price: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE medicines SET price = ? WHERE id = ?",
            (new_price, medicine_id)
        )
        await db.commit()

async def add_category(name_uz: str, name_ru: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO categories (name_uz, name_ru) VALUES (?, ?)",
            (name_uz, name_ru)
        )
        await db.commit()


# ===================== ORDER FUNCTIONS =====================

async def create_order(user_id, total_price, bonus_used, delivery_type, delivery_address, payment_method):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
            INSERT INTO orders (user_id, total_price, bonus_used, delivery_type, delivery_address, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, total_price, bonus_used, delivery_type, delivery_address, payment_method))
        await db.commit()
        return cursor.lastrowid

async def add_order_item(order_id, medicine_id, quantity, price):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO order_items (order_id, medicine_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, medicine_id, quantity, price))
        await db.commit()

async def get_order(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()

async def get_order_items(order_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT oi.*, m.name FROM order_items oi
            JOIN medicines m ON oi.medicine_id = m.id
            WHERE oi.order_id = ?
        """, (order_id,))
        return await cursor.fetchall()

async def get_new_orders():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT o.*, u.full_name, u.phone FROM orders o JOIN users u ON o.user_id = u.telegram_id WHERE o.status = 'new' ORDER BY o.created_at DESC"
        )
        return await cursor.fetchall()

async def update_order_status(order_id: int, status: str, note: str = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE orders SET status = ?, admin_note = ? WHERE id = ?",
            (status, note, order_id)
        )
        await db.commit()

async def get_user_orders(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        return await cursor.fetchall()


# ===================== RECIPE FUNCTIONS =====================

async def create_recipe(user_id: int, photo_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO recipes (user_id, photo_id) VALUES (?, ?)",
            (user_id, photo_id)
        )
        await db.commit()
        return cursor.lastrowid

async def get_pending_recipes():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT r.*, u.full_name, u.phone FROM recipes r
            JOIN users u ON r.user_id = u.telegram_id
            WHERE r.status = 'pending'
        """)
        return await cursor.fetchall()

async def reply_recipe(recipe_id: int, reply: str, total_price: int = None):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE recipes SET status = 'answered', admin_reply = ?, total_price = ? WHERE id = ?",
            (reply, total_price, recipe_id)
        )
        await db.commit()


# ===================== CONSULTATION FUNCTIONS =====================

async def create_consultation(user_id: int, question: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO consultations (user_id, question) VALUES (?, ?)",
            (user_id, question)
        )
        await db.commit()
        return cursor.lastrowid

async def get_pending_consultations():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT c.*, u.full_name FROM consultations c
            JOIN users u ON c.user_id = u.telegram_id
            WHERE c.status = 'pending'
        """)
        return await cursor.fetchall()

async def reply_consultation(consultation_id: int, answer: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE consultations SET status = 'answered', answer = ? WHERE id = ?",
            (answer, consultation_id)
        )
        await db.commit()


# ===================== STATISTICS =====================

async def get_statistics():
    async with aiosqlite.connect(DB_NAME) as db:
        stats = {}
        
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        stats['total_orders'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
        stats['new_orders'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'")
        result = await cursor.fetchone()
        stats['total_revenue'] = result[0] or 0
        
        cursor = await db.execute(
            "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')"
        )
        stats['today_orders'] = (await cursor.fetchone())[0]
        
        return stats
