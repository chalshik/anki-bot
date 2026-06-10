import html
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from .. import db
from ..dictionary import fetch_definition
from ..formatting import format_card


async def handle_add_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = update.message.text.strip()
    user_id = update.effective_user.id

    await db.ensure_user(user_id)
    settings = await db.get_user_settings(user_id)

    existing = await db.get_word(user_id, word)
    if existing:
        card = existing["cards"][0] if existing.get("cards") else {}
        due_str = card.get("due", "")
        due_display = _format_due(due_str) if due_str else "unknown"
        body = format_card(
            existing["word"],
            existing.get("definition", ""),
            settings,
            part_of_speech=existing.get("part_of_speech") or "",
            examples=existing.get("examples"),
            example=existing.get("example"),
            synonyms=existing.get("synonyms"),
        )
        await update.message.reply_text(
            f"📖 {body}\n\n<i>Already in your deck — next review: {due_display}</i>",
            parse_mode="HTML",
        )
        return

    result = await fetch_definition(word)
    if result is None:
        await update.message.reply_text(
            f"❌ No definition found for <b>{html.escape(word)}</b>. "
            f"Check the spelling and try again.",
            parse_mode="HTML",
        )
        return

    await db.save_word(
        user_id,
        word,
        result["definition"],
        result.get("example"),
        examples=result.get("examples"),
        synonyms=result.get("synonyms"),
        part_of_speech=result.get("part_of_speech"),
    )

    body = format_card(
        word.lower(),
        result["definition"],
        settings,
        part_of_speech=result.get("part_of_speech") or "",
        examples=result.get("examples"),
        example=result.get("example"),
        synonyms=result.get("synonyms"),
    )
    await update.message.reply_text(
        f"📖 {body}\n\n✅ Saved to your deck",
        parse_mode="HTML",
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
