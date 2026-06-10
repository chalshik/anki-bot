# Vocabulary Bot — Requirements Document

## Overview

A Telegram bot that helps users build English vocabulary through spaced repetition. Users send a word, get a definition instantly, and the bot schedules reviews using the FSRS algorithm.

English only. v1 covers the four fundamental Anki features: add, quiz, list, delete.

---

## Tech Stack

| Layer | Service |
|---|---|
| HTTP server | FastAPI |
| Bot runtime | Python + `python-telegram-bot` v20 |
| Hosting | Google Cloud Run |
| Database | Supabase (free tier, PostgreSQL) |
| Dictionary API | Free Dictionary API (free, no key) |
| SRS Algorithm | `py-fsrs` (FSRS-4.5, open source) |
| Containerization | Docker + Docker Compose |

---

## Features

### 1. Add a Word
- User sends any English word as a plain message
- Bot fetches definition + example sentence from Free Dictionary API
- Bot replies with the formatted card and saves it to the user's deck with initial FSRS state (New, due immediately)
- If the word already exists in the user's deck, bot replies with the existing entry and its next review date — no duplicate is created
- If the API returns no result, bot replies with an error and does not save anything
- No commands needed — just type the word

**Example:**
```
User: ephemeral

Bot: 📖 ephemeral (adj.)
     Lasting for a very short time.
     "the ephemeral pleasures of youth"
     ✅ Saved to your deck
```

---

### 2. Daily Quiz (`/quiz`)
- User runs `/quiz` to start a review session
- Bot asks how many cards to review (default: 20)
- If no cards are due, bot replies with when the next card is due and exits
- Cards are shown one at a time in standard Anki front/back style:

**Step 1 — Front (word shown, definition hidden):**
```
Bot: What does "ephemeral" mean?
     [Show answer]
```

**Step 2 — Back (after tapping Show answer):**
```
Bot: ephemeral (adj.)
     Lasting for a very short time.
     "the ephemeral pleasures of youth"

     How did you do?
     [1 Again] [2 Hard] [3 Good] [4 Easy]
```

- Bot updates FSRS state and schedules next review after each rating
- Session ends with a summary: cards reviewed, cards still due today, due tomorrow

---

### 3. Word List (`/words`)
- Shows all saved words with their next review date
- Paginated (10 words per page, inline prev/next buttons)

---

### 4. Delete a Word (`/delete <word>`)
- Removes the word and its card history permanently
- Bot confirms deletion or replies if the word is not found

---

## Database Schema (Supabase)

### `users`
| Column | Type | Notes |
|---|---|---|
| id | bigint | Telegram user ID (primary key) |
| created_at | timestamp | |

### `words`
| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| user_id | bigint | FK → users |
| word | text | The vocabulary word |
| definition | text | Fetched from API |
| example | text | Fetched from API |
| created_at | timestamp | |

### `cards`
| Column | Type | Notes |
|---|---|---|
| id | uuid | Primary key |
| word_id | uuid | FK → words |
| card_id | bigint | Internal FSRS card identifier |
| state | smallint | 1=Learning 2=Review 3=Relearning |
| step | integer | Current learning/relearning step (null in Review state) |
| stability | float | FSRS: how long memory lasts (days) |
| difficulty | float | FSRS: inherent difficulty |
| due | timestamp | Next review datetime |
| last_review | timestamp | When the card was last reviewed |

---

## FSRS Algorithm

Uses the `py-fsrs` Python library (FSRS-4.5). The `Card` object maps directly to the `cards` table columns above.

**New card flow:**
1. `fsrs.Card()` created with default state (New, due immediately)
2. All fields persisted to `cards` table on first save

**Review flow:**
1. Load card fields from DB and reconstruct the `fsrs.Card` object
2. Call `fsrs.review_card(card, rating, now)` — returns updated card + review log
3. Persist all updated fields back to DB

**Rating → interval (approximate):**
| Rating | Effect |
|---|---|
| 1 — Again | Card re-enters Learning; short interval (~1 day) |
| 2 — Hard | Slightly shorter than the predicted interval |
| 3 — Good | Standard predicted interval |
| 4 — Easy | Longer interval with stability bonus |

Exact intervals are computed by `py-fsrs` based on the card's stability and difficulty — do not hardcode them.

---

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `SUPABASE_URL` | Project URL from Supabase dashboard |
| `SUPABASE_KEY` | `anon` public key from Supabase dashboard |
| `WEBHOOK_URL` | Public HTTPS URL of the Render service |

Store in a `.env` file locally (never commit it) and as Environment Variables in the Render dashboard.

---

## Bot Setup (BotFather)

1. Message `@BotFather` on Telegram
2. Send `/newbot` and follow prompts to get a `TELEGRAM_BOT_TOKEN`
3. Set commands via `/setcommands`:
   ```
   quiz - Start a review session
   words - List all saved words
   delete - Delete a word
   ```

---

## Local Development

```bash
git clone <repo>
cd anki-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python bot.py          # runs in polling mode locally
```

Polling mode is used locally. Webhook mode is production-only (Render).

---

## Deployment (Google Cloud Run)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/<PROJECT_ID>/anki-bot

# Deploy
gcloud run deploy anki-bot \
  --image gcr.io/<PROJECT_ID>/anki-bot \
  --platform managed \
  --region <REGION> \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=...,SUPABASE_URL=...,SUPABASE_KEY=...,WEBHOOK_URL=https://<your-service-url>,ENVIRONMENT=production
```

After the first deploy, copy the Cloud Run service URL into `WEBHOOK_URL` and redeploy. The bot registers its webhook with Telegram automatically on startup via the FastAPI lifespan.

---

## Out of Scope (v1)

- Daily reminders
- Stats / streaks
- Web interface
- EPUB/PDF import
- Multi-language support
- Shared decks
- Timezone-aware scheduling
