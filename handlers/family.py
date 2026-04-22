from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_conn
from datetime import datetime
from config import MY_ID, WIFE_ID
from utils.calendar_helper import show_calendar, process_calendar

F_TASK, F_DATE_TITLE, F_DATE_DATE = range(50, 53)

def family_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 Mood Check-in", callback_data="family_mood")],
        [InlineKeyboardButton("📋 Shared Task", callback_data="family_task_add")],
        [InlineKeyboardButton("📅 Tambah Date Penting", callback_data="family_date_add")],
        [InlineKeyboardButton("🗓 Senarai Date", callback_data="family_date_list")],
        [InlineKeyboardButton("✅ Task List", callback_data="family_task_list")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def family_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👨‍👩 *Family Module*\n\nPilih:", parse_mode="Markdown", reply_markup=family_menu())

async def family_mood(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 Happy", callback_data="mood_happy"),
         InlineKeyboardButton("😐 Neutral", callback_data="mood_neutral")],
        [InlineKeyboardButton("😟 Stressed", callback_data="mood_stressed"),
         InlineKeyboardButton("😡 Angry", callback_data="mood_angry")],
        [InlineKeyboardButton("🔙 Family", callback_data="mod_family")],
    ])
    await query.edit_message_text("😊 *Mood Check-in*\n\nBagaimana perasaan kau sekarang?", parse_mode="Markdown", reply_markup=keyboard)

async def got_mood(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mood_map = {"mood_happy": "😊 Happy", "mood_neutral": "😐 Neutral",
                "mood_stressed": "😟 Stressed", "mood_angry": "😡 Angry"}
    mood = mood_map.get(query.data, "Neutral")
    conn = get_conn()
    conn.execute("INSERT INTO checkins (user_id, mood) VALUES (?,?)", (query.from_user.id, mood))
    conn.commit()
    conn.close()
    tips = {
        "mood_happy": "Bagus! Guna tenaga positif ni. 💪",
        "mood_neutral": "Ok je. Buat kerja perlahan-lahan.",
        "mood_stressed": "Ambil nafas dalam. Rehat 5 minit. ☕",
        "mood_angry": "Jangan buat keputusan besar sekarang. Rehat dulu. 🙏"
    }
    await query.edit_message_text(
        f"Mood direkod: {mood}\n\n{tips.get(query.data, '')}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Family", callback_data="mod_family")]]))

async def family_task_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨 Untuk Saya", callback_data="task_assign_me"),
         InlineKeyboardButton("👩 Untuk Wife", callback_data="task_assign_wife")],
    ])
    await query.edit_message_text("👨‍👩 Assign task kepada siapa?", reply_markup=keyboard)
    return F_TASK

async def got_assign(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["f_assign"] = MY_ID if query.data == "task_assign_me" else WIFE_ID
    await query.edit_message_text("📋 Nama task:")
    return F_TASK

async def got_family_task(update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    conn.execute("INSERT INTO shared_tasks (assigned_by, assigned_to, title) VALUES (?,?,?)",
        (update.effective_user.id, context.user_data.get("f_assign", MY_ID), update.message.text))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Task ditambah: {update.message.text}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍👩 Family", callback_data="mod_family")]]))
    return ConversationHandler.END

async def family_task_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM shared_tasks WHERE status='Pending' ORDER BY created_at DESC").fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada shared task.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Family", callback_data="mod_family")]]))
        return
    msg = "👨‍👩 *Shared Tasks:*\n\n"
    keyboard = []
    for r in rows:
        who = "👨 Saya" if r["assigned_to"] == MY_ID else "👩 Wife"
        msg += f"🔸 {r['title']} — {who}\n"
        keyboard.append([InlineKeyboardButton(f"✅ {r['title'][:25]}", callback_data=f"ftask_done_{r['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Family", callback_data="mod_family")])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def ftask_done(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tid = int(query.data.replace("ftask_done_", ""))
    conn = get_conn()
    conn.execute("UPDATE shared_tasks SET status='Done' WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    await query.edit_message_text("✅ Task siap!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍👩 Family", callback_data="mod_family")]]))

async def family_date_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📅 Nama tarikh penting:")
    return F_DATE_TITLE

async def got_date_title(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["f_date_title"] = update.message.text
    await update.message.reply_text("📅 Pilih tarikh:", reply_markup=show_calendar("family_date"))
    return F_DATE_DATE

async def family_date_calendar(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    result, key, step = process_calendar(query.data, "family_date")
    if result:
        date_str = result.strftime("%d-%m-%Y")
        conn = get_conn()
        conn.execute("INSERT INTO family_dates (title, date) VALUES (?,?)",
            (context.user_data["f_date_title"], date_str))
        conn.commit()
        conn.close()
        await query.edit_message_text(
            f"✅ Ditambah!\n\n📅 {context.user_data['f_date_title']}\n{date_str}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍👩 Family", callback_data="mod_family")]]))
        return ConversationHandler.END
    elif key:
        await query.edit_message_text("📅 Pilih tarikh:", reply_markup=key)
        return F_DATE_DATE

async def family_date_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM family_dates ORDER BY date ASC").fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada tarikh penting.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Family", callback_data="mod_family")]]))
        return
    msg = "📅 *Tarikh Penting:*\n\n"
    for r in rows:
        msg += f"🔸 {r['title']} — {r['date']}\n"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Family", callback_data="mod_family")]]))
