from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.main import categories_keyboard, medicines_keyboard, medicine_detail_keyboard, main_menu_keyboard
from utils.texts import t

router = Router()

class CatalogState(StatesGroup):
    searching = State()

@router.message(F.text.in_(["💊 Dorilar katalogi", "💊 Каталог лекарств"]))
async def show_catalog(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return

    lang = user["language"]
    categories = await db.get_all_categories()

    if not categories:
        await message.answer("📂 Kategoriyalar mavjud emas." if lang == "uz" else "📂 Категории отсутствуют.")
        return

    await message.answer(t("choose_category", lang), reply_markup=categories_keyboard(categories, lang))

@router.callback_query(F.data.startswith("cat_"))
async def show_medicines(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    category_id = int(callback.data.split("_")[1])

    medicines = await db.get_medicines_by_category(category_id)
    if not medicines:
        await callback.answer(t("no_medicines", lang), show_alert=True)
        return

    await callback.message.edit_text(
        "💊 Dorilar:" if lang == "uz" else "💊 Лекарства:",
        reply_markup=medicines_keyboard(medicines, lang)
    )

@router.callback_query(F.data.startswith("med_"))
async def show_medicine_detail(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    medicine_id = int(callback.data.split("_")[1])

    med = await db.get_medicine(medicine_id)
    if not med:
        await callback.answer("Topilmadi", show_alert=True)
        return

    desc = med["description_uz"] if lang == "uz" else med["description_ru"]
    status = "✅ Mavjud" if lang == "uz" else "✅ В наличии"
    if not med["in_stock"]:
        status = "❌ Mavjud emas" if lang == "uz" else "❌ Нет в наличии"

    recipe_note = ""
    if med["requires_recipe"]:
        recipe_note = "\n⚠️ Retsept talab qilinadi" if lang == "uz" else "\n⚠️ Требуется рецепт"

    text = (
        f"💊 *{med['name']}*\n\n"
        f"📝 {desc or '-'}\n\n"
        f"💰 Narx: *{med['price']:,} so'm*\n"
        f"📦 Birlik: {med['unit']}\n"
        f"{status}{recipe_note}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=medicine_detail_keyboard(medicine_id, lang),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    categories = await db.get_all_categories()
    await callback.message.edit_text(
        t("choose_category", lang),
        reply_markup=categories_keyboard(categories, lang)
    )

@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    await callback.message.delete()
    await callback.message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
