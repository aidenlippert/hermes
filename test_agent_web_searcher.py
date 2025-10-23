"""
A2A-Compliant Web Searcher Agent

Searches the web and provides summaries:
- Web search and information retrieval
- News aggregation
- Research assistance
- Fact checking
- Current events

Uses Gemini with search grounding for accurate, current information.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import os
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WebSearcher Agent")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
genai.configure(api_key=GOOGLE_API_KEY)


AGENT_INFO = {
    "name": "WebSearcher",
    "description": "Web search and research agent that finds current information, aggregates news, and provides fact-checked summaries from the web.",
    "capabilities": [
        "web_search",
        "research",
        "news_aggregation",
        "fact_checking",
        "current_events",
        "information_retrieval"
    ],
    "version": "1.0.0",
    "endpoint": "http://localhost:10004/a2a"
}


class A2ATask(BaseModel):
    """A2A Task format"""
    task_id: str
    parts: List[Dict[str, Any]]


@app.get("/.well-known/agent.json")
async def agent_card():
    """
    A2A Agent Card - Discovery endpoint
    """
    logger.info("📋 Agent card requested")
    return AGENT_INFO


@app.post("/a2a")
async def handle_task(request: Request):
    """
    A2A Task Handler - Main endpoint for receiving tasks
    """
    try:
        body = await request.json()
        logger.info(f"📨 Received A2A request: {body.get('method')}")

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", 1)

        if method == "tasks.create":
            task_id = params.get("task_id", "unknown")
            parts = params.get("parts", [])

            task_description = ""
            for part in parts:
                if part.get("type") == "TextPart":
                    task_description += part.get("content", "")

            logger.info(f"🔍 Searching web for task: {task_id}")
            logger.info(f"   Query: {task_description[:100]}...")

            # Use Gemini with Google Search grounding
            model = genai.GenerativeModel(
                "gemini-2.0-flash-exp",
                tools="google_search_retrieval"
            )

            prompt = f"""Search the web and provide a comprehensive, well-researched answer to this query:

{task_description}

Please provide:
1. **Summary**: A clear, concise overview of what you found
2. **Key Findings**: Main points and important information
3. **Details**: Relevant details, facts, and context
4. **Sources**: Mention types of sources consulted (news, research, official sites, etc.)

Be accurate, cite current information, and organize your response clearly."""

            response = model.generate_content(prompt)
            search_results = response.text.strip()

            logger.info(f"✅ Search complete ({len(search_results)} characters)")

            # Extract grounding metadata if available
            grounding_metadata = {}
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    grounding_metadata = {
                        "grounded": True,
                        "search_queries": getattr(candidate.grounding_metadata, 'search_entry_point', None)
                    }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "artifacts": [
                        {
                            "type": "TextArtifact",
                            "content": search_results,
                            "metadata": {
                                "agent": "WebSearcher",
                                "grounding": grounding_metadata,
                                "query": task_description[:200]
                            }
                        }
                    ]
                }
            }

        elif method == "tasks.get":
            task_id = params.get("task_id")
            logger.info(f"📊 Status check for task: {task_id}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "status": "completed"
                }
            }

        else:
            logger.warning(f"⚠️ Unknown method: {method}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "jsonrpc": "2.0",
            "id": body.get("id", 1),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@app.get("/")
async def root():
    """Agent info"""
    return {
        "agent": AGENT_INFO["name"],
        "status": "operational",
        "capabilities": AGENT_INFO["capabilities"],
        "agent_card": "/.well-known/agent.json"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔍 WEB SEARCHER AGENT")
    print("="*70)
    print(f"\n🌐 Capabilities: {', '.join(AGENT_INFO['capabilities'])}")
    print(f"🌐 Endpoint: {AGENT_INFO['endpoint']}")
    print(f"📋 Agent Card: http://localhost:10004/.well-known/agent.json")
    print("\n✨ Examples:")
    print("   - What are the latest AI breakthroughs?")
    print("   - Find current news about electric vehicles")
    print("   - Research best practices for remote work")
    print("\n⚠️  Note: Uses Google Search grounding for accurate, current info")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=10004, log_level="info")
