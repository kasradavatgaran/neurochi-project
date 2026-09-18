import asyncio
import base64
import logging
import os
import threading
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().with_name(".env"))

LIARA_CHAT_MODEL = os.getenv("LIARA_CHAT_MODEL", "google/gemini-3.5-flash-lite")
LIARA_CHAT_FALLBACK_MODEL = os.getenv("LIARA_CHAT_FALLBACK_MODEL", "google/gemini-3.1-flash-lite")
LIARA_CHAT_REASONING_EFFORT = os.getenv("LIARA_CHAT_REASONING_EFFORT", "low")
LIARA_ANALYSIS_REASONING_EFFORT = os.getenv("LIARA_ANALYSIS_REASONING_EFFORT", "low")
LIARA_TRANSCRIBE_MODEL = os.getenv("LIARA_TRANSCRIBE_MODEL", "google/gemini-2.5-flash")
LIARA_TIMEOUT_SECONDS = float(os.getenv("LIARA_TIMEOUT_SECONDS", "120"))

logger = logging.getLogger("rag_service.generate")
_resolved_chat_model = None
_model_resolution_lock = threading.Lock()


def get_liara_client() -> OpenAI:
    base_url = os.getenv("LIARA_BASE_URL")
    api_key = os.getenv("LIARA_API_KEY")

    if not base_url or not api_key:
        raise RuntimeError("LIARA_BASE_URL or LIARA_API_KEY is not configured.")

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=LIARA_TIMEOUT_SECONDS,
    )


def _available_model_ids(client: OpenAI) -> set[str]:
    try:
        response = client.models.list()
        return {str(item.id) for item in getattr(response, "data", []) if getattr(item, "id", None)}
    except Exception as exc:
        logger.warning("Could not probe Liara models; using configured model: %s", exc)
        return set()


def resolve_chat_model(client: OpenAI | None = None) -> str:
    global _resolved_chat_model
    if _resolved_chat_model:
        return _resolved_chat_model

    with _model_resolution_lock:
        if _resolved_chat_model:
            return _resolved_chat_model
        client = client or get_liara_client()
        available = _available_model_ids(client)
        if available and LIARA_CHAT_MODEL not in available:
            if LIARA_CHAT_FALLBACK_MODEL in available:
                _resolved_chat_model = LIARA_CHAT_FALLBACK_MODEL
                logger.warning(
                    "Configured Liara model %s is unavailable; using fallback %s.",
                    LIARA_CHAT_MODEL,
                    LIARA_CHAT_FALLBACK_MODEL,
                )
            else:
                _resolved_chat_model = LIARA_CHAT_MODEL
        else:
            _resolved_chat_model = LIARA_CHAT_MODEL
        return _resolved_chat_model


def _is_model_availability_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    message = str(exc).lower()
    return status_code in {400, 404} and any(
        marker in message for marker in ("model", "not found", "not supported", "invalid")
    )


def _extract_text_from_completion(response) -> str:
    choice = response.choices[0].message
    content = choice.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    text_parts.append(item["text"])
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    text_parts.append(text_value)
        return "\n".join(part.strip() for part in text_parts if part).strip()

    return ""


def call_liara_chat_completion(
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float = 0.3,
    reasoning_effort: str | None = None,
) -> str:
    global _resolved_chat_model
    client = get_liara_client()
    selected_model = model or resolve_chat_model(client)
    request_kwargs = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "reasoning_effort": reasoning_effort or LIARA_CHAT_REASONING_EFFORT,
    }
    try:
        response = client.chat.completions.create(**request_kwargs)
    except Exception as exc:
        if model or selected_model != LIARA_CHAT_MODEL or not _is_model_availability_error(exc):
            raise
        logger.warning(
            "Liara model %s failed; retrying once with fallback %s: %s",
            selected_model,
            LIARA_CHAT_FALLBACK_MODEL,
            exc,
        )
        _resolved_chat_model = LIARA_CHAT_FALLBACK_MODEL
        request_kwargs["model"] = LIARA_CHAT_FALLBACK_MODEL
        response = client.chat.completions.create(**request_kwargs)
    text = _extract_text_from_completion(response)
    if not text:
        raise RuntimeError("Liara returned an empty chat completion.")
    return text


def stream_liara_chat_completion(
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float = 0.3,
    reasoning_effort: str | None = None,
):
    """Yield text deltas from Liara's OpenAI-compatible SSE response."""
    global _resolved_chat_model
    client = get_liara_client()
    selected_model = model or resolve_chat_model(client)
    request_kwargs = {
        "model": selected_model,
        "messages": messages,
        "temperature": temperature,
        "reasoning_effort": reasoning_effort or LIARA_CHAT_REASONING_EFFORT,
        "stream": True,
    }
    try:
        response = client.chat.completions.create(**request_kwargs)
    except Exception as exc:
        if model or selected_model != LIARA_CHAT_MODEL or not _is_model_availability_error(exc):
            raise
        logger.warning(
            "Liara streaming model %s failed; retrying once with fallback %s: %s",
            selected_model,
            LIARA_CHAT_FALLBACK_MODEL,
            exc,
        )
        _resolved_chat_model = LIARA_CHAT_FALLBACK_MODEL
        request_kwargs["model"] = LIARA_CHAT_FALLBACK_MODEL
        response = client.chat.completions.create(**request_kwargs)

    for chunk in response:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue
        delta = getattr(choices[0], "delta", None)
        content = getattr(delta, "content", None) if delta is not None else None
        if isinstance(content, str) and content:
            yield content


def call_liara_for_analysis(
    prompt: str,
    system_instruction: str = "",
    *,
    reasoning_effort: str | None = None,
) -> str:
    try:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        text = call_liara_chat_completion(
            messages,
            temperature=0.2,
            reasoning_effort=reasoning_effort or LIARA_ANALYSIS_REASONING_EFFORT,
        )
        logger.info("Analysis response received from Liara.")
        return text
    except Exception as e:
        logger.error(f"Error getting analysis from Liara: {e}", exc_info=True)
        return "متاسفانه در پردازش تحلیل توسط هوش مصنوعی خطایی رخ داد."


def _detect_audio_format(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower().lstrip(".")
    if suffix in {"mp3", "wav", "mpeg", "ogg", "webm", "m4a"}:
        return suffix
    return "mp3"


def _transcribe_via_multimodal_chat(audio_path: Path) -> str:
    client = get_liara_client()

    with audio_path.open("rb") as file_obj:
        audio_b64 = base64.b64encode(file_obj.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=LIARA_TRANSCRIBE_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise speech-to-text engine. "
                    "Return only the Persian transcription of the provided audio. "
                    "Do not add explanations, punctuation notes, or extra text."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Transcribe this audio to Persian. Return only the transcription.",
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": _detect_audio_format(audio_path),
                        },
                    },
                ],
            },
        ],
    )

    return _extract_text_from_completion(response)


def _transcribe_via_audio_api(audio_path: Path) -> str:
    client = get_liara_client()

    with audio_path.open("rb") as file_obj:
        response = client.audio.transcriptions.create(
            file=file_obj,
            model=LIARA_TRANSCRIBE_MODEL,
            language="fa",
            response_format="text",
        )

    if isinstance(response, str):
        return response.strip()

    return str(response).strip()


def _transcribe_audio(audio_path: Path) -> str:
    errors = []

    for transcriber in (_transcribe_via_multimodal_chat, _transcribe_via_audio_api):
        try:
            text = transcriber(audio_path)
            if text:
                logger.info("Audio transcription received from Liara.")
                return text
        except Exception as exc:
            errors.append(f"{transcriber.__name__}: {exc}")
            logger.warning("Liara transcription attempt failed via %s: %s", transcriber.__name__, exc)

    raise RuntimeError(" | ".join(errors) or "Liara transcription failed.")


async def call_liara_for_transcribe(audio_path: Path) -> str:
    return await asyncio.to_thread(_transcribe_audio, audio_path)
