from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from .handlers import start, help, add_word, quiz, words, settings, cleanup, upload


def create_application(token: str, use_updater: bool = True) -> Application:
    builder = ApplicationBuilder().token(token)
    if not use_updater:
        builder = builder.updater(None)
    app = builder.build()
    _register_handlers(app)
    return app


def _register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start.handle_start))
    application.add_handler(CommandHandler("help", help.handle_help))
    application.add_handler(CommandHandler("quiz", quiz.handle_quiz))
    application.add_handler(CommandHandler("words", words.handle_words))
    application.add_handler(CommandHandler("delete", delete.handle_delete))

    application.add_handler(CommandHandler("settings", settings.handle_settings))
    application.add_handler(CommandHandler("cleanup", cleanup.handle_cleanup))
    application.add_handler(CommandHandler("upload", upload.handle_upload_command))

    # Photo & File Handlers
    application.add_handler(MessageHandler(filters.PHOTO, upload.handle_photo))

    # General word addition
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_word.handle_add_word))

    # Callback queries
    application.add_handler(CallbackQueryHandler(quiz.handle_show_answer, pattern="^show:"))
    application.add_handler(CallbackQueryHandler(quiz.handle_rate, pattern="^rate:"))
    application.add_handler(CallbackQueryHandler(words.handle_words_page, pattern=r"^words_page:"))
    application.add_handler(CallbackQueryHandler(settings.handle_toggle_setting, pattern="^setting:"))
    application.add_handler(CallbackQueryHandler(cleanup.handle_cleanup_page, pattern="^cleanup_page:"))
    application.add_handler(CallbackQueryHandler(cleanup.handle_cleanup_toggle, pattern="^cleanup_toggle:"))
    application.add_handler(CallbackQueryHandler(cleanup.handle_cleanup_confirm, pattern="^cleanup_confirm$"))
    application.add_handler(CallbackQueryHandler(cleanup.handle_cleanup_cancel, pattern="^cleanup_cancel$"))
    application.add_handler(CallbackQueryHandler(upload.handle_upload_toggle, pattern="^upload_toggle:"))
    application.add_handler(CallbackQueryHandler(upload.handle_upload_done, pattern="^upload_done$"))
