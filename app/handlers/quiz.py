from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from fsrs import Scheduler, Rating

from .. import db
from ..fsrs_utils import card_from_row
from ..formatting import format_card

_scheduler = Scheduler()

# In-memory quiz sessions keyed by user_id.
# On Cloud Run single-instance deployments this is fine for v1.
_sessions: dict[int, _QuizSession] = {}


@dataclass
class _QuizSession:
    cards: list[dict]
    index: int = 0
    reviewed: int = 0


_RATING_LABELS = {1: "1 Again", 2: "2 Hard", 3: "3 Good", 4: "4 Easy"}
_RATING_MAP = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}


async def handle_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await db.ensure_user(user_id)

    limit = 20
    if context.args:
        try:
            limit = max(1, min(int(context.args[0]), 100))
        except ValueError:
            pass

    cards = await db.get_due_cards(user_id, limit)

    if not cards:
        next_due = await db.get_next_due(user_id)
        if next_due:
            next_due_display = _format_due(next_due)
            await update.message.reply_text(
                f"✅ No cards due right now. Next review: {next_due_display}."
            )
        else:
            await update.message.reply_text(
                "📭 Your deck is empty. Send any English word to add it."
            )
        return

    _sessions[user_id] = _QuizSession(cards=cards)
    await _send_card_front(update.message.reply_text, cards[0])


async def handle_show_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    card_id = query.data.split(":", 1)[1]

    user_id = update.effective_user.id
    session = _sessions.get(user_id)
    if session is None:
        await query.edit_message_text("Session expired. Run /quiz to start again.")
        return

    card_row = _find_card(session, card_id)
    if card_row is None:
        await query.edit_message_text("Session mismatch. Run /quiz to start again.")
        return

    settings = await db.get_user_settings(user_id)
    await _send_card_back(query.edit_message_text, card_row, settings)


async def handle_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, card_id, rating_str = query.data.split(":", 2)
    rating_int = int(rating_str)

    user_id = update.effective_user.id
    session = _sessions.get(user_id)
    if session is None:
        await query.edit_message_text("Session expired. Run /quiz to start again.")
        return

    card_row = _find_card(session, card_id)
    if card_row is None:
        await query.edit_message_text("Session mismatch. Run /quiz to start again.")
        return

    # Run FSRS
    card = card_from_row(card_row)
    updated_card, _ = _scheduler.review_card(card, _RATING_MAP[rating_int])
    await db.update_card(card_id, updated_card)

    session.reviewed += 1
    session.index += 1

    if session.index < len(session.cards):
        next_card = session.cards[session.index]
        await _send_card_front(query.edit_message_text, next_card)
    else:
        del _sessions[user_id]
        total = session.reviewed
        await query.edit_message_text(
            f"🎉 Session complete!\n\n"
            f"Reviewed: {total} card{'s' if total != 1 else ''}\n\n"
            f"Run /quiz anytime to continue."
        )


# ---------- helpers ----------

def _find_card(session: _QuizSession, card_id: str) -> dict | None:
    for c in session.cards:
        if c["id"] == card_id:
            return c
    return None


async def _send_card_front(send_fn, card_row: dict) -> None:
    word = html.escape(card_row["words"]["word"])
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("👁 Show answer", callback_data=f"show:{card_row['id']}")
    ]])
    await send_fn(
        f'What does <b>"{word}"</b> mean?',
        parse_mode="HTML",
        reply_markup=markup,
    )


async def _send_card_back(send_fn, card_row: dict, settings: dict) -> None:
    w = card_row["words"]
    body = format_card(
        w["word"],
        w.get("definition", ""),
        settings,
        part_of_speech=w.get("part_of_speech") or "",
        examples=w.get("examples"),
        example=w.get("example"),
        synonyms=w.get("synonyms"),
        translation=w.get("translation"),
    )
    text = f"{body}\n\nHow did you do?"

    buttons = [
        InlineKeyboardButton(label, callback_data=f"rate:{card_row['id']}:{r}")
        for r, label in _RATING_LABELS.items()
    ]
    markup = InlineKeyboardMarkup([buttons])
    await send_fn(text, parse_mode="HTML", reply_markup=markup)


def _format_due(due: datetime) -> str:
    now = datetime.now(timezone.utc)
    days = (due.date() - now.date()).days
    if days == 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"
