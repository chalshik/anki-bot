"""Shared rendering for a word's card body (used by add-word and quiz).

Output is Telegram **HTML** (``parse_mode="HTML"``). HTML is used instead of
legacy Markdown because dictionary prose and synonyms routinely contain ``_``,
``*`` and ``[`` as ordinary text, which break Markdown parsing and cause Telegram
to reject the whole message. HTML has well-defined escaping via ``html.escape``.
"""
import html
from typing import Optional


def format_card(
    word: str,
    definition: str,
    settings: dict,
    part_of_speech: str = "",
    examples: Optional[list[str]] = None,
    example: Optional[str] = None,
    synonyms: Optional[list[str]] = None,
    translation: Optional[str] = None,
) -> str:
    """Render the HTML body for a word.

    ``settings`` is the dict from ``db.get_user_settings`` and controls whether
    the examples and synonyms lines are shown. Falls back to the legacy single
    ``example`` column for rows saved before the ``examples`` array existed.
    """
    ex_list = examples or ([example] if example else [])
    syn_list = synonyms or []

    pos = f" <i>({html.escape(part_of_speech)})</i>" if part_of_speech else ""
    lines = [f"<b>{html.escape(word)}</b>{pos}", html.escape(definition)]

    if settings.get("show_examples", True):
        lines.extend(f'<i>"{html.escape(ex)}"</i>' for ex in ex_list)

    if settings.get("show_synonyms", True) and syn_list:
        joined = ", ".join(html.escape(s) for s in syn_list)
        lines.append(f"🔁 Synonyms: {joined}")

    if translation:
        lines.append(f"🇷🇺 {html.escape(translation)}")

    return "\n".join(lines)
