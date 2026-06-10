import httpx

_BASE = "https://freedictionaryapi.com/api/v1/entries/en"

_MAX_EXAMPLES = 3
_MAX_SYNONYMS = 5


async def fetch_definition(word: str) -> dict | None:
    """Look up an English word via the Wiktionary-backed Free Dictionary API.

    Returns a dict with definition, examples, synonyms and part of speech, or
    None if the word can't be found / the request fails. Note: unknown words
    return HTTP 200 with an empty ``entries`` list, not a 404.
    """
    url = f"{_BASE}/{word.lower().strip()}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
        except httpx.RequestError:
            return None

    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
    except ValueError:
        return None

    entries = data.get("entries") or []
    if not entries:
        return None

    return _parse_entries(entries)


def _parse_entries(entries: list[dict]) -> dict | None:
    # Use the first entry for the headline definition / part of speech, but
    # gather examples and synonyms across all of its senses.
    entry = entries[0]
    senses = entry.get("senses") or []

    definition = ""
    for sense in senses:
        if sense.get("definition"):
            definition = sense["definition"]
            break

    if not definition:
        return None

    examples: list[str] = []
    synonyms: list[str] = []
    for sense in senses:
        for ex in sense.get("examples") or []:
            if ex and ex not in examples:
                examples.append(ex)
        for syn in sense.get("synonyms") or []:
            if syn and syn not in synonyms:
                synonyms.append(syn)

    examples = examples[:_MAX_EXAMPLES]
    synonyms = synonyms[:_MAX_SYNONYMS]

    return {
        "definition": definition,
        "example": examples[0] if examples else None,  # back-compat
        "examples": examples,
        "part_of_speech": entry.get("partOfSpeech", ""),
        "synonyms": synonyms,
    }
