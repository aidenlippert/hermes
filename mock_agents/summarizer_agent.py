"""
Summarizer Agent Mock Server

Free agent that summarizes text for testing ASTRAEUS.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Free Summarizer Agent", version="1.0.0")


class SummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 100
    style: Optional[str] = "concise"


class SummarizeResponse(BaseModel):
    summary: str
    key_points: List[str]
    original_length: int
    summary_length: int
    compression_ratio: float
    agent_name: str = "Free Summarizer"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "Free Summarizer",
        "version": "1.0.0",
        "is_free": True
    }


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """Summarize text"""

    words = request.text.split()
    original_length = len(words)

    summary_length = min(request.max_length, original_length // 3)
    summary = " ".join(words[:summary_length]) + "..."

    key_points = [
        f"Point 1: {' '.join(words[:5])}...",
        f"Point 2: {' '.join(words[5:10])}...",
        f"Point 3: {' '.join(words[10:15])}..."
    ]

    return SummarizeResponse(
        summary=summary,
        key_points=key_points,
        original_length=original_length,
        summary_length=summary_length,
        compression_ratio=round(summary_length / original_length, 2) if original_length > 0 else 0
    )


@app.post("/execute")
async def execute(request: dict):
    """
    ASTRAEUS standard execution endpoint
    """
    try:
        input_data = request.get("input", {})
        text = input_data.get("text", "")
        max_length = input_data.get("max_length", 100)

        result = await summarize(SummarizeRequest(
            text=text,
            max_length=max_length
        ))

        return {
            "output": result.dict(),
            "status": "success",
            "execution_time_ms": 80,
            "metadata": {
                "agent_type": "summarization",
                "model": "mock-summarizer-v1",
                "is_free": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
