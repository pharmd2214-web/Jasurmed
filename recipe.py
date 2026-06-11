from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.main import main_menu_keyboard, back_keyboard
from utils.texts import t
from config import ADMIN_IDS

router = Router()

class RecipeState(StatesGroup):
    waiting_photo = State()

@router.message(F.text.in_(["📋 Retsept yuborish", "📋 Отправить рецепт"]))
async def start_recipe(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return
    lang = user["language"]
    await message.answer(t("send_recipe_photo", lang), reply_markup=back_keyboard(lang))
    await state.set_state(RecipeState.waiting_photo)

@router.message(RecipeState.waiting_photo, F.photo)
async def receive_recipe(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"

    photo_id = message.photo[-1].file_id
    recipe_id = await db.create_recipe(message.from_user.id, photo_id)

    await message.answer(t("recipe_received", lang), reply_markup=main_menu_keyboard(lang))
    await state.clear()

    # Adminga xabar
    from keyboards.admin import recipe_actions_keyboard
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                admin_id,
                photo=photo_id,
                caption=(
                    f"📋 *Yangi retsept #{recipe_id}*\n\n"
                    f"👤 {user['full_name']} | {user['phone']}"
                ),
                reply_markup=recipe_actions_keyboard(recipe_id, message.from_user.id),
                parse_mode="Markdown"
            )
        except:
            pass
