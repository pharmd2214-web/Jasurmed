from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin Telegram ID lari (bir nechta bo'lishi mumkin)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# Database
DB_NAME = "jasurmed.db"

# Bonus tizimi
BONUS_RATE = 10000  # har 10,000 so'm = 1 bal

# Dorixona ma'lumotlari
PHARMACY_NAME = "JasurMED Farm"
PHARMACY_ADDRESS = "Manzilni kiriting"
PHARMACY_PHONE = "+998 XX XXX XX XX"
PHARMACY_WORK_HOURS = "08:00 - 21:00"

# To'lov usullari
PAYME_URL = "https://payme.uz/..."
CLICK_URL = "https://my.click.uz/..."
