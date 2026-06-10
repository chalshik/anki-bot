import os
import html
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from . import db
from .bot import create_application

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
REMIND_TOKEN = os.getenv("REMIND_TOKEN", "")

ptb_app = create_application(
    token=TELEGRAM_BOT_TOKEN,
    use_updater=(ENVIRONMENT == "local"),
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init(SUPABASE_URL, SUPABASE_KEY)

    async with ptb_app:
        await ptb_app.start()

        if ENVIRONMENT == "local":
            await ptb_app.updater.start_polling(drop_pending_updates=True)
        elif WEBHOOK_URL:
            await ptb_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

        yield

        if ENVIRONMENT == "local":
            await ptb_app.updater.stop()
        await ptb_app.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/remind")
async def remind(request: Request) -> Response:
    token = request.headers.get("X-Remind-Token")
    if not REMIND_TOKEN or token != REMIND_TOKEN:
        return Response(status_code=401)

    users_to_remind = await db.get_users_with_due_cards()
    for user_id, word, card_id in users_to_remind:
        try:
            text = f'🛎 *Review Reminder!*\n\nWhat does <b>"{html.escape(word)}"</b> mean?'
            markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("👁 Show answer", callback_data=f"show:{card_id}")
            ]])
            await ptb_app.bot.send_message(
                chat_id=user_id, 
                text=text, 
                parse_mode="HTML",
                reply_markup=markup
            )
        except Exception:
            continue

            
    return Response(status_code=200)


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
