"""
Translation Agent Mock Server

Simulates a translation agent for testing ASTRAEUS.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Translation Agent", version="1.0.0")


class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = "auto"
    target_language: str = "es"


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    agent_name: str = "Translation Bot"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "Translation Bot",
        "version": "1.0.0"
    }


@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    """Translate text between languages"""

    translations = {
        "es": f"[ES] {request.text}",
        "fr": f"[FR] {request.text}",
        "de": f"[DE] {request.text}",
        "ja": f"[JA] {request.text}",
        "zh": f"[ZH] {request.text}",
    }

    translated = translations.get(
        request.target_language,
        f"[{request.target_language.upper()}] {request.text}"
    )

    return TranslationResponse(
        translated_text=translated,
        source_language=request.source_language if request.source_language != "auto" else "en",
        target_language=request.target_language,
        confidence=0.95
    )


@app.post("/execute")
async def execute(request: dict):
    """
    ASTRAEUS standard execution endpoint
    """
    try:
        input_data = request.get("input", {})
        text = input_data.get("text", "")
        target_lang = input_data.get("target_language", "es")

        result = await translate(TranslationRequest(
            text=text,
            target_language=target_lang
        ))

        return {
            "output": result.dict(),
            "status": "success",
            "execution_time_ms": 150,
            "metadata": {
                "agent_type": "translation",
                "model": "mock-translator-v1"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
