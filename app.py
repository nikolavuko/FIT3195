import os
from typing import List, Literal, Optional, Dict, Any

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


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None  # allow client override if desired


class ChatResponse(BaseModel):
    reply: str


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
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static frontend (index.html, JS, CSS)
static_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="web")

