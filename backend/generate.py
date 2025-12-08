# generate.py
from pathlib import Path

import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_MODEL_NAME = "models/gemini-2.5-flash"

logger = logging.getLogger("rag_service.generate")



def call_gemini_for_analysis(prompt: str) -> str:

    
    try:
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=""),
            contents=prompt
        )
        logger.info("RAG response received from Gemini.")
        return response.text
    except Exception as e:
        logger.error(f"Error getting analysis from Gemini: {e}", exc_info=True)
        return "متاسفانه در پردازش تحلیل توسط هوش مصنوعی خطایی رخ داد."
    

async def call_gemini_for_transcribe(audio_path: Path) -> str:
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()

    client = genai.Client()
    response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        'Transcribe to farsi',
        types.Part.from_bytes(
        data=audio_bytes,
        mime_type='audio/mp3',
        )
    ]
    )

    return response.text
    





