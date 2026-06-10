from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .. import db

# Maps the setting key to its display label.
_TOGGLES = {
    "show_examples": "Examples",
    "show_synonyms": "Synonyms",
}


async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await db.ensure_user(user_id)
    settings = await db.get_user_settings(user_id)
    await update.message.reply_text(
        "⚙️ *Settings*\n\nTap to toggle what shows under each definition:",
        parse_mode="Markdown",
        reply_markup=_build_markup(settings),
    )


async def handle_toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    if key not in _TOGGLES:
        return

    user_id = update.effective_user.id
    settings = await db.get_user_settings(user_id)
    new_value = not settings.get(key, True)
    await db.update_user_setting(user_id, key, new_value)
    settings[key] = new_value

    await query.edit_message_text(
        "⚙️ *Settings*\n\nTap to toggle what shows under each definition:",
        parse_mode="Markdown",
        reply_markup=_build_markup(settings),
    )


def _build_markup(settings: dict) -> InlineKeyboardMarkup:
    rows = []
    for key, label in _TOGGLES.items():
        state = "✅ ON" if settings.get(key, True) else "❌ OFF"
        rows.append([
            InlineKeyboardButton(f"{label}: {state}", callback_data=f"setting:{key}")
        ])
    return InlineKeyboardMarkup(rows)
