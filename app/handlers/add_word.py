from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from .. import db
from ..dictionary import fetch_definition


async def handle_add_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = update.message.text.strip()
    user_id = update.effective_user.id

    await db.ensure_user(user_id)

    existing = await db.get_word(user_id, word)
    if existing:
        card = existing["cards"][0] if existing.get("cards") else {}
        due_str = card.get("due", "")
        due_display = _format_due(due_str) if due_str else "unknown"
        pos = f" ({existing.get('part_of_speech', '')})" if existing.get("part_of_speech") else ""
        await update.message.reply_text(
            f"📖 *{existing['word']}*{pos}\n"
            f"{existing['definition']}\n"
            f"{chr(34) + existing['example'] + chr(34) if existing.get('example') else ''}\n\n"
            f"_Already in your deck — next review: {due_display}_",
            parse_mode="Markdown",
        )
        return

    result = await fetch_definition(word)
    if result is None:
        await update.message.reply_text(
            f"❌ No definition found for *{word}*. Check the spelling and try again.",
            parse_mode="Markdown",
        )
        return

    await db.save_word(user_id, word, result["definition"], result.get("example"))

    pos = f" ({result['part_of_speech']})" if result.get("part_of_speech") else ""
    example_line = f'\n"{result["example"]}' + '"' if result.get("example") else ""
    await update.message.reply_text(
        f"📖 *{word.lower()}*{pos}\n"
        f"{result['definition']}"
        f"{example_line}\n\n"
        f"✅ Saved to your deck",
        parse_mode="Markdown",
    )


def _format_due(due_str: str) -> str:
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
