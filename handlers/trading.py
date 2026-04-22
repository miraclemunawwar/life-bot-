from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from db import get_conn
from datetime import date
from config import ALLOWED_USERS, DAILY_LOSS_LIMIT

# States
T_PAIR, T_ENTRY, T_EXIT, T_LOT, T_SETUP, T_RESULT, T_PNL, T_NOTES = range(20, 28)
CHECKLIST_SETUP, CHECKLIST_RISK, CHECKLIST_EMOTION = range(28, 31)

def trading_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Log Trade", callback_data="trade_add")],
        [InlineKeyboardButton("📋 Semua Trade", callback_data="trade_list")],
        [InlineKeyboardButton("📊 Summary Hari Ini", callback_data="trade_today")],
        [InlineKeyboardButton("⚠️ Daily Loss Status", callback_data="trade_loss")],
        [InlineKeyboardButton("🏠 Home", callback_data="back_home")],
    ])

async def trading_home(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📈 *Trading Module*\n\nPilih:", parse_mode="Markdown", reply_markup=trading_menu())

# PRE-TRADE CHECKLIST
async def trade_add(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["checklist"] = {}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ya, setup valid", callback_data="chk_setup_yes"),
         InlineKeyboardButton("❌ Tidak", callback_data="chk_setup_no")],
    ])
    await query.edit_message_text(
        "📋 *Pre-Trade Checklist*\n\n1️⃣ Setup kau valid? (Ada konfirmasi?)",
        parse_mode="Markdown", reply_markup=keyboard
    )
    return CHECKLIST_SETUP

async def chk_setup(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "chk_setup_no":
        await query.edit_message_text("❌ Setup tidak valid. Jangan masuk trade.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
        return ConversationHandler.END
    context.user_data["checklist"]["setup"] = True
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Ya, risk ok", callback_data="chk_risk_yes"),
         InlineKeyboardButton("❌ Tidak", callback_data="chk_risk_no")],
    ])
    await query.edit_message_text(
        "📋 *Pre-Trade Checklist*\n\n2️⃣ Risk managed? (SL dah set?)",
        parse_mode="Markdown", reply_markup=keyboard
    )
    return CHECKLIST_RISK

async def chk_risk(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "chk_risk_no":
        await query.edit_message_text("❌ Set SL dulu sebelum masuk trade.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
        return ConversationHandler.END
    context.user_data["checklist"]["risk"] = True
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tenang & fokus", callback_data="chk_emo_yes"),
         InlineKeyboardButton("⚠️ Kurang stabil", callback_data="chk_emo_no")],
    ])
    await query.edit_message_text(
        "📋 *Pre-Trade Checklist*\n\n3️⃣ Emosi stabil?",
        parse_mode="Markdown", reply_markup=keyboard
    )
    return CHECKLIST_EMOTION

async def chk_emotion(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "chk_emo_no":
        await query.edit_message_text("⚠️ Emosi tak stabil. Rehat dulu. Jangan trade sekarang.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
        return ConversationHandler.END
    await query.edit_message_text("✅ *Checklist lulus!*\n\nTaip pair (contoh: XAUUSD):", parse_mode="Markdown")
    return T_PAIR

async def got_pair(update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["t_pair"] = update.message.text.upper().strip()
    await update.message.reply_text("📥 Entry price:")
    return T_ENTRY

async def got_entry(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["t_entry"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return T_ENTRY
    await update.message.reply_text("📤 Exit price (taip 0 kalau belum close):")
    return T_EXIT

async def got_exit(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["t_exit"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return T_EXIT
    await update.message.reply_text("📦 Lot size:")
    return T_LOT

async def got_lot(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["t_lot"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor sahaja:")
        return T_LOT
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Supply & Demand", callback_data="setup_sd")],
        [InlineKeyboardButton("Price Action", callback_data="setup_pa")],
        [InlineKeyboardButton("SMC / ICT", callback_data="setup_smc")],
        [InlineKeyboardButton("Other", callback_data="setup_other")],
    ])
    await update.message.reply_text("📊 Setup:", reply_markup=keyboard)
    return T_SETUP

async def got_setup(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    setup_map = {"setup_sd": "Supply & Demand", "setup_pa": "Price Action", "setup_smc": "SMC/ICT", "setup_other": "Other"}
    context.user_data["t_setup"] = setup_map.get(query.data, "Other")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ WIN", callback_data="result_win"),
         InlineKeyboardButton("❌ LOSS", callback_data="result_loss"),
         InlineKeyboardButton("➡️ BE", callback_data="result_be")],
    ])
    await query.edit_message_text("🏆 Hasil trade:", reply_markup=keyboard)
    return T_RESULT

async def got_result(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    result_map = {"result_win": "WIN", "result_loss": "LOSS", "result_be": "BE"}
    context.user_data["t_result"] = result_map.get(query.data, "BE")
    await query.edit_message_text("💵 P&L (USD)? Negatif untuk loss. Contoh: -25 atau 40")
    return T_PNL

async def got_pnl(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["t_pnl"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("Taip nombor. Contoh: -25 atau 40")
        return T_PNL
    await update.message.reply_text("📝 Notes (atau taip skip):")
    return T_NOTES

async def got_notes(update, context: ContextTypes.DEFAULT_TYPE):
    notes = update.message.text.strip()
    if notes.lower() == "skip":
        notes = ""
    u = context.user_data
    conn = get_conn()
    conn.execute(
        "INSERT INTO trades (user_id, pair, entry, exit_price, lot_size, setup, result, pnl, notes) VALUES (?,?,?,?,?,?,?,?,?)",
        (update.effective_user.id, u["t_pair"], u["t_entry"], u["t_exit"], u["t_lot"], u["t_setup"], u["t_result"], u["t_pnl"], notes)
    )
    conn.commit()

    # Check daily loss limit
    today = str(date.today())
    total_loss = conn.execute(
        "SELECT COALESCE(SUM(pnl),0) FROM trades WHERE user_id=? AND date=? AND pnl < 0",
        (update.effective_user.id, today)
    ).fetchone()[0]
    conn.close()

    msg = (
        f"✅ Trade dilog!\n\n"
        f"🪙 {u['t_pair']} | {u['t_result']}\n"
        f"📥 Entry: {u['t_entry']} | 📤 Exit: {u['t_exit']}\n"
        f"📦 Lot: {u['t_lot']} | 💵 P&L: {u['t_pnl']}\n"
        f"📊 Setup: {u['t_setup']}"
    )
    if abs(total_loss) >= DAILY_LOSS_LIMIT:
        msg += f"\n\n🚨 *STOP TRADING!*\nLoss hari ini: ${abs(total_loss):.2f}\nHad: ${DAILY_LOSS_LIMIT}"

    await update.message.reply_text(msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📈 Trading", callback_data="mod_trading")]]))
    return ConversationHandler.END

async def trade_list(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM trades WHERE user_id=? ORDER BY date DESC LIMIT 10",
        (query.from_user.id,)
    ).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada trade dilog.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
        return
    msg = "📋 *10 Trade Terbaru:*\n\n"
    for r in rows:
        icon = "✅" if r["result"] == "WIN" else ("❌" if r["result"] == "LOSS" else "➡️")
        msg += f"{icon} {r['pair']} | {r['setup']} | P&L: {r['pnl']} | {r['date']}\n"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))

async def trade_today(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = str(date.today())
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trades WHERE user_id=? AND date=?", (query.from_user.id, today)).fetchall()
    conn.close()
    if not rows:
        await query.edit_message_text("Tiada trade hari ini.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
        return
    wins = sum(1 for r in rows if r["result"] == "WIN")
    losses = sum(1 for r in rows if r["result"] == "LOSS")
    total_pnl = sum(r["pnl"] for r in rows)
    msg = (
        f"📊 *Summary Hari Ini ({today})*\n\n"
        f"Total Trade: {len(rows)}\n"
        f"✅ Win: {wins} | ❌ Loss: {losses}\n"
        f"💵 Total P&L: ${total_pnl:.2f}\n"
    )
    if total_pnl < 0 and abs(total_pnl) >= DAILY_LOSS_LIMIT:
        msg += f"\n🚨 *STOP! Had loss harian dicapai.*"
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))

async def trade_loss(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = str(date.today())
    conn = get_conn()
    total_loss = conn.execute(
        "SELECT COALESCE(SUM(pnl),0) FROM trades WHERE user_id=? AND date=? AND pnl < 0",
        (query.from_user.id, today)
    ).fetchone()[0]
    conn.close()
    pct = (abs(total_loss) / DAILY_LOSS_LIMIT) * 100
    status = "🟢 Selamat" if pct < 50 else ("🟡 Berhati-hati" if pct < 100 else "🔴 STOP!")
    msg = (
        f"⚠️ *Daily Loss Status*\n\n"
        f"Had: ${DAILY_LOSS_LIMIT}\n"
        f"Loss hari ini: ${abs(total_loss):.2f}\n"
        f"Baki: ${max(0, DAILY_LOSS_LIMIT - abs(total_loss)):.2f}\n\n"
        f"Status: {status}"
    )
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Trading", callback_data="mod_trading")]]))
