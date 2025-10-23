"""
A2A-Compliant Data Analyzer Agent

Analyzes data and provides insights:
- CSV/JSON data analysis
- Statistical analysis
- Pattern detection
- Trend identification
- Data visualization recommendations

Uses Gemini for intelligent data analysis.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import os
import logging
import uvicorn
import json
import csv
from io import StringIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DataAnalyzer Agent")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyAOceA7tUW7cPenJol4pyOcNyTBpa_a5cg")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")


AGENT_INFO = {
    "name": "DataAnalyzer",
    "description": "Intelligent data analysis agent that processes CSV/JSON data, identifies patterns, performs statistical analysis, and provides actionable insights.",
    "capabilities": [
        "data_analysis",
        "csv_analysis",
        "json_analysis",
        "statistical_analysis",
        "pattern_detection",
        "data_insights"
    ],
    "version": "1.0.0",
    "endpoint": "http://localhost:10003/a2a"
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


def detect_data_format(data_str: str) -> tuple[str, Any]:
    """Detect if data is CSV or JSON"""
    data_str = data_str.strip()

    # Try JSON first
    try:
        data = json.loads(data_str)
        return "json", data
    except:
        pass

    # Try CSV
    try:
        reader = csv.DictReader(StringIO(data_str))
        rows = list(reader)
        if rows:
            return "csv", rows
    except:
        pass

    return "unknown", data_str


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

            logger.info(f"📊 Analyzing data for task: {task_id}")
            logger.info(f"   Description: {task_description[:100]}...")

            # Try to detect data format
            data_format, parsed_data = detect_data_format(task_description)

            if data_format == "json":
                data_preview = json.dumps(parsed_data, indent=2)[:500]
                data_info = f"JSON data with {len(parsed_data) if isinstance(parsed_data, list) else 1} records"
            elif data_format == "csv":
                data_preview = str(parsed_data[:3])[:500]
                data_info = f"CSV data with {len(parsed_data)} rows and {len(parsed_data[0].keys()) if parsed_data else 0} columns"
            else:
                data_preview = task_description[:500]
                data_info = "Text description or unstructured data"

            prompt = f"""You are a professional data analyst. Analyze this data and provide insights:

Data Format: {data_info}
Data Preview:
{data_preview}

Full Request:
{task_description}

Please provide:
1. **Summary**: Overview of the data
2. **Key Statistics**: Important numbers and metrics
3. **Patterns & Trends**: What patterns do you see?
4. **Insights**: What does this data tell us?
5. **Recommendations**: Actionable next steps

Format your response clearly with sections and bullet points."""

            response = model.generate_content(prompt)
            analysis = response.text.strip()

            logger.info(f"✅ Analysis complete ({len(analysis)} characters)")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "task_id": task_id,
                    "status": "completed",
                    "artifacts": [
                        {
                            "type": "TextArtifact",
                            "content": analysis,
                            "metadata": {
                                "data_format": data_format,
                                "record_count": len(parsed_data) if isinstance(parsed_data, list) else 1,
                                "agent": "DataAnalyzer"
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
    print("📊 DATA ANALYZER AGENT")
    print("="*70)
    print(f"\n📈 Capabilities: {', '.join(AGENT_INFO['capabilities'])}")
    print(f"🌐 Endpoint: {AGENT_INFO['endpoint']}")
    print(f"📋 Agent Card: http://localhost:10003/.well-known/agent.json")
    print("\n✨ Examples:")
    print("   - Analyze sales data for Q4")
    print("   - Find patterns in customer behavior")
    print("   - Provide insights on website traffic")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=10003, log_level="info")
