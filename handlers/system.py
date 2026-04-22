from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import get_conn
from datetime import date, datetime

def system_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Top 3 Prioriti Hari Ini", callback_data="sys_priority")],
        [InlineKeyboardButton("📊 Weekly Review", callback_data="sys_weekly")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def system_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ *System*\n\nPilih:", parse_mode="Markdown", reply_markup=system_menu())

async def sys_priority(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = date.today()
    conn = get_conn()
    uid = query.from_user.id

    priorities = []

    # Urgent assignments
    assignments = conn.execute(
        "SELECT * FROM assignments WHERE user_id=? AND done=0", (uid,)).fetchall()
    for a in assignments:
        try:
            due = datetime.strptime(a["deadline"], "%d-%m-%Y").date()
            days = (due - today).days
            if days <= 3:
                priorities.append((0 - days, f"📚 URGENT: {a['title']} (due {days} hari)"))
        except:
            pass

    # Unpaid commitments due soon
    commits = conn.execute("SELECT * FROM commitments WHERE paid=0").fetchall()
    for c in commits:
        try:
            due = datetime.strptime(c["due_date"], "%d-%m-%Y").date()
            days = (due - today).days
            if days <= 5:
                priorities.append((1, f"💰 Bayar: {c['title']} RM{c['amount']:.0f} (due {days} hari)"))
        except:
            pass

    # Pending work tasks
    tasks = conn.execute(
        "SELECT * FROM work_tasks WHERE user_id=? AND status='Pending' LIMIT 2", (uid,)).fetchall()
    for t in tasks:
        priorities.append((2, f"💼 Task: {t['task']} — {t['client']}"))

    conn.close()

    priorities.sort(key=lambda x: x[0])
    top3 = priorities[:3]

    if not top3:
        msg = "✅ *Tiada prioriti urgent hari ini.*\n\nLadang lah dulu! 💪"
    else:
        msg = f"🎯 *Top Prioriti Hari Ini ({today}):*\n\n"
        for i, (_, item) in enumerate(top3, 1):
            msg += f"{i}. {item}\n\n"

    await query.edit_message_text(msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 System", callback_data="mod_system")]]))

async def sys_weekly(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    conn = get_conn()
    month = date.today().strftime("%Y-%m")

    # Expenses
    total_exp = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND date LIKE ?",
        (uid, f"{month}%")).fetchone()[0]

    # Income
    total_income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM income WHERE user_id=? AND date LIKE ?",
        (uid, f"{month}%")).fetchone()[0]

    # Assignments
    done_assign = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE user_id=? AND done=1", (uid,)).fetchone()[0]
    pending_assign = conn.execute(
        "SELECT COUNT(*) FROM assignments WHERE user_id=? AND done=0", (uid,)).fetchone()[0]

    # Trades
    trades = conn.execute(
        "SELECT * FROM trades WHERE user_id=? AND date LIKE ?",
        (uid, f"{month}%")).fetchall()
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    pnl = sum(t["pnl"] for t in trades)

    # Work tasks
    done_tasks = conn.execute(
        "SELECT COUNT(*) FROM work_tasks WHERE user_id=? AND status='Done'", (uid,)).fetchone()[0]

    conn.close()

    msg = (
        f"📊 *Weekly Review — {month}*\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 *Finance*\n"
        f"Income: RM{total_income:.2f}\n"
        f"Belanja: RM{total_exp:.2f}\n"
        f"Baki: RM{total_income - total_exp:.2f}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📚 *Study*\n"
        f"Siap: {done_assign} | Pending: {pending_assign}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📈 *Trading*\n"
        f"Trade: {len(trades)} | W: {wins} | L: {losses}\n"
        f"P&L: ${pnl:.2f}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💼 *Work*\n"
        f"Task siap: {done_tasks}\n"
    )

    await query.edit_message_text(msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 System", callback_data="mod_system")]]))
