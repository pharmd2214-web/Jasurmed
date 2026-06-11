from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.admin import admin_main_keyboard, medicine_manage_keyboard, order_actions_keyboard
from config import ADMIN_IDS

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

class AdminStates(StatesGroup):
    # Dori qo'shish
    add_med_name = State()
    add_med_desc_uz = State()
    add_med_desc_ru = State()
    add_med_category = State()
    add_med_price = State()
    add_med_unit = State()
    add_med_recipe = State()
    # Narx yangilash
    update_price_id = State()
    update_price_value = State()
    # Kategoriya qo'shish
    add_cat_uz = State()
    add_cat_ru = State()
    # Retseptga javob
    reply_recipe_id = State()
    reply_recipe_text = State()
    reply_recipe_user = State()
    # Maslahatga javob
    reply_consult_id = State()
    reply_consult_text = State()
    reply_consult_user = State()

# === ADMIN PANEL ===
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat yo'q.")
        return
    await message.answer("👨‍💼 Admin panel", reply_markup=admin_main_keyboard())

# === BUYURTMALAR ===
@router.message(F.text == "📦 Yangi buyurtmalar")
async def show_new_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = await db.get_new_orders()
    if not orders:
        await message.answer("✅ Yangi buyurtmalar yo'q.")
        return
    for order in orders:
        text = (
            f"📦 *Buyurtma #{order['id']}*\n"
            f"👤 {order['full_name']} | {order['phone']}\n"
            f"💰 {order['total_price']:,} so'm\n"
            f"🚗 {'Yetkazib berish' if order['delivery_type'] == 'courier' else 'O\'zi oladi'}\n"
        )
        if order["delivery_address"]:
            text += f"📍 {order['delivery_address']}\n"
        text += f"💳 {order['payment_method']}"
        await message.answer(text, reply_markup=order_actions_keyboard(order["id"]), parse_mode="Markdown")

@router.callback_query(F.data.startswith("order_"))
async def handle_order_action(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    parts = callback.data.split("_")
    action = parts[1]
    order_id = int(parts[2])

    status_map = {
        "accept": "accepted",
        "preparing": "preparing",
        "delivering": "delivering",
        "completed": "completed",
        "cancel": "cancelled"
    }

    status_text = {
        "accepted": "✅ Qabul qilindi",
        "preparing": "🔄 Tayyorlanmoqda",
        "delivering": "🚚 Yo'lda",
        "completed": "✅ Yetkazildi",
        "cancelled": "❌ Bekor qilindi"
    }

    new_status = status_map.get(action)
    if not new_status:
        return

    await db.update_order_status(order_id, new_status)
    order = await db.get_order(order_id)

    await callback.answer(f"Holat: {status_text.get(new_status, new_status)}")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.reply(f"✅ Buyurtma #{order_id} holati: {status_text.get(new_status)}")

    # Foydalanuvchiga xabar
    try:
        user_text = f"📦 Buyurtma #{order_id} holati: *{status_text.get(new_status)}*"
        await bot.send_message(order["user_id"], user_text, parse_mode="Markdown")
    except:
        pass

# === RETSEPTLAR ===
@router.message(F.text == "📋 Retseptlar")
async def show_recipes(message: Message):
    if not is_admin(message.from_user.id):
        return
    recipes = await db.get_pending_recipes()
    if not recipes:
        await message.answer("✅ Kutilayotgan retseptlar yo'q.")
        return
    from keyboards.admin import recipe_actions_keyboard
    for recipe in recipes:
        await message.answer_photo(
            photo=recipe["photo_id"],
            caption=(
                f"📋 *Retsept #{recipe['id']}*\n"
                f"👤 {recipe['full_name']} | {recipe['phone']}"
            ),
            reply_markup=recipe_actions_keyboard(recipe["id"], recipe["user_id"]),
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("recipe_reply_"))
async def start_recipe_reply(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    recipe_id = int(parts[2])
    user_id = int(parts[3])
    await state.update_data(recipe_id=recipe_id, recipe_user_id=user_id)
    await callback.message.answer(f"📋 Retsept #{recipe_id} uchun javob yozing (narxni ham kiriting):")
    await state.set_state(AdminStates.reply_recipe_text)
    await callback.answer()

@router.message(AdminStates.reply_recipe_text)
async def send_recipe_reply(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    user_id = data["recipe_user_id"]

    await db.reply_recipe(recipe_id, message.text)
    await state.clear()

    await message.answer(f"✅ Retsept #{recipe_id} ga javob yuborildi.")
    try:
        await bot.send_message(
            user_id,
            f"📋 Retseptingizga javob:\n\n{message.text}"
        )
    except:
        pass

# === MASLAHATLAR ===
@router.message(F.text == "👨‍⚕️ Maslahatlar")
async def show_consultations(message: Message):
    if not is_admin(message.from_user.id):
        return
    consultations = await db.get_pending_consultations()
    if not consultations:
        await message.answer("✅ Kutilayotgan maslahatlar yo'q.")
        return
    from keyboards.admin import consultation_actions_keyboard
    for consult in consultations:
        await message.answer(
            f"👨‍⚕️ *Savol #{consult['id']}*\n"
            f"👤 {consult['full_name']}\n\n"
            f"❓ {consult['question']}",
            reply_markup=consultation_actions_keyboard(consult["id"], consult["user_id"]),
            parse_mode="Markdown"
        )

@router.callback_query(F.data.startswith("consult_reply_"))
async def start_consult_reply(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    consult_id = int(parts[2])
    user_id = int(parts[3])
    await state.update_data(consult_id=consult_id, consult_user_id=user_id)
    await callback.message.answer(f"👨‍⚕️ Savol #{consult_id} ga javob yozing:")
    await state.set_state(AdminStates.reply_consult_text)
    await callback.answer()

@router.message(AdminStates.reply_consult_text)
async def send_consult_reply(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    consult_id = data["consult_id"]
    user_id = data["consult_user_id"]

    await db.reply_consultation(consult_id, message.text)
    await state.clear()

    await message.answer(f"✅ Savol #{consult_id} ga javob yuborildi.")
    try:
        await bot.send_message(
            user_id,
            f"👨‍⚕️ Farmatsevt javobi:\n\n{message.text}"
        )
    except:
        pass

# === DORI BOSHQARUV ===
@router.message(F.text == "💊 Dori boshqaruv")
async def medicine_manage(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("💊 Dori boshqaruv:", reply_markup=medicine_manage_keyboard())

@router.callback_query(F.data == "admin_add_category")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("➕ Kategoriya nomini o'zbek tilida kiriting:")
    await state.set_state(AdminStates.add_cat_uz)
    await callback.answer()

@router.message(AdminStates.add_cat_uz)
async def add_cat_uz(message: Message, state: FSMContext):
    await state.update_data(cat_uz=message.text)
    await message.answer("Kategoriya nomini rus tilida kiriting:")
    await state.set_state(AdminStates.add_cat_ru)

@router.message(AdminStates.add_cat_ru)
async def add_cat_ru(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_category(data["cat_uz"], message.text)
    await state.clear()
    await message.answer(f"✅ Kategoriya qo'shildi: {data['cat_uz']} / {message.text}")

@router.callback_query(F.data == "admin_add_medicine")
async def start_add_medicine(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("💊 Dori nomini kiriting:")
    await state.set_state(AdminStates.add_med_name)
    await callback.answer()

@router.message(AdminStates.add_med_name)
async def add_med_name(message: Message, state: FSMContext):
    await state.update_data(med_name=message.text)
    await message.answer("📝 Tavsifini o'zbek tilida kiriting:")
    await state.set_state(AdminStates.add_med_desc_uz)

@router.message(AdminStates.add_med_desc_uz)
async def add_med_desc_uz(message: Message, state: FSMContext):
    await state.update_data(med_desc_uz=message.text)
    await message.answer("📝 Tavsifini rus tilida kiriting:")
    await state.set_state(AdminStates.add_med_desc_ru)

@router.message(AdminStates.add_med_desc_ru)
async def add_med_desc_ru(message: Message, state: FSMContext):
    await state.update_data(med_desc_ru=message.text)
    categories = await db.get_all_categories()
    cat_text = "📂 Kategoriya ID ni kiriting:\n\n"
    for cat in categories:
        cat_text += f"{cat['id']}. {cat['name_uz']}\n"
    await message.answer(cat_text)
    await state.set_state(AdminStates.add_med_category)

@router.message(AdminStates.add_med_category)
async def add_med_category(message: Message, state: FSMContext):
    await state.update_data(med_category=int(message.text))
    await message.answer("💰 Narxini kiriting (so'm):")
    await state.set_state(AdminStates.add_med_price)

@router.message(AdminStates.add_med_price)
async def add_med_price(message: Message, state: FSMContext):
    await state.update_data(med_price=int(message.text))
    await message.answer("📦 Birligini kiriting (dona, blister, quti...):")
    await state.set_state(AdminStates.add_med_unit)

@router.message(AdminStates.add_med_unit)
async def add_med_unit(message: Message, state: FSMContext):
    await state.update_data(med_unit=message.text)
    await message.answer("Retsept kerakmi? (ha / yo'q):")
    await state.set_state(AdminStates.add_med_recipe)

@router.message(AdminStates.add_med_recipe)
async def add_med_recipe(message: Message, state: FSMContext):
    data = await state.get_data()
    requires_recipe = 1 if message.text.lower() in ["ha", "да", "yes"] else 0

    await db.add_medicine(
        data["med_name"], data["med_desc_uz"], data["med_desc_ru"],
        data["med_category"], data["med_price"], data["med_unit"], requires_recipe
    )
    await state.clear()
    await message.answer(f"✅ Dori qo'shildi: *{data['med_name']}* — {data['med_price']:,} so'm", parse_mode="Markdown")

@router.callback_query(F.data == "admin_update_price")
async def start_update_price(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("💰 Dori ID sini kiriting:")
    await state.set_state(AdminStates.update_price_id)
    await callback.answer()

@router.message(AdminStates.update_price_id)
async def update_price_id(message: Message, state: FSMContext):
    med = await db.get_medicine(int(message.text))
    if not med:
        await message.answer("❌ Dori topilmadi.")
        return
    await state.update_data(update_med_id=int(message.text))
    await message.answer(f"💊 {med['name']}\nJoriy narx: {med['price']:,} so'm\n\nYangi narxni kiriting:")
    await state.set_state(AdminStates.update_price_value)

@router.message(AdminStates.update_price_value)
async def update_price_value(message: Message, state: FSMContext):
    data = await state.get_data()
    new_price = int(message.text)
    await db.update_medicine_price(data["update_med_id"], new_price)
    await state.clear()
    await message.answer(f"✅ Narx yangilandi: {new_price:,} so'm")

# === STATISTIKA ===
@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = await db.get_statistics()
    text = (
        f"📊 *Statistika*\n\n"
        f"👤 Jami foydalanuvchilar: {stats['total_users']}\n"
        f"📦 Jami buyurtmalar: {stats['total_orders']}\n"
        f"🆕 Yangi buyurtmalar: {stats['new_orders']}\n"
        f"📅 Bugungi buyurtmalar: {stats['today_orders']}\n"
        f"💰 Jami daromad: {stats['total_revenue']:,} so'm"
    )
    await message.answer(text, parse_mode="Markdown")
