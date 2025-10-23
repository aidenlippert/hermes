"""
A2A-Compliant Content Writer Agent

Generates high-quality written content:
- Blog posts
- Articles
- Social media posts
- Marketing copy
- Documentation

Uses Gemini for content generation.
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

app = FastAPI(title="ContentWriter Agent")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")


AGENT_INFO = {
    "name": "ContentWriter",
    "description": "Professional content writer that creates blog posts, articles, social media content, and marketing copy. Specializes in engaging, well-structured written content.",
    "capabilities": [
        "content_write",
        "blog_write",
        "article_write",
        "social_media",
        "marketing_copy",
        "documentation"
    ],
    "version": "1.0.0",
    "endpoint": "http://localhost:10002/a2a"
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

            logger.info(f"✍️ Writing content for task: {task_id}")
            logger.info(f"   Description: {task_description[:100]}...")

            prompt = f"""You are a professional content writer. Create high-quality, engaging content based on this request:

{task_description}

Guidelines:
1. Make it engaging and well-structured
2. Use clear, professional language
3. Include relevant examples or details
4. Optimize for readability
5. If it's a blog post, include an introduction, body, and conclusion
6. If it's social media, be concise and engaging
7. If it's marketing copy, focus on benefits and call-to-action

Provide ONLY the content, without meta-commentary."""

            response = model.generate_content(prompt)
            content = response.text.strip()

            logger.info(f"✅ Content generated ({len(content)} characters)")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "artifacts": [
                        {
                            "type": "TextArtifact",
                            "content": content,
                            "metadata": {
                                "word_count": len(content.split()),
                                "character_count": len(content),
                                "agent": "ContentWriter"
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
    print("✍️ CONTENT WRITER AGENT")
    print("="*70)
    print(f"\n📝 Capabilities: {', '.join(AGENT_INFO['capabilities'])}")
    print(f"🌐 Endpoint: {AGENT_INFO['endpoint']}")
    print(f"📋 Agent Card: http://localhost:10002/.well-known/agent.json")
    print("\n✨ Examples:")
    print("   - Write a blog post about AI trends")
    print("   - Create a tweet about our new product")
    print("   - Write marketing copy for landing page")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=10002, log_level="info")
