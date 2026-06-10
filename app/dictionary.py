import asyncio
import json
import os

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

_model: GenerativeModel | None = None

_SYSTEM = (
    "You are a precise English dictionary. Return only JSON with these keys: "
    "found (bool), definition (one concise sentence), part_of_speech (noun/verb/adjective/adverb/etc), "
    "examples (array of up to 3 natural usage sentences), synonyms (array of up to 5), "
    "translation (Russian translation, 1-3 words). "
    'If the input is not a real English word, return {"found": false}.'
)

_CONFIG = GenerationConfig(
    response_mime_type="application/json",
    temperature=0.1,
    max_output_tokens=300,
)


def _get_model() -> GenerativeModel:
    global _model
    if _model is None:
        vertexai.init(
            project=os.environ["GCP_PROJECT_ID"],
            location=os.environ.get("GCP_LOCATION", "us-central1"),
        )
        _model = GenerativeModel("gemini-1.5-flash", system_instruction=_SYSTEM)
    return _model


async def fetch_definition(word: str) -> dict | None:
    try:
        resp = await asyncio.to_thread(
            _get_model().generate_content,
            word.lower().strip(),
            generation_config=_CONFIG,
        )
        data = json.loads(resp.text)
    except Exception:
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
