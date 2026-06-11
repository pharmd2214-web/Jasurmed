from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards.main import language_keyboard, phone_keyboard, main_menu_keyboard
from utils.texts import t
from config import PHARMACY_NAME, PHARMACY_ADDRESS, PHARMACY_PHONE, PHARMACY_WORK_HOURS

router = Router()

class Registration(StatesGroup):
    choosing_language = State()
    entering_name = State()
    entering_phone = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if user:
        lang = user["language"]
        await message.answer(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))
    else:
        await message.answer(t("choose_language", "uz"), reply_markup=language_keyboard())
        await state.set_state(Registration.choosing_language)

@router.callback_query(F.data.startswith("lang_"), Registration.choosing_language)
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    await callback.message.edit_text(t("welcome", lang))
    await state.set_state(Registration.entering_name)
    await callback.answer()

@router.message(Registration.entering_name)
async def enter_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    await state.update_data(full_name=message.text)
    await message.answer(t("enter_phone", lang), reply_markup=phone_keyboard(lang))
    await state.set_state(Registration.entering_phone)

@router.message(Registration.entering_phone, F.contact)
async def enter_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", "uz")
    phone = message.contact.phone_number
    full_name = data.get("full_name", message.from_user.full_name)

    await db.create_user(message.from_user.id, full_name, phone, lang)
    await state.clear()

    await message.answer(
        t("registration_done", lang, name=full_name),
        reply_markup=main_menu_keyboard(lang)
    )

@router.message(F.text == "ℹ️ Ma'lumot")
@router.message(F.text == "ℹ️ Информация")
async def pharmacy_info(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"
    await message.answer(
        t("pharmacy_info", lang,
          address=PHARMACY_ADDRESS,
          phone=PHARMACY_PHONE,
          hours=PHARMACY_WORK_HOURS),
        parse_mode="Markdown"
    )
