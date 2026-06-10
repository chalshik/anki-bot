from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from .handlers.add_word import handle_add_word
from .handlers.quiz import handle_quiz, handle_show_answer, handle_rate
from .handlers.words import handle_words, handle_words_page
from .handlers.delete import handle_delete
from .handlers.start_help import handle_start, handle_help
from .handlers.settings import handle_settings, handle_toggle_setting


def create_application(token: str, use_updater: bool = True) -> Application:
    builder = ApplicationBuilder().token(token)
    if not use_updater:
        builder = builder.updater(None)
    app = builder.build()
    _register_handlers(app)
    return app


def _register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("quiz", handle_quiz))
    app.add_handler(CommandHandler("words", handle_words))
    app.add_handler(CommandHandler("delete", handle_delete))
    app.add_handler(CommandHandler("settings", handle_settings))

    app.add_handler(CallbackQueryHandler(handle_show_answer, pattern=r"^show:"))
    app.add_handler(CallbackQueryHandler(handle_rate, pattern=r"^rate:"))
    app.add_handler(CallbackQueryHandler(handle_words_page, pattern=r"^words_page:"))
    app.add_handler(CallbackQueryHandler(handle_toggle_setting, pattern=r"^setting:"))

    # Must be last — catches all non-command text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_word))
