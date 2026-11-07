"""One place to call the LLM. Gemini first, Groq as automatic backup.

Used by the Discovery Engine (Step 5), the Streamlit app (Step 6) and the MVP (Step 9).
Keys come from .env locally, or from Streamlit Secrets in the cloud (exposed as env vars).
"""
import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MIN_GAP = float(os.getenv("LLM_MIN_GAP", "6.5"))  # seconds between calls (free tier ~10 req/min)
_last_call = 0.0
_gemini = _groq = None


def _pace():
    global _last_call
    wait = MIN_GAP - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def parse_json(text: str):
    """Parse JSON even if the model wrapped it in ``` fences or added text around it."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            raise
        return json.loads(text[start:end + 1])


def _gemini_call(prompt, system, model, temperature):
    global _gemini
    from google import genai
    from google.genai import types
    if _gemini is None:  # 60 s timeout so one stuck call can't hang the whole pipeline
        _gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options=types.HttpOptions(timeout=60_000))
    r = _gemini.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, temperature=temperature,
                                           response_mime_type="application/json"))
    return r.text


def _groq_call(prompt, system, temperature):
    global _groq
    from groq import Groq
    if _groq is None:
        _groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    r = _groq.chat.completions.create(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), messages=msgs,
                                      temperature=temperature, max_tokens=8000,
                                      response_format={"type": "json_object"})
    return r.choices[0].message.content


def ask_json(prompt: str, system: str = None, quality: bool = False, temperature: float = 0.0, retries: int = 3):
    """Return (parsed_json, provider_name). Prompt must ask for a JSON OBJECT.

    quality=True uses GEMINI_QUALITY_MODEL (low free quota: use for small, important calls only).
    """
    model = os.getenv("GEMINI_QUALITY_MODEL" if quality else "GEMINI_MODEL",
                      "gemini-3.5-flash" if quality else "gemini-3.5-flash-lite")
    last_err = None
    for attempt in range(retries):
        _pace()
        try:
            return parse_json(_gemini_call(prompt, system, model, temperature)), f"gemini:{model}"
        except Exception as e:  # 429 quota / 503 busy / bad JSON
            last_err = e
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                if "per day" in msg.lower() or "PerDay" in msg:
                    break  # daily quota gone: go straight to Groq
                time.sleep(20 * (attempt + 1))
            elif "503" in msg or "UNAVAILABLE" in msg:
                time.sleep(10 * (attempt + 1))
    # backup
    try:
        _pace()
        return parse_json(_groq_call(prompt, system, temperature)), "groq:" + os.getenv("GROQ_MODEL", "")
    except Exception as e:
        raise RuntimeError(f"Both LLMs failed. Gemini: {last_err} | Groq: {e}") from e


if __name__ == "__main__":
    print(ask_json('Return {"ok": true} as JSON.'))
