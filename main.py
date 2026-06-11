from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from utils.texts import t

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])

def phone_keyboard(lang="uz"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_share_phone", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu_keyboard(lang="uz"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_catalog", lang)), KeyboardButton(text=t("btn_order", lang))],
            [KeyboardButton(text=t("btn_recipe", lang)), KeyboardButton(text=t("btn_consultation", lang))],
            [KeyboardButton(text=t("btn_bonus", lang)), KeyboardButton(text=t("btn_my_orders", lang))],
            [KeyboardButton(text=t("btn_info", lang))]
        ],
        resize_keyboard=True
    )

def back_keyboard(lang="uz"):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_back", lang))]],
        resize_keyboard=True
    )

def categories_keyboard(categories, lang="uz"):
    buttons = []
    for cat in categories:
        name = cat["name_uz"] if lang == "uz" else cat["name_ru"]
        buttons.append([InlineKeyboardButton(
            text=name,
            callback_data=f"cat_{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def medicines_keyboard(medicines, lang="uz"):
    buttons = []
    for med in medicines:
        buttons.append([InlineKeyboardButton(
            text=f"💊 {med['name']} — {med['price']:,} so'm",
            callback_data=f"med_{med['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def medicine_detail_keyboard(medicine_id, lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Savatga qo'shish" if lang=="uz" else "🛒 В корзину", callback_data=f"add_{medicine_id}")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_medicines")]
    ])

def delivery_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_delivery", lang), callback_data="delivery_courier")],
        [InlineKeyboardButton(text=t("btn_pickup", lang), callback_data="delivery_pickup")]
    ])

def payment_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_cash", lang), callback_data="pay_cash")],
        [InlineKeyboardButton(text=t("btn_payme", lang), callback_data="pay_payme")],
        [InlineKeyboardButton(text=t("btn_click", lang), callback_data="pay_click")]
    ])

def bonus_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_use_bonus", lang), callback_data="bonus_yes")],
        [InlineKeyboardButton(text=t("btn_skip_bonus", lang), callback_data="bonus_no")]
    ])

def confirm_order_keyboard(lang="uz"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash" if lang=="uz" else "✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Bekor qilish" if lang=="uz" else "❌ Отменить", callback_data="cancel_order")]
    ])
