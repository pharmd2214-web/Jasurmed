from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.main import main_menu_keyboard, back_keyboard
from utils.texts import t
from config import ADMIN_IDS

router = Router()

class ConsultationState(StatesGroup):
    waiting_question = State()

@router.message(F.text.in_(["👨‍⚕️ Farmatsevt maslahat", "👨‍⚕️ Консультация фармацевта"]))
async def start_consultation(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return
    lang = user["language"]
    await message.answer(t("enter_question", lang), reply_markup=back_keyboard(lang))
    await state.set_state(ConsultationState.waiting_question)

@router.message(ConsultationState.waiting_question, F.text)
async def receive_question(message: Message, state: FSMContext, bot: Bot):
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"

    consult_id = await db.create_consultation(message.from_user.id, message.text)
    await message.answer(t("consultation_received", lang), reply_markup=main_menu_keyboard(lang))
    await state.clear()

    from keyboards.admin import consultation_actions_keyboard
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"👨‍⚕️ *Yangi savol #{consult_id}*\n\n"
                f"👤 {user['full_name']} | {user['phone']}\n\n"
                f"❓ {message.text}",
                reply_markup=consultation_actions_keyboard(consult_id, message.from_user.id),
                parse_mode="Markdown"
            )
        except:
            pass
