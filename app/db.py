import asyncio
from datetime import datetime, timezone
from typing import Optional

from supabase import create_client, Client
from fsrs import Card

from .fsrs_utils import card_to_dict

_client: Optional[Client] = None


def init(url: str, key: str) -> None:
    global _client
    _client = create_client(url, key)


def _db() -> Client:
    if _client is None:
        raise RuntimeError("DB not initialized — call db.init() first")
    return _client


async def _run(fn):
    return await asyncio.to_thread(fn)


# ---------- users ----------

async def ensure_user(user_id: int) -> None:
    await _run(lambda: _db().table("users").upsert({"id": user_id}).execute())


async def get_user_settings(user_id: int) -> dict:
    result = await _run(
        lambda: _db().table("users")
        .select("show_synonyms, show_examples")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    row = result.data[0] if result.data else {}
    return {
        "show_synonyms": row.get("show_synonyms", True),
        "show_examples": row.get("show_examples", True),
    }


async def update_user_setting(user_id: int, key: str, value: bool) -> None:
    if key not in ("show_synonyms", "show_examples"):
        raise ValueError(f"Unknown setting: {key}")
    await _run(
        lambda: _db().table("users").update({key: value}).eq("id", user_id).execute()
    )


# ---------- words ----------

async def get_word(user_id: int, word: str) -> Optional[dict]:
    result = await _run(
        lambda: _db().table("words")
        .select("*, cards(*)")
        .eq("user_id", user_id)
        .ilike("word", word)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


async def save_word(
    user_id: int,
    word: str,
    definition: str,
    example: Optional[str],
    examples: Optional[list[str]] = None,
    synonyms: Optional[list[str]] = None,
    part_of_speech: Optional[str] = None,
) -> dict:
    word_result = await _run(
        lambda: _db().table("words").insert({
            "user_id": user_id,
            "word": word.lower(),
            "definition": definition,
            "example": example,
            "examples": examples,
            "synonyms": synonyms,
            "part_of_speech": part_of_speech,
        }).execute()
    )
    word_row = word_result.data[0]

    initial_card = Card()
    card_data = card_to_dict(initial_card)
    card_data["word_id"] = word_row["id"]
    await _run(lambda: _db().table("cards").insert(card_data).execute())

    return word_row


async def get_all_words(user_id: int, page: int, page_size: int = 10) -> tuple[list[dict], int]:
    offset = page * page_size
    result = await _run(
        lambda: _db().table("words")
        .select("*, cards(*)", count="exact")
        .eq("user_id", user_id)
        .order("word")
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return result.data or [], result.count or 0


async def delete_word(user_id: int, word: str) -> bool:
    result = await _run(
        lambda: _db().table("words")
        .delete()
        .eq("user_id", user_id)
        .ilike("word", word)
        .execute()
    )
    return bool(result.data)


# ---------- cards ----------

async def get_due_cards(user_id: int, limit: int = 20) -> list[dict]:
    words_result = await _run(
        lambda: _db().table("words").select("id").eq("user_id", user_id).execute()
    )
    word_ids = [w["id"] for w in (words_result.data or [])]
    if not word_ids:
        return []

    now_iso = datetime.now(timezone.utc).isoformat()
    result = await _run(
        lambda: _db().table("cards")
        .select("*, words(*)")
        .in_("word_id", word_ids)
        .lte("due", now_iso)
        .order("due")
        .limit(limit)
        .execute()
    )
    return result.data or []


async def get_next_due(user_id: int) -> Optional[datetime]:
    words_result = await _run(
        lambda: _db().table("words").select("id").eq("user_id", user_id).execute()
    )
    word_ids = [w["id"] for w in (words_result.data or [])]
    if not word_ids:
        return None

    result = await _run(
        lambda: _db().table("cards")
        .select("due")
        .in_("word_id", word_ids)
        .order("due")
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    due_str = result.data[0]["due"]
    dt = datetime.fromisoformat(due_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


async def update_card(card_id: str, card: Card) -> None:
    data = card_to_dict(card)
    await _run(lambda: _db().table("cards").update(data).eq("id", card_id).execute())
