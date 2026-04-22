from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ALLOWED_USERS

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Study", callback_data="mod_study"),
         InlineKeyboardButton("📈 Trading", callback_data="mod_trading")],
        [InlineKeyboardButton("💼 Work", callback_data="mod_work"),
         InlineKeyboardButton("👨‍👩 Family", callback_data="mod_family")],
        [InlineKeyboardButton("💰 Finance", callback_data="mod_finance"),
         InlineKeyboardButton("⚙️ System", callback_data="mod_system")],
    ])

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Akses ditolak.")
        return
    await update.message.reply_text(
        "👋 Salam! Life Management Bot\n\nPilih modul:",
        reply_markup=main_menu_keyboard()
    )

async def back_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 Home — Pilih modul:",
        reply_markup=main_menu_keyboard()
    )

async def any_message(update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Akses ditolak.")
        return
    await update.message.reply_text(
        "👋 Salam! Life Management Bot\n\nPilih modul:",
        reply_markup=main_menu_keyboard()
    )
