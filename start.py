#!/usr/bin/env python3
"""
Quick start script for Hermes

Just run: python start.py
"""

import sys
import os

# Add hermes to path
sys.path.insert(0, os.path.dirname(__file__))

from hermes.api.server import app
import uvicorn

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║                🚀 HERMES IS STARTING 🚀                   ║
    ║                                                           ║
    ║            Messenger of the Gods, Now for AI              ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    📍 API Server: http://localhost:8000
    📚 API Docs:   http://localhost:8000/docs
    📊 Status:     http://localhost:8000/status

    💡 Quick Test:
       curl -X POST http://localhost:8000/orchestrate \\
            -H "Content-Type: application/json" \\
            -d '{"query": "help me write code"}'

    Press Ctrl+C to stop
    """)

    uvicorn.run(
        "hermes.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
