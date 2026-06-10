import math
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .. import db

PAGE_SIZE = 10


async def handle_words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await db.ensure_user(user_id)
    await _send_words_page(update.message.reply_text, user_id, page=0)


async def handle_words_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    user_id = update.effective_user.id
    await _send_words_page(query.edit_message_text, user_id, page=page)


async def _send_words_page(send_fn, user_id: int, page: int) -> None:
    words, total = await db.get_all_words(user_id, page, PAGE_SIZE)

    if total == 0:
        await send_fn("📭 Your deck is empty. Send any English word to add it.")
        return

    total_pages = math.ceil(total / PAGE_SIZE)
    lines = [f"📚 *Your words* (page {page + 1}/{total_pages}):\n"]
    for i, w in enumerate(words, start=page * PAGE_SIZE + 1):
        card = w["cards"][0] if w.get("cards") else {}
        due = _format_due(card.get("due", ""))
        lines.append(f"{i}. {w['word']} — {due}")

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("← Prev", callback_data=f"words_page:{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Next →", callback_data=f"words_page:{page + 1}"))

    markup = InlineKeyboardMarkup([buttons]) if buttons else None
    await send_fn("\n".join(lines), parse_mode="Markdown", reply_markup=markup)


def _format_due(due_str: str) -> str:
    if not due_str:
        return "unknown"
    try:
        due = datetime.fromisoformat(due_str)
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days = (due.date() - now.date()).days
        if days < 0:
            return "overdue"
        if days == 0:
            return "today"
        if days == 1:
            return "tomorrow"
        return f"in {days} days"
    except (ValueError, AttributeError):
        return "unknown"
