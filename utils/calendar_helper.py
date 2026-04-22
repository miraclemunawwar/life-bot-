import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_bot_calendar import DetailedTelegramCalendar

def show_calendar(cal_id="default"):
    """Return InlineKeyboardMarkup for calendar."""
    raw, step = DetailedTelegramCalendar(calendar_id=cal_id).build()
    data = json.loads(raw)
    keyboard = []
    for row in data["inline_keyboard"]:
        btn_row = []
        for btn in row:
            btn_row.append(InlineKeyboardButton(
                text=str(btn["text"]),
                callback_data=btn["callback_data"]
            ))
        keyboard.append(btn_row)
    return InlineKeyboardMarkup(keyboard)

def process_calendar(callback_data, cal_id="default"):
    """Process calendar callback. Returns (result_date, markup, step)."""
    result, raw, step = DetailedTelegramCalendar(calendar_id=cal_id).process(callback_data)
    if result:
        return result, None, None
    if raw:
        data = json.loads(raw)
        keyboard = []
        for row in data["inline_keyboard"]:
            btn_row = []
            for btn in row:
                btn_row.append(InlineKeyboardButton(
                    text=str(btn["text"]),
                    callback_data=btn["callback_data"]
                ))
            keyboard.append(btn_row)
        return None, InlineKeyboardMarkup(keyboard), step
    return None, None, None
