from telegram import Update
from telegram.ext import ContextTypes

from .. import db


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /delete <word>")
        return

    word = " ".join(context.args).strip()
    user_id = update.effective_user.id

    deleted = await db.delete_word(user_id, word)
    if deleted:
        await update.message.reply_text(f"🗑 *{word.lower()}* removed from your deck.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ *{word.lower()}* not found in your deck.", parse_mode="Markdown")
