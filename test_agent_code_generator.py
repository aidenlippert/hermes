"""
Test A2A Agent - Code Generator

This is a simple A2A-compliant agent for testing Hermes.

It demonstrates:
1. Agent Card at /.well-known/agent.json
2. A2A task handling (JSON-RPC 2.0)
3. Artifact generation

Run this on port 10001:
    python test_agent_code_generator.py
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import Dict, Any
import google.generativeai as genai
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CodeGenerator Agent", version="1.0")

# Configure Gemini for code generation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")


@app.get("/.well-known/agent.json")
async def agent_card():
    """
    Agent Card - This is how Hermes discovers what this agent can do.

    This is THE MOST IMPORTANT endpoint for A2A compliance.
    """
    return {
        "name": "CodeGenerator",
        "description": "Generates code in any programming language using Gemini",
        "version": "1.0.0",
        "endpoint": "http://localhost:10001/a2a",
        "capabilities": [
            {
                "name": "code_write",
                "description": "Write new code from description",
                "parameters": {
                    "language": "string (optional)",
                    "description": "string (required)"
                }
            },
            {
                "name": "code_debug",
                "description": "Debug and fix code",
                "parameters": {
                    "code": "string (required)",
                    "error": "string (optional)"
                }
            },
            {
                "name": "code_explain",
                "description": "Explain what code does",
                "parameters": {
                    "code": "string (required)"
                }
            }
        ],
        "authentication": None,
        "supportedModalities": ["text"],
        "streaming": False
    }


@app.post("/a2a")
async def handle_task(request: Request):
    """
    A2A Task Handler - This is where Hermes sends tasks.

    Receives JSON-RPC 2.0 requests, processes them, returns artifacts.
    """
    body = await request.json()

    logger.info(f"📥 Received task: {body.get('id')}")

    # Validate JSON-RPC 2.0 format
    if body.get("jsonrpc") != "2.0":
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC version"
                },
                "id": body.get("id")
            }
        )

    # Extract task details
    params = body.get("params", {})
    task_id = body.get("id")
    parts = params.get("parts", [])

    # Get the task description from parts
    task_description = ""
    for part in parts:
        if part.get("type") == "TextPart":
            task_description = part.get("content", "")
            break

    if not task_description:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "No task description provided"
                },
                "id": task_id
            }
        )

    logger.info(f"🤖 Processing: {task_description[:100]}...")

    try:
        # Use Gemini to generate code
        prompt = f"""You are a code generation agent.

Task: {task_description}

Generate clean, working code with comments. Include only the code, no explanations."""

        response = model.generate_content(prompt)
        generated_code = response.text.strip()

        # Remove markdown code blocks if present
        if generated_code.startswith("```"):
            lines = generated_code.split("\n")
            generated_code = "\n".join(lines[1:-1])

        logger.info(f"✅ Generated {len(generated_code)} characters of code")

        # Return A2A-compliant response with artifact
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "artifacts": [
                        {
                            "type": "CodeArtifact",
                            "content": generated_code,
                            "metadata": {
                                "language": "auto-detected",
                                "lines": len(generated_code.split("\n")),
                                "model": "gemini-2.0-flash-exp"
                            }
                        }
                    ],
                    "metadata": {
                        "processing_time": "1.2s",
                        "tokens_used": 150
                    }
                },
                "id": task_id
            }
        )

    except Exception as e:
        logger.error(f"❌ Error generating code: {e}")

        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Code generation failed: {str(e)}"
                },
                "id": task_id
            }
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "CodeGenerator", "version": "1.0"}


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 CODEGENERATOR AGENT STARTING")
    print("="*60)
    print("\n📍 A2A Endpoint: http://localhost:10001/a2a")
    print("📋 Agent Card: http://localhost:10001/.well-known/agent.json")
    print("\n💡 Test with:")
    print('   curl http://localhost:10001/.well-known/agent.json')
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=10001)
