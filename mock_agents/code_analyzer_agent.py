"""
Code Analyzer Agent Mock Server

Analyzes code quality and suggests improvements for testing ASTRAEUS.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import random

app = FastAPI(title="Code Analyzer Agent", version="1.0.0")


class CodeAnalysisRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    check_security: Optional[bool] = True


class Issue(BaseModel):
    severity: str
    line: int
    message: str
    suggestion: str


class CodeAnalysisResponse(BaseModel):
    quality_score: float
    issues: List[Issue]
    metrics: Dict[str, int]
    suggestions: List[str]
    agent_name: str = "Code Analyzer"


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "Code Analyzer",
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code quality"""

    lines = request.code.split("\n")
    num_lines = len(lines)

    issues = []

    if num_lines > 50:
        issues.append(Issue(
            severity="warning",
            line=1,
            message="Function too long",
            suggestion="Consider breaking into smaller functions"
        ))

    if "TODO" in request.code:
        issues.append(Issue(
            severity="info",
            line=random.randint(1, num_lines),
            message="TODO comment found",
            suggestion="Complete or remove TODO comments"
        ))

    if request.check_security and ("eval(" in request.code or "exec(" in request.code):
        issues.append(Issue(
            severity="critical",
            line=random.randint(1, num_lines),
            message="Security risk: Use of eval/exec",
            suggestion="Avoid using eval/exec for security reasons"
        ))

    quality_score = max(0.5, 1.0 - (len(issues) * 0.1))

    return CodeAnalysisResponse(
        quality_score=round(quality_score, 2),
        issues=issues,
        metrics={
            "lines_of_code": num_lines,
            "complexity": random.randint(5, 20),
            "maintainability_index": random.randint(60, 95)
        },
        suggestions=[
            "Add type hints for better code clarity",
            "Consider adding docstrings to functions",
            "Use consistent naming conventions"
        ]
    )


@app.post("/execute")
async def execute(request: dict):
    """
    ASTRAEUS standard execution endpoint
    """
    try:
        input_data = request.get("input", {})
        code = input_data.get("code", "")
        language = input_data.get("language", "python")

        result = await analyze_code(CodeAnalysisRequest(
            code=code,
            language=language
        ))

        return {
            "output": result.dict(),
            "status": "success",
            "execution_time_ms": 200,
            "metadata": {
                "agent_type": "code_analysis",
                "model": "mock-analyzer-v1",
                "language": language
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
