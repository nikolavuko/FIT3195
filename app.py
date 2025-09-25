import base64
import os
from typing import List, Literal, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables (OPENAI_API_KEY in .env)
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found. Add it to your .env file.")

client = OpenAI(api_key=api_key)

# Optional ElevenLabs voice settings
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
eleven_voice_id = os.getenv("ELEVENLABS_VOICE_ID")
eleven_model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2")


def _synthesise_elevenlabs_speech(text: str) -> Optional[str]:
    """Return base64 audio for the supplied text or None if TTS is disabled/failed."""
    if not eleven_api_key or not eleven_voice_id or not text:
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{eleven_voice_id}"
    headers = {
        "xi-api-key": eleven_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": eleven_model_id,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75,
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
    except Exception:
        return None

    return base64.b64encode(response.content).decode("ascii")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # allow client override if desired


class ChatResponse(BaseModel):
    reply: str
    audio_base64: Optional[str] = None


app = FastAPI(title="Talking Web App API")

# CORS: allow same-origin and local dev defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    # Default model aligned with existing script
    model = req.model or "gpt-5-nano"

    try:
        # The Responses API can take a list of messages directly via `input`
        response = client.responses.create(
            model=model,
            input=[m.model_dump() for m in req.messages],
        )
        reply = (response.output_text or "").strip()

        audio_base64 = _synthesise_elevenlabs_speech(reply)

        return ChatResponse(reply=reply, audio_base64=audio_base64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static frontend (index.html, JS, CSS)
static_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

