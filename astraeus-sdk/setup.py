"""
ASTRAEUS SDK - Build and publish AI agents to the ASTRAEUS Network
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="astraeus-sdk",
    version="1.0.0",
    author="ASTRAEUS Team",
    author_email="support@astraeus.ai",
    description="Build and publish AI agents to the ASTRAEUS Network",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/astraeus-ai/sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "langchain": [
            "langchain>=0.1.0",
            "langchain-openai>=0.0.2",
        ],
        "crewai": [
            "crewai>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "astraeus=astraeus.cli:main",
        ],
    },
    keywords="ai agents agentic-ai agent-network a2a-protocol autonomous-agents",
    project_urls={
        "Documentation": "https://docs.astraeus.ai",
        "Source": "https://github.com/astraeus-ai/sdk",
        "Tracker": "https://github.com/astraeus-ai/sdk/issues",
    },
)
