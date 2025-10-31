"""
LangChain Agent Integration

Real AI agent using LangChain for testing ASTRAEUS with actual LLM capabilities.

Prerequisites:
    pip install langchain openai fastapi uvicorn python-dotenv

Environment Variables:
    OPENAI_API_KEY=your-key-here
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.agents import initialize_agent, AgentType, Tool
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not installed. Install with: pip install langchain openai")

app = FastAPI(title="LangChain Agent", version="1.0.0")


class AgentRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = 0.7


class AgentResponse(BaseModel):
    output: str
    status: str
    reasoning: Optional[str] = None
    agent_name: str = "LangChain Agent"


def summarize_text(text: str) -> str:
    """Summarize text using simple extraction"""
    sentences = text.split(". ")
    return ". ".join(sentences[:3]) + "..." if len(sentences) > 3 else text


def extract_keywords(text: str) -> str:
    """Extract keywords from text"""
    words = text.split()
    keywords = [w for w in words if len(w) > 5][:5]
    return ", ".join(keywords)


def sentiment_analysis(text: str) -> str:
    """Simple sentiment analysis"""
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
    negative_words = ["bad", "terrible", "awful", "horrible", "poor", "worst"]

    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)

    if pos_count > neg_count:
        return "Positive"
    elif neg_count > pos_count:
        return "Negative"
    else:
        return "Neutral"


if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")

    tools = [
        Tool(
            name="Summarizer",
            func=summarize_text,
            description="Summarizes long text into concise summaries. Input should be text to summarize."
        ),
        Tool(
            name="KeywordExtractor",
            func=extract_keywords,
            description="Extracts important keywords from text. Input should be text to analyze."
        ),
        Tool(
            name="SentimentAnalyzer",
            func=sentiment_analysis,
            description="Analyzes sentiment of text as Positive, Negative, or Neutral. Input should be text to analyze."
        )
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True
    )

    AGENT_MODE = "langchain"
else:
    agent = None
    AGENT_MODE = "fallback"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "LangChain Agent",
        "version": "1.0.0",
        "mode": AGENT_MODE,
        "langchain_available": LANGCHAIN_AVAILABLE,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """Run LangChain agent"""

    try:
        if AGENT_MODE == "langchain":
            result = agent.run(request.query)

            return AgentResponse(
                output=result,
                status="success",
                reasoning="Used LangChain agent with OpenAI GPT-3.5"
            )
        else:
            fallback_response = f"[FALLBACK MODE] Query received: {request.query}\n\n"
            fallback_response += "LangChain/OpenAI not configured. This is a fallback response.\n"
            fallback_response += "To enable real AI: pip install langchain openai && set OPENAI_API_KEY"

            return AgentResponse(
                output=fallback_response,
                status="success",
                reasoning="Fallback mode (LangChain not configured)"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@app.post("/execute")
async def execute(request: dict):
    """
    ASTRAEUS standard execution endpoint
    """
    try:
        input_data = request.get("input", {})
        query = input_data.get("query", input_data.get("text", ""))
        temperature = input_data.get("temperature", 0.7)

        result = await run_agent(AgentRequest(
            query=query,
            temperature=temperature
        ))

        return {
            "output": {
                "result": result.output,
                "reasoning": result.reasoning
            },
            "status": "success",
            "execution_time_ms": 1500,
            "metadata": {
                "agent_type": "langchain",
                "model": "gpt-3.5-turbo" if AGENT_MODE == "langchain" else "fallback",
                "mode": AGENT_MODE
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print(f"\n🤖 LangChain Agent Server")
    print(f"Mode: {AGENT_MODE}")
    print(f"LangChain Available: {LANGCHAIN_AVAILABLE}")
    print(f"OpenAI Configured: {bool(os.getenv('OPENAI_API_KEY'))}\n")

    uvicorn.run(app, host="0.0.0.0", port=8004)
