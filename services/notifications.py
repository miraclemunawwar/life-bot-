from db import get_conn
from datetime import date, datetime
from config import MY_ID, WIFE_ID

async def daily_reminders(context):
    """Hantar pukul 8 pagi — assignment & commitment reminder sahaja."""
    today = date.today()
    notify = [MY_ID]
    if WIFE_ID != 0:
        notify.append(WIFE_ID)

    conn = get_conn()

    # Assignment reminders
    rows = conn.execute("SELECT * FROM assignments WHERE done=0").fetchall()
    for r in rows:
        try:
            due = datetime.strptime(r["deadline"], "%d-%m-%Y").date()
            days = (due - today).days
            if days in [3, 1, 0]:
                label = "HARI INI DUE! 🚨" if days == 0 else f"{days} hari lagi ⚠️"
                msg = f"📚 *Assignment Reminder*\n\n{r['title']}\n{r['subject']}\nDue: {r['deadline']} — {label}"
                await context.bot.send_message(chat_id=r["user_id"], text=msg, parse_mode="Markdown")
        except:
            pass

    # Commitment reminders
    commits = conn.execute("SELECT * FROM commitments WHERE paid=0").fetchall()
    for c in commits:
        try:
            due = datetime.strptime(c["due_date"], "%d-%m-%Y").date()
            days = (due - today).days
            if days in [3, 1, 0]:
                label = "HARI INI! 🚨" if days == 0 else f"{days} hari lagi ⚠️"
                msg = f"💰 *Bil Reminder*\n\n{c['title']}\nRM{c['amount']:.2f}\nDue: {c['due_date']} — {label}"
                for uid in notify:
                    await context.bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
        except:
            pass

    # Family date reminders
    dates = conn.execute("SELECT * FROM family_dates WHERE reminded=0").fetchall()
    for d in dates:
        try:
            due = datetime.strptime(d["date"], "%d-%m-%Y").date()
            days = (due - today).days
            if days in [3, 1, 0]:
                label = "HARI INI! 🎉" if days == 0 else f"{days} hari lagi"
                msg = f"📅 *Date Reminder*\n\n{d['title']}\n{d['date']} — {label}"
                for uid in notify:
                    await context.bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
        except:
            pass

    conn.close()

async def evening_checkin(context):
    """Hantar pukul 8 malam — family check-in."""
    notify = [MY_ID]
    if WIFE_ID != 0:
        notify.append(WIFE_ID)
    for uid in notify:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text="👨‍👩 *Daily Reminder*\n\nDah luangkan masa bersama hari ini? 💕",
                parse_mode="Markdown"
            )
        except:
            pass
