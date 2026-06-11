from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Yangi buyurtmalar"), KeyboardButton(text="📋 Retseptlar")],
            [KeyboardButton(text="👨‍⚕️ Maslahatlar"), KeyboardButton(text="💊 Dori boshqaruv")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏠 Bosh menyu")]
        ],
        resize_keyboard=True
    )

def medicine_manage_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Dori qo'shish", callback_data="admin_add_medicine")],
        [InlineKeyboardButton(text="💰 Narx yangilash", callback_data="admin_update_price")],
        [InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="admin_add_category")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")]
    ])

def order_actions_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Qabul qilindi", callback_data=f"order_accept_{order_id}")],
        [InlineKeyboardButton(text="🔄 Tayyorlanmoqda", callback_data=f"order_preparing_{order_id}")],
        [InlineKeyboardButton(text="🚚 Yo'lda", callback_data=f"order_delivering_{order_id}")],
        [InlineKeyboardButton(text="✅ Yetkazildi", callback_data=f"order_completed_{order_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"order_cancel_{order_id}")]
    ])

def recipe_actions_keyboard(recipe_id, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"recipe_reply_{recipe_id}_{user_id}")]
    ])

def consultation_actions_keyboard(consult_id, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"consult_reply_{consult_id}_{user_id}")]
    ])
