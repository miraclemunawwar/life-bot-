from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_conn
from datetime import date
from utils.calendar_helper import show_calendar, process_calendar

FIN_AMT, FIN_CAT, FIN_NOTE, COMMIT_TITLE, COMMIT_AMT, COMMIT_DUE = range(60, 66)

CATEGORIES = ["🍔 Makan", "⛽ Minyak", "🏠 Rumah", "💊 Kesihatan", "👕 Pakaian", "📱 Bil", "🎮 Hiburan", "📦 Lain-lain"]

def finance_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Tambah Perbelanjaan", callback_data="fin_add")],
        [InlineKeyboardButton("📊 Overview Bulan Ini", callback_data="fin_overview")],
        [InlineKeyboardButton("📋 Komitmen / Bil", callback_data="fin_commit_list")],
        [InlineKeyboardButton("➕ Tambah Komitmen", callback_data="fin_commit_add")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def finance_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💰 *Finance Module*\n\nPilih:", parse_mode="Markdown", reply_markup=finance_menu())

async def fin_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💵 Jumlah (RM):")
    return FIN_AMT

async def got_fin_amt(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["fin_amt"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return FIN_AMT
    keyboard = [[InlineKeyboardButton(c, callback_data=f"fincat_{c}")] for c in CATEGORIES]
    await update.message.reply_text("📂 Kategori:", reply_markup=InlineKeyboardMarkup(keyboard))
    return FIN_CAT

async def got_fin_cat(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["fin_cat"] = query.data.replace("fincat_", "")
    await query.edit_message_text("📝 Note (atau taip skip):")
    return FIN_NOTE

async def got_fin_note(update, context: ContextTypes.DEFAULT_TYPE):
    note = update.message.text.strip()
    if note.lower() == "skip":
        note = ""
    conn = get_conn()
    conn.execute("INSERT INTO expenses (user_id, amount, category, note) VALUES (?,?,?,?)",
        (update.effective_user.id, context.user_data["fin_amt"], context.user_data["fin_cat"], note))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Direkod!\n\n💵 RM{context.user_data['fin_amt']:.2f}\n📂 {context.user_data['fin_cat']}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Finance", callback_data="mod_finance")]]))
    return ConversationHandler.END

async def fin_overview(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    month = date.today().strftime("%Y-%m")
    conn = get_conn()
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE user_id=? AND date LIKE ? GROUP BY category",
        (query.from_user.id, f"{month}%")).fetchall()
    total = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND date LIKE ?",
        (query.from_user.id, f"{month}%")).fetchone()[0]
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada rekod bulan ini.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Finance", callback_data="mod_finance")]]))
        return
    msg = f"📊 *Overview {month}:*\n\n"
    for r in rows:
        msg += f"{r['category']}: RM{r['total']:.2f}\n"
    msg += f"\n💰 *Total: RM{total:.2f}*"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Finance", callback_data="mod_finance")]]))

async def fin_commit_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📋 Nama komitmen (contoh: Ansuran Kereta):")
    return COMMIT_TITLE

async def got_commit_title(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["c_title"] = update.message.text
    await update.message.reply_text("💵 Jumlah (RM):")
    return COMMIT_AMT

async def got_commit_amt(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["c_amt"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return COMMIT_AMT
    await update.message.reply_text("📅 Pilih tarikh due:", reply_markup=show_calendar("commit"))
    return COMMIT_DUE

async def commit_calendar(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    result, key, step = process_calendar(query.data, "commit")
    if result:
        date_str = result.strftime("%d-%m-%Y")
        conn = get_conn()
        conn.execute("INSERT INTO commitments (title, amount, due_date) VALUES (?,?,?)",
            (context.user_data["c_title"], context.user_data["c_amt"], date_str))
        conn.commit()
        conn.close()
        await query.edit_message_text(
            f"✅ Komitmen ditambah!\n\n📋 {context.user_data['c_title']}\n💵 RM{context.user_data['c_amt']:.2f}\n📅 {date_str}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Finance", callback_data="mod_finance")]]))
        return ConversationHandler.END
    elif key:
        await query.edit_message_text("📅 Pilih tarikh due:", reply_markup=key)
        return COMMIT_DUE

async def fin_commit_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM commitments WHERE paid=0 ORDER BY due_date ASC").fetchall()
    total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM commitments WHERE paid=0").fetchone()[0]
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada komitmen pending.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Finance", callback_data="mod_finance")]]))
        return
    msg = "📋 *Komitmen / Bil:*\n\n"
    keyboard = []
    for r in rows:
        msg += f"🔸 {r['title']} — RM{r['amount']:.2f} | Due: {r['due_date']}\n"
        keyboard.append([InlineKeyboardButton(f"✅ Bayar: {r['title'][:20]}", callback_data=f"commit_pay_{r['id']}")])
    msg += f"\n💰 *Total: RM{total:.2f}*"
    keyboard.append([InlineKeyboardButton("🔙 Finance", callback_data="mod_finance")])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def commit_pay(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = int(query.data.replace("commit_pay_", ""))
    conn = get_conn()
    conn.execute("UPDATE commitments SET paid=1 WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    await query.edit_message_text("✅ Ditandakan bayar!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Finance", callback_data="mod_finance")]]))
