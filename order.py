from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.main import delivery_keyboard, payment_keyboard, bonus_keyboard, confirm_order_keyboard, main_menu_keyboard
from utils.texts import t
from config import ADMIN_IDS, BONUS_RATE

router = Router()

# Savatni FSM da saqlaymiz: {medicine_id: {name, price, qty}}
class OrderState(StatesGroup):
    choosing_delivery = State()
    entering_address = State()
    choosing_payment = State()
    choosing_bonus = State()
    confirming = State()

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    medicine_id = int(callback.data.split("_")[1])

    med = await db.get_medicine(medicine_id)
    if not med:
        await callback.answer("Topilmadi", show_alert=True)
        return

    data = await state.get_data()
    cart = data.get("cart", {})

    med_key = str(medicine_id)
    if med_key in cart:
        cart[med_key]["qty"] += 1
    else:
        cart[med_key] = {"name": med["name"], "price": med["price"], "qty": 1}

    await state.update_data(cart=cart)

    total_items = sum(v["qty"] for v in cart.values())
    msg = f"✅ Savatga qo'shildi!\n🛒 Savat: {total_items} ta" if lang == "uz" else f"✅ Добавлено в корзину!\n🛒 В корзине: {total_items} шт."
    await callback.answer(msg, show_alert=True)

@router.message(F.text.in_(["🛒 Buyurtma berish", "🛒 Оформить заказ"]))
async def start_order(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return

    lang = user["language"]
    data = await state.get_data()
    cart = data.get("cart", {})

    if not cart:
        await message.answer(t("cart_empty", lang))
        return

    # Savat tarkibini ko'rsatish
    cart_text = "🛒 *Savatingiz:*\n\n" if lang == "uz" else "🛒 *Ваша корзина:*\n\n"
    total = 0
    for item in cart.values():
        subtotal = item["price"] * item["qty"]
        total += subtotal
        cart_text += f"• {item['name']} x{item['qty']} = {subtotal:,} so'm\n"
    cart_text += f"\n💰 Jami: *{total:,} so'm*" if lang == "uz" else f"\n💰 Итого: *{total:,} сум*"

    await message.answer(cart_text, parse_mode="Markdown")
    await message.answer(t("choose_delivery", lang), reply_markup=delivery_keyboard(lang))
    await state.set_state(OrderState.choosing_delivery)

@router.callback_query(F.data.startswith("delivery_"), OrderState.choosing_delivery)
async def choose_delivery(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    delivery_type = callback.data.split("_")[1]

    await state.update_data(delivery_type=delivery_type)

    if delivery_type == "courier":
        await callback.message.edit_text(t("enter_address", lang))
        await state.set_state(OrderState.entering_address)
    else:
        await state.update_data(delivery_address=None)
        await callback.message.edit_text(t("choose_payment", lang), reply_markup=payment_keyboard(lang))
        await state.set_state(OrderState.choosing_payment)

@router.message(OrderState.entering_address)
async def enter_address(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"
    await state.update_data(delivery_address=message.text)
    await message.answer(t("choose_payment", lang), reply_markup=payment_keyboard(lang))
    await state.set_state(OrderState.choosing_payment)

@router.callback_query(F.data.startswith("pay_"), OrderState.choosing_payment)
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    payment = callback.data.split("_")[1]
    await state.update_data(payment=payment)

    bonus = await db.get_user_bonus(callback.from_user.id)
    if bonus > 0:
        bonus_value = bonus * BONUS_RATE // 10
        await callback.message.edit_text(
            t("use_bonus", lang, points=bonus, value=bonus_value),
            reply_markup=bonus_keyboard(lang),
            parse_mode="Markdown"
        )
        await state.set_state(OrderState.choosing_bonus)
    else:
        await state.update_data(bonus_used=0)
        await show_order_summary(callback.message, state, user, lang)

@router.callback_query(F.data.startswith("bonus_"), OrderState.choosing_bonus)
async def choose_bonus(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"

    if callback.data == "bonus_yes":
        bonus = await db.get_user_bonus(callback.from_user.id)
        await state.update_data(bonus_used=bonus)
    else:
        await state.update_data(bonus_used=0)

    await show_order_summary(callback.message, state, user, lang)

async def show_order_summary(message, state: FSMContext, user, lang):
    data = await state.get_data()
    cart = data.get("cart", {})
    delivery_type = data.get("delivery_type", "pickup")
    delivery_address = data.get("delivery_address")
    payment = data.get("payment", "cash")
    bonus_used = data.get("bonus_used", 0)

    total = sum(v["price"] * v["qty"] for v in cart.values())
    bonus_discount = bonus_used * (BONUS_RATE // 10)
    final_total = max(0, total - bonus_discount)

    delivery_text = "🚚 Yetkazib berish" if delivery_type == "courier" else "🏪 O'zi olib ketish"
    if lang == "ru":
        delivery_text = "🚚 Доставка" if delivery_type == "courier" else "🏪 Самовывоз"

    payment_names = {"cash": "💵 Naqd", "payme": "💳 Payme", "click": "💳 Click"}

    summary = f"📋 *Buyurtma xulosasi:*\n\n" if lang == "uz" else f"📋 *Сводка заказа:*\n\n"
    for item in cart.values():
        summary += f"• {item['name']} x{item['qty']} = {item['price']*item['qty']:,} so'm\n"
    summary += f"\n💰 Jami: {total:,} so'm\n"
    if bonus_used > 0:
        summary += f"🎁 Bonus: -{bonus_discount:,} so'm\n"
    summary += f"💳 To'lov: {final_total:,} so'm\n"
    summary += f"\n{delivery_text}"
    if delivery_address:
        summary += f"\n📍 {delivery_address}"
    summary += f"\n{payment_names.get(payment, payment)}"

    await state.update_data(final_total=final_total)

    confirm_kb = confirm_order_keyboard(lang)
    try:
        await message.edit_text(summary, reply_markup=confirm_kb, parse_mode="Markdown")
    except:
        await message.answer(summary, reply_markup=confirm_kb, parse_mode="Markdown")

    await state.set_state(OrderState.confirming)

@router.callback_query(F.data == "confirm_order", OrderState.confirming)
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    data = await state.get_data()

    cart = data.get("cart", {})
    delivery_type = data.get("delivery_type", "pickup")
    delivery_address = data.get("delivery_address")
    payment = data.get("payment", "cash")
    bonus_used = data.get("bonus_used", 0)
    final_total = data.get("final_total", 0)

    # Buyurtmani saqlash
    order_id = await db.create_order(
        callback.from_user.id, final_total, bonus_used,
        delivery_type, delivery_address, payment
    )

    for med_id, item in cart.items():
        await db.add_order_item(order_id, int(med_id), item["qty"], item["price"])

    # Bonus hisoblash
    earned = await db.update_bonus(callback.from_user.id, final_total, bonus_used)

    # Foydalanuvchiga xabar
    await callback.message.edit_text(
        t("order_confirmed", lang, order_id=order_id, total=f"{final_total:,}", earned=earned),
        parse_mode="Markdown"
    )

    # Adminga xabar
    admin_text = (
        f"🔔 *Yangi buyurtma #{order_id}*\n\n"
        f"👤 {user['full_name']} | {user['phone']}\n"
        f"💰 {final_total:,} so'm\n"
        f"🚗 {'Yetkazib berish' if delivery_type == 'courier' else 'O\'zi oladi'}\n"
    )
    if delivery_address:
        admin_text += f"📍 {delivery_address}\n"
    admin_text += f"💳 {payment}"

    from keyboards.admin import order_actions_keyboard
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id, admin_text,
                reply_markup=order_actions_keyboard(order_id),
                parse_mode="Markdown"
            )
        except:
            pass

    # Savatni tozalash
    await state.update_data(cart={})
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    await state.clear()
    await callback.message.edit_text("❌ Buyurtma bekor qilindi." if lang == "uz" else "❌ Заказ отменён.")
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))

@router.message(F.text.in_(["📦 Buyurtmalarim", "📦 Мои заказы"]))
async def my_orders(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return

    lang = user["language"]
    orders = await db.get_user_orders(message.from_user.id)

    if not orders:
        text = "📦 Hali buyurtmalar yo'q." if lang == "uz" else "📦 Заказов пока нет."
        await message.answer(text)
        return

    status_names = {
        "new": "🆕 Yangi" if lang == "uz" else "🆕 Новый",
        "accepted": "✅ Qabul qilindi" if lang == "uz" else "✅ Принят",
        "preparing": "🔄 Tayyorlanmoqda" if lang == "uz" else "🔄 Готовится",
        "delivering": "🚚 Yo'lda" if lang == "uz" else "🚚 В пути",
        "completed": "✅ Yetkazildi" if lang == "uz" else "✅ Доставлен",
        "cancelled": "❌ Bekor" if lang == "uz" else "❌ Отменён"
    }

    text = "📦 *Buyurtmalarim:*\n\n" if lang == "uz" else "📦 *Мои заказы:*\n\n"
    for order in orders:
        status = status_names.get(order["status"], order["status"])
        text += f"#{order['id']} — {order['total_price']:,} so'm | {status}\n"

    await message.answer(text, parse_mode="Markdown")
