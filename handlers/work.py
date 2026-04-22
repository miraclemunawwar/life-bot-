from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_conn

W_CLIENT, W_TASK, W_INCOME_AMT, W_INCOME_SRC = range(40, 44)

def work_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Tambah Task", callback_data="work_add")],
        [InlineKeyboardButton("📋 Senarai Task", callback_data="work_list")],
        [InlineKeyboardButton("💵 Rekod Income", callback_data="work_income_add")],
        [InlineKeyboardButton("📊 Summary Income", callback_data="work_income_list")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def work_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💼 *Work Module*\n\nPilih:", parse_mode="Markdown", reply_markup=work_menu())

async def work_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🏢 Nama client / site:")
    return W_CLIENT

async def got_client(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["w_client"] = update.message.text
    await update.message.reply_text("📋 Nama task:")
    return W_TASK

async def got_task(update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    conn.execute("INSERT INTO work_tasks (user_id, client, task) VALUES (?,?,?)",
        (update.effective_user.id, context.user_data["w_client"], update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Task ditambah!\n\n🏢 {context.user_data['w_client']}\n📋 {update.message.text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💼 Work", callback_data="mod_work")]]))
    return ConversationHandler.END

async def work_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM work_tasks WHERE user_id=? AND status!='Done' ORDER BY created_at DESC",
        (query.from_user.id,)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada task pending.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Work", callback_data="mod_work")]]))
        return
    msg = "💼 *Task Pending:*\n\n"
    keyboard = []
    for r in rows:
        msg += f"🔸 *{r['task']}*\n   🏢 {r['client']} | {r['status']}\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ Done: {r['task'][:20]}", callback_data=f"work_done_{r['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Work", callback_data="mod_work")])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def work_done(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = int(query.data.replace("work_done_", ""))
    conn = get_conn()
    conn.execute("UPDATE work_tasks SET status='Done' WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    await query.edit_message_text("✅ Task siap!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💼 Work", callback_data="mod_work")]]))

async def work_income_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💵 Jumlah income (RM):")
    return W_INCOME_AMT

async def got_income_amt(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["w_income"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return W_INCOME_AMT
    await update.message.reply_text("📌 Sumber income:")
    return W_INCOME_SRC

async def got_income_src(update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    conn.execute("INSERT INTO income (user_id, amount, source) VALUES (?,?,?)",
        (update.effective_user.id, context.user_data["w_income"], update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Income direkod!\n\n💵 RM{context.user_data['w_income']:.2f}\n📌 {update.message.text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💼 Work", callback_data="mod_work")]]))
    return ConversationHandler.END

async def work_income_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM income WHERE user_id=? ORDER BY date DESC LIMIT 10",
        (query.from_user.id,)).fetchall()
    total = conn.execute("SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=?",
        (query.from_user.id,)).fetchone()[0]
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada rekod income.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Work", callback_data="mod_work")]]))
        return
    msg = "💵 *Income Terkini:*\n\n"
    for r in rows:
        msg += f"✅ RM{r['amount']:.2f} — {r['source']} | {r['date']}\n"
    msg += f"\n💰 *Total: RM{total:.2f}*"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Work", callback_data="mod_work")]]))
