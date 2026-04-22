from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_conn
from datetime import datetime, date
from utils.calendar_helper import show_calendar, process_calendar

S_TITLE, S_SUBJECT, S_PROGRESS = range(10, 13)

def study_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Tambah Assignment", callback_data="study_add")],
        [InlineKeyboardButton("📋 Semua Assignment", callback_data="study_list")],
        [InlineKeyboardButton("🚨 Urgent (≤3 hari)", callback_data="study_urgent")],
        [InlineKeyboardButton("⏱ Focus Timer", callback_data="study_timer")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def study_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📚 *Study Module*\n\nPilih:", parse_mode="Markdown", reply_markup=study_menu())

async def study_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 Nama assignment:")
    return S_TITLE

async def got_title(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_title"] = update.message.text
    await update.message.reply_text("📖 Nama subjek:")
    return S_SUBJECT

async def got_subject(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["s_subject"] = update.message.text
    await update.message.reply_text(
        "📅 Pilih deadline:",
        reply_markup=show_calendar("study")
    )
    return S_PROGRESS

async def got_progress(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        prog = int(update.message.text.strip())
        if not 0 <= prog <= 100:
            raise ValueError
    except:
        await update.message.reply_text("Taip nombor 0-100:")
        return S_PROGRESS
    conn = get_conn()
    conn.execute(
        "INSERT INTO assignments (user_id, title, subject, deadline, progress) VALUES (?,?,?,?,?)",
        (update.effective_user.id, context.user_data["s_title"],
         context.user_data["s_subject"], context.user_data["s_deadline"], prog)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Ditambah!\n\n📝 {context.user_data['s_title']}\n"
        f"📖 {context.user_data['s_subject']}\n"
        f"📅 Due: {context.user_data['s_deadline']}\n"
        f"📊 Progress: {prog}%",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 Study", callback_data="mod_study")]]))
    return ConversationHandler.END

async def study_calendar_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    result, key, step = process_calendar(query.data, "study")
    if result:
        context.user_data["s_deadline"] = result.strftime("%d-%m-%Y")
        await query.edit_message_text(
            f"📅 Deadline: *{context.user_data['s_deadline']}*\n\n📊 Progress sekarang? (0-100)\nTaip 0 kalau baru mula:",
            parse_mode="Markdown"
        )
        return S_PROGRESS
    elif key:
        await query.edit_message_text("📅 Pilih deadline:", reply_markup=key)
        return S_PROGRESS
    return S_PROGRESS

async def study_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM assignments WHERE user_id=? AND done=0 ORDER BY deadline ASC",
        (query.from_user.id,)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada assignment.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Study", callback_data="mod_study")]]))
        return
    msg = "📋 *Assignment Kau:*\n\n"
    today = date.today()
    for r in rows:
        try:
            due = datetime.strptime(r["deadline"], "%d-%m-%Y").date()
            days = (due - today).days
            alert = " 🚨" if days <= 3 else ""
        except:
            alert = ""
        msg += f"{alert}📝 *{r['title']}*\n   📖 {r['subject']} | 📅 {r['deadline']} | 📊 {r['progress']}%\n\n"
    keyboard = []
    for r in rows:
        keyboard.append([InlineKeyboardButton(f"✅ Siap: {r['title'][:25]}", callback_data=f"study_done_{r['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Study", callback_data="mod_study")])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def study_urgent(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute("SELECT * FROM assignments WHERE user_id=? AND done=0", (query.from_user.id,)).fetchall()
    conn.close()
    today = date.today()
    urgent = []
    for r in rows:
        try:
            due = datetime.strptime(r["deadline"], "%d-%m-%Y").date()
            days = (due - today).days
            if days <= 3:
                urgent.append((r, days))
        except:
            pass
    if not urgent:
        await query.edit_message_text("✅ Tiada assignment urgent!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Study", callback_data="mod_study")]]))
        return
    msg = "🚨 *URGENT — ≤ 3 Hari:*\n\n"
    for r, days in urgent:
        label = "HARI INI!" if days == 0 else (f"OVERDUE {abs(days)} hari!" if days < 0 else f"{days} hari lagi")
        msg += f"🔴 *{r['title']}*\n   {r['subject']} | {label}\n\n"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Study", callback_data="mod_study")]]))

async def study_done(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    aid = int(query.data.replace("study_done_", ""))
    conn = get_conn()
    conn.execute("UPDATE assignments SET done=1 WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    await query.edit_message_text("✅ Assignment ditandakan siap!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📚 Study", callback_data="mod_study")]]))

async def study_timer(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱ 25 Minit (Pomodoro)", callback_data="timer_25")],
        [InlineKeyboardButton("⏱ 50 Minit (Deep Work)", callback_data="timer_50")],
        [InlineKeyboardButton("🔙 Study", callback_data="mod_study")],
    ])
    await query.edit_message_text("⏱ *Focus Timer*\n\nPilih masa:", parse_mode="Markdown", reply_markup=keyboard)

async def timer_start(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mins = 25 if query.data == "timer_25" else 50
    await query.edit_message_text(
        f"⏱ *Focus Mode: {mins} Minit*\n\nMula sekarang. Fokus!\nSaya akan notify bila habis.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Study", callback_data="mod_study")]]))
    context.job_queue.run_once(timer_done, when=mins*60, chat_id=query.message.chat_id, data={"mins": mins})

async def timer_done(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"🔔 *{context.job.data['mins']} minit habis!*\n\nRehat 5 minit. Bagus!",
        parse_mode="Markdown")
