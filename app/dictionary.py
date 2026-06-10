import json
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

_SYSTEM = (
    "You are a precise English dictionary. Return only JSON with these keys: "
    "found (bool), definition (one concise sentence), part_of_speech (noun/verb/adjective/adverb/etc), "
    "examples (array of up to 3 natural usage sentences), synonyms (array of up to 5), "
    "translation (Russian translation, 1-3 words). "
    'If the input is not a real English word, return {"found": false}.'
)

_CONFIG = types.GenerateContentConfig(
    system_instruction=_SYSTEM,
    response_mime_type="application/json",
    temperature=0.1,
    max_output_tokens=1000,
)


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=os.environ["GCP_PROJECT_ID"],
            location=os.environ.get("GCP_LOCATION", "us-central1"),
        )
    return _client


async def fetch_definition(word: str) -> dict | None:
    raw = ""
    try:
        resp = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=word.lower().strip(),
            config=_CONFIG,
        )
        raw = resp.text.strip()
        # gemini-2.5-flash sometimes wraps JSON in markdown fences despite
        # response_mime_type="application/json" — strip them if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]  # drop opening fence line
            raw = raw.rsplit("```", 1)[0]  # drop closing fence
        data = json.loads(raw)
    except Exception as e:
        logger.error("Gemini lookup failed for %r: %s. Raw response: %s", word, e, raw)
        return None



    if not data.get("found"):
        return None

    definition = data.get("definition", "").strip()
    if not definition:
        return None

    examples = (data.get("examples") or [])[:3]
    synonyms = (data.get("synonyms") or [])[:5]

    return {
        "definition": definition,
        "example": examples[0] if examples else None,
        "examples": examples,
        "part_of_speech": data.get("part_of_speech", ""),
        "synonyms": synonyms,
        "translation": data.get("translation", ""),
    }
