from telegram import Update
from telegram.ext import ContextTypes

from .. import db

HELP_TEXT = (
    "📚 *Anki Bot — Commands*\n\n"
    "Just send any word to look it up and add it to your deck.\n\n"
    "/quiz — review your due cards\n"
    "/words — browse all your saved words\n"
    "/delete <word> — remove a word from your deck\n"
    "/settings — toggle synonyms & examples\n"
    "/help — show this message\n\n"
    "_Definitions from Wiktionary (CC BY-SA 4.0)_"
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await db.ensure_user(user_id)
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 Hi {name}! Welcome to Anki Bot.\n\n" + HELP_TEXT,
        parse_mode="Markdown",
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")
