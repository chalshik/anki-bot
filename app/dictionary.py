import httpx

_BASE = "https://api.dictionaryapi.dev/api/v2/entries/en"


async def fetch_definition(word: str) -> dict | None:
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
        meanings = data[0].get("meanings", [])
        if not meanings:
            return None
        defn = meanings[0]["definitions"][0]
        return {
            "definition": defn.get("definition", ""),
            "example": defn.get("example"),
            "part_of_speech": meanings[0].get("partOfSpeech", ""),
        }
    except (IndexError, KeyError):
        return None
