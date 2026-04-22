from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
from config import TOKEN
from db import init_db
from handlers.home import start, back_home, any_message
from handlers.study import (
    study_home, study_add, study_list, study_urgent, study_done,
    study_timer, timer_start, got_title, got_subject, got_progress,
    study_calendar_handler, S_TITLE, S_SUBJECT, S_PROGRESS
)
from handlers.trading import (
    trading_home, trade_add, trade_list, trade_today, trade_loss,
    chk_setup, chk_risk, chk_emotion, got_pair, got_entry, got_exit,
    got_lot, got_setup, got_result, got_pnl, got_notes,
    T_PAIR, T_ENTRY, T_EXIT, T_LOT, T_SETUP, T_RESULT, T_PNL, T_NOTES,
    CHECKLIST_SETUP, CHECKLIST_RISK, CHECKLIST_EMOTION
)
from handlers.work import (
    work_home, work_add, work_list, work_done,
    work_income_add, work_income_list, got_client, got_task,
    got_income_amt, got_income_src,
    W_CLIENT, W_TASK, W_INCOME_AMT, W_INCOME_SRC
)
from handlers.family import (
    family_home, family_mood, got_mood, family_task_add, got_assign,
    got_family_task, family_task_list, ftask_done,
    family_date_add, got_date_title, family_date_calendar, family_date_list,
    F_TASK, F_DATE_TITLE, F_DATE_DATE
)
from handlers.finance import (
    finance_home, fin_add, fin_overview, fin_commit_add, fin_commit_list,
    commit_pay, got_fin_amt, got_fin_cat, got_fin_note,
    got_commit_title, got_commit_amt, commit_calendar,
    FIN_AMT, FIN_CAT, FIN_NOTE, COMMIT_TITLE, COMMIT_AMT, COMMIT_DUE
)
from handlers.system import system_home, sys_priority, sys_weekly
from services.notifications import daily_reminders, evening_checkin

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # Study conversation
    study_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(study_add, pattern="^study_add$")],
        states={
            S_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_title)],
            S_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_subject)],
            S_PROGRESS: [
                CallbackQueryHandler(study_calendar_handler, pattern="^cbcal_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_progress),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Trading conversation
    trade_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(trade_add, pattern="^trade_add$")],
        states={
            CHECKLIST_SETUP: [CallbackQueryHandler(chk_setup, pattern="^chk_setup_")],
            CHECKLIST_RISK: [CallbackQueryHandler(chk_risk, pattern="^chk_risk_")],
            CHECKLIST_EMOTION: [CallbackQueryHandler(chk_emotion, pattern="^chk_emo_")],
            T_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_pair)],
            T_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_entry)],
            T_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_exit)],
            T_LOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_lot)],
            T_SETUP: [CallbackQueryHandler(got_setup, pattern="^setup_")],
            T_RESULT: [CallbackQueryHandler(got_result, pattern="^result_")],
            T_PNL: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_pnl)],
            T_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_notes)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Work conversation
    work_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(work_add, pattern="^work_add$"),
            CallbackQueryHandler(work_income_add, pattern="^work_income_add$"),
        ],
        states={
            W_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_client)],
            W_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_task)],
            W_INCOME_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_income_amt)],
            W_INCOME_SRC: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_income_src)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Family conversation
    family_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(family_task_add, pattern="^family_task_add$"),
            CallbackQueryHandler(family_date_add, pattern="^family_date_add$"),
        ],
        states={
            F_TASK: [
                CallbackQueryHandler(got_assign, pattern="^task_assign_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_family_task),
            ],
            F_DATE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_date_title)],
            F_DATE_DATE: [CallbackQueryHandler(family_date_calendar, pattern="^cbcal_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Finance conversation
    finance_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(fin_add, pattern="^fin_add$"),
            CallbackQueryHandler(fin_commit_add, pattern="^fin_commit_add$"),
        ],
        states={
            FIN_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_fin_amt)],
            FIN_CAT: [CallbackQueryHandler(got_fin_cat, pattern="^fincat_")],
            FIN_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_fin_note)],
            COMMIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_commit_title)],
            COMMIT_AMT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_commit_amt)],
            COMMIT_DUE: [CallbackQueryHandler(commit_calendar, pattern="^cbcal_")],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Register conversations first
    app.add_handler(study_conv)
    app.add_handler(trade_conv)
    app.add_handler(work_conv)
    app.add_handler(family_conv)
    app.add_handler(finance_conv)

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Module routing
    app.add_handler(CallbackQueryHandler(back_home, pattern="^back_home$"))
    app.add_handler(CallbackQueryHandler(study_home, pattern="^mod_study$"))
    app.add_handler(CallbackQueryHandler(trading_home, pattern="^mod_trading$"))
    app.add_handler(CallbackQueryHandler(work_home, pattern="^mod_work$"))
    app.add_handler(CallbackQueryHandler(family_home, pattern="^mod_family$"))
    app.add_handler(CallbackQueryHandler(finance_home, pattern="^mod_finance$"))
    app.add_handler(CallbackQueryHandler(system_home, pattern="^mod_system$"))

    # Study
    app.add_handler(CallbackQueryHandler(study_list, pattern="^study_list$"))
    app.add_handler(CallbackQueryHandler(study_urgent, pattern="^study_urgent$"))
    app.add_handler(CallbackQueryHandler(study_timer, pattern="^study_timer$"))
    app.add_handler(CallbackQueryHandler(timer_start, pattern="^timer_"))
    app.add_handler(CallbackQueryHandler(study_done, pattern="^study_done_"))

    # Trading
    app.add_handler(CallbackQueryHandler(trade_list, pattern="^trade_list$"))
    app.add_handler(CallbackQueryHandler(trade_today, pattern="^trade_today$"))
    app.add_handler(CallbackQueryHandler(trade_loss, pattern="^trade_loss$"))

    # Work
    app.add_handler(CallbackQueryHandler(work_list, pattern="^work_list$"))
    app.add_handler(CallbackQueryHandler(work_done, pattern="^work_done_"))
    app.add_handler(CallbackQueryHandler(work_income_list, pattern="^work_income_list$"))

    # Family
    app.add_handler(CallbackQueryHandler(family_mood, pattern="^family_mood$"))
    app.add_handler(CallbackQueryHandler(got_mood, pattern="^mood_"))
    app.add_handler(CallbackQueryHandler(family_task_list, pattern="^family_task_list$"))
    app.add_handler(CallbackQueryHandler(ftask_done, pattern="^ftask_done_"))
    app.add_handler(CallbackQueryHandler(family_date_list, pattern="^family_date_list$"))

    # Finance
    app.add_handler(CallbackQueryHandler(fin_overview, pattern="^fin_overview$"))
    app.add_handler(CallbackQueryHandler(fin_commit_list, pattern="^fin_commit_list$"))
    app.add_handler(CallbackQueryHandler(commit_pay, pattern="^commit_pay_"))

    # System
    app.add_handler(CallbackQueryHandler(sys_priority, pattern="^sys_priority$"))
    app.add_handler(CallbackQueryHandler(sys_weekly, pattern="^sys_weekly$"))

    # Any message → show menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))

    # Reminder pukul 8 pagi — assignment & bil
    from datetime import time as dtime
    app.job_queue.run_daily(daily_reminders, time=dtime(8, 0, 0))
    # Check-in pukul 8 malam — family
    app.job_queue.run_daily(evening_checkin, time=dtime(20, 0, 0))

    print("Life Management Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
