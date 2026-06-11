from aiogram import Router, F
from aiogram.types import Message

import database as db
from utils.texts import t
from config import BONUS_RATE

router = Router()

@router.message(F.text.in_(["🎁 Mening ballarim", "🎁 Мои бонусы"]))
async def show_bonus(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer(t("not_registered", "uz"))
        return
    lang = user["language"]
    points = user["bonus_points"]
    value = points * (BONUS_RATE // 10)
    await message.answer(
        t("bonus_info", lang, points=points, value=f"{value:,}"),
        parse_mode="Markdown"
    )
