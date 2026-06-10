import math
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .. import db

PAGE_SIZE = 8
_KEY = "cleanup_selected"  # set of word UUIDs in context.user_data


async def handle_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[_KEY] = set()
    user_id = update.effective_user.id
    await db.ensure_user(user_id)
    await _send_page(update.message.reply_text, context, user_id, page=0)


async def handle_cleanup_page(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split(":")[1])
    user_id = update.effective_user.id
    await _send_page(query.edit_message_text, context, user_id, page=page)


async def handle_cleanup_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    word_id = query.data.split(":", 1)[1]
    selected: set = context.user_data.setdefault(_KEY, set())
    if word_id in selected:
        selected.discard(word_id)
    else:
        selected.add(word_id)
    # Re-render current page (extract page from message markup)
    page = _current_page_from_markup(query.message.reply_markup)
    user_id = update.effective_user.id
    await _send_page(query.edit_message_text, context, user_id, page=page)


async def handle_cleanup_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    selected: set = context.user_data.get(_KEY, set())
    if not selected:
        await query.edit_message_text("⚠️ Nothing selected.")
        return
    count = await db.delete_words_batch(user_id, list(selected))
    context.user_data.pop(_KEY, None)
    await query.edit_message_text(f"🗑 Deleted {count} word{'s' if count != 1 else ''} from your deck.")


async def handle_cleanup_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    context.user_data.pop(_KEY, None)
    await query.edit_message_text("✖ Cleanup cancelled. Nothing was deleted.")


# ── helpers ──────────────────────────────────────────────────────────────────

async def _send_page(send_fn, context: ContextTypes.DEFAULT_TYPE, user_id: int, page: int) -> None:
    words, total = await db.get_words_by_due_desc(user_id, page, PAGE_SIZE)

    if total == 0:
        await send_fn("📭 Your deck is empty.")
        return

    selected: set = context.user_data.setdefault(_KEY, set())
    total_pages = math.ceil(total / PAGE_SIZE)

    header = (
        f"🗑 *Cleanup — select words to delete*\n"
        f"Sorted by next review (furthest first — best-known words)\n"
        f"Page {page + 1}/{total_pages} · {len(selected)} selected\n"
    )
    lines = [header]
    for w in words:
        card = w["cards"][0] if w.get("cards") else {}
        due = _format_due(card.get("due", ""))
        mark = "✅" if w["id"] in selected else "◻️"
        lines.append(f"{mark} *{w['word']}* — {due}")

    # Toggle buttons (one per word, two columns)
    toggle_rows = []
    row = []
    for w in words:
        mark = "✅" if w["id"] in selected else "◻️"
        btn = InlineKeyboardButton(
            f"{mark} {w['word']}",
            callback_data=f"cleanup_toggle:{w['id']}",
        )
        row.append(btn)
        if len(row) == 2:
            toggle_rows.append(row)
            row = []
    if row:
        toggle_rows.append(row)

    # Navigation row
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("← Prev", callback_data=f"cleanup_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next →", callback_data=f"cleanup_page:{page + 1}"))

    # Action row
    n = len(selected)
    action = [
        InlineKeyboardButton(
            f"🗑 Delete {n} selected" if n else "🗑 Delete selected",
            callback_data="cleanup_confirm",
        ),
        InlineKeyboardButton("✖ Cancel", callback_data="cleanup_cancel"),
    ]

    keyboard = toggle_rows
    if nav:
        keyboard.append(nav)
    keyboard.append(action)

    await send_fn(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


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


def _current_page_from_markup(markup: InlineKeyboardMarkup) -> int:
    """Extract current page from the navigation buttons, fallback to 0."""
    if not markup:
        return 0
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("cleanup_page:"):
                # Next → means current is n-1, Prev ← means current is n+1
                n = int(btn.callback_data.split(":")[1])
                if btn.text.startswith("Next"):
                    return n - 1
                else:  # Prev
                    return n + 1
    return 0
