"""
ASTRAEUS CLI - Command-line interface for agent management

Usage:
    astraeus init          # Initialize a new agent project
    astraeus register      # Register agent with ASTRAEUS network
    astraeus start         # Start your agent server
    astraeus login         # Login to ASTRAEUS platform
    astraeus deploy        # Deploy to production
    astraeus status        # Check agent status on network
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import Optional


def init_agent_project(name: Optional[str] = None):
    """Initialize a new ASTRAEUS agent project"""
    print("\n🚀 ASTRAEUS Agent Project Initializer\n")

    # Get project details
    if not name:
        name = input("Agent name: ").strip() or "MyAgent"

    description = input("Agent description: ").strip() or f"{name} - An ASTRAEUS agent"
    email = input("Your email: ").strip() or "developer@example.com"

    # Create project directory
    project_dir = Path(name.lower().replace(" ", "-"))

    if project_dir.exists():
        print(f"\n❌ Directory '{project_dir}' already exists!")
        return

    project_dir.mkdir()

    # Create agent.py
    agent_code = f'''"""
{name} - ASTRAEUS Agent

{description}
"""

from astraeus import Agent

# Create your agent
agent = Agent(
    name="{name}",
    description="{description}",
    api_key="your_astraeus_api_key_here",  # Get from https://astraeus.ai
    owner="{email}"
)


@agent.capability("hello", cost=0.00, description="Say hello")
async def hello(name: str = "World") -> dict:
    """Simple hello capability"""
    return {{
        "message": f"Hello, {{name}}!",
        "agent": agent.name,
        "status": "✅ Working!"
    }}


# Add more capabilities here
# @agent.capability("your_capability", cost=0.01, description="...")
# async def your_capability(input: str) -> dict:
#     return {{"result": "..."}}


if __name__ == "__main__":
    print("\\n" + "="*70)
    print(f"🤖 Starting {{agent.name}}")
    print("="*70)
    print(f"\\n📋 Description: {{agent.description}}")
    print(f"📧 Owner: {{agent.owner}}")
    print("\\n" + "="*70 + "\\n")

    # Start the agent server
    agent.serve(host="0.0.0.0", port=8000, register=True)
'''

    (project_dir / "agent.py").write_text(agent_code)

    # Create config file
    config = {
        "name": name,
        "description": description,
        "owner": email,
        "version": "1.0.0",
        "network": "https://web-production-3df46.up.railway.app",
        "port": 8000
    }

    (project_dir / "astraeus.json").write_text(json.dumps(config, indent=2))

    # Create README
    readme = f'''# {name}

{description}

## Quick Start

1. Get your API key from https://astraeus.ai
2. Edit `agent.py` and add your API key
3. Run your agent:

```bash
astraeus start
```

## Deploy to Production

```bash
astraeus deploy
```

## Check Status

```bash
astraeus status
```

## Documentation

- [ASTRAEUS Docs](https://docs.astraeus.ai)
- [SDK Reference](https://docs.astraeus.ai/sdk)
- [Examples](https://github.com/astraeus-ai/examples)
'''

    (project_dir / "README.md").write_text(readme)

    # Create .env template
    env_template = '''# ASTRAEUS Configuration
ASTRAEUS_API_KEY=your_api_key_here
ASTRAEUS_NETWORK=https://web-production-3df46.up.railway.app
AGENT_PORT=8000
'''

    (project_dir / ".env.example").write_text(env_template)

    # Create requirements.txt
    requirements = '''astraeus-sdk>=1.0.0
python-dotenv>=1.0.0
'''

    (project_dir / "requirements.txt").write_text(requirements)

    # Create Dockerfile
    dockerfile = f'''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .
COPY astraeus.json .

EXPOSE 8000

CMD ["python", "agent.py"]
'''

    (project_dir / "Dockerfile").write_text(dockerfile)

    print(f"\n✅ Created agent project: {project_dir}/")
    print("\n📁 Project structure:")
    print(f"   {project_dir}/")
    print("   ├── agent.py           # Your agent code")
    print("   ├── astraeus.json      # Agent configuration")
    print("   ├── requirements.txt   # Python dependencies")
    print("   ├── Dockerfile         # Docker deployment")
    print("   ├── .env.example       # Environment template")
    print("   └── README.md          # Documentation")

    print("\n🔑 Next steps:")
    print(f"   1. cd {project_dir}")
    print("   2. Get your API key from https://astraeus.ai")
    print("   3. Edit agent.py and add your API key")
    print("   4. astraeus start")
    print()


def register_agent():
    """Register agent with ASTRAEUS network via web portal"""
    print("\n🌐 ASTRAEUS Agent Registration\n")
    print("To register your agent, visit:")
    print("\n   👉 https://astraeus.ai/register")
    print("\nOr use the web portal at:")
    print("\n   👉 http://localhost:3000/register (if running locally)")
    print("\nYou'll get an API key that you can use in your agent code.")
    print()


def start_agent():
    """Start the agent server"""
    print("\n🚀 Starting ASTRAEUS Agent...\n")

    if not Path("agent.py").exists():
        print("❌ No agent.py found in current directory!")
        print("   Run 'astraeus init' to create a new agent project")
        return

    # Load config if exists
    if Path("astraeus.json").exists():
        config = json.loads(Path("astraeus.json").read_text())
        print(f"📦 Agent: {config['name']}")
        print(f"📋 Description: {config['description']}")
        print()

    # Run the agent
    os.system("python agent.py")


def login():
    """Login to ASTRAEUS platform"""
    print("\n🔐 ASTRAEUS Platform Login\n")
    print("Visit: https://astraeus.ai/login")
    print("\nOr if running locally: http://localhost:3000/login")
    print()


def deploy_agent():
    """Deploy agent to production"""
    print("\n🚀 ASTRAEUS Agent Deployment\n")

    if not Path("Dockerfile").exists():
        print("❌ No Dockerfile found!")
        print("   Run 'astraeus init' to create a new agent project")
        return

    print("Choose deployment option:")
    print("\n1. Railway (Recommended)")
    print("2. Heroku")
    print("3. Docker Compose")
    print("4. Kubernetes")

    choice = input("\nEnter option (1-4): ").strip()

    if choice == "1":
        print("\n📦 Railway Deployment:")
        print("\n1. Install Railway CLI:")
        print("   npm install -g @railway/cli")
        print("\n2. Login:")
        print("   railway login")
        print("\n3. Deploy:")
        print("   railway up")
        print("\n4. Your agent will be live at:")
        print("   https://your-agent.up.railway.app")

    elif choice == "2":
        print("\n📦 Heroku Deployment:")
        print("\n1. Install Heroku CLI:")
        print("   https://devcenter.heroku.com/articles/heroku-cli")
        print("\n2. Login:")
        print("   heroku login")
        print("\n3. Create app:")
        print("   heroku create your-agent-name")
        print("\n4. Deploy:")
        print("   git push heroku main")

    elif choice == "3":
        print("\n🐳 Docker Deployment:")
        print("\n1. Build image:")
        print("   docker build -t my-agent .")
        print("\n2. Run container:")
        print("   docker run -p 8000:8000 my-agent")

    elif choice == "4":
        print("\n☸️  Kubernetes Deployment:")
        print("\n1. Build and push image:")
        print("   docker build -t your-registry/my-agent .")
        print("   docker push your-registry/my-agent")
        print("\n2. Create deployment:")
        print("   kubectl create deployment my-agent --image=your-registry/my-agent")
        print("\n3. Expose service:")
        print("   kubectl expose deployment my-agent --port=8000 --type=LoadBalancer")

    print()


def check_status():
    """Check agent status on network"""
    print("\n📊 ASTRAEUS Agent Status\n")

    if not Path("astraeus.json").exists():
        print("❌ No astraeus.json found!")
        print("   Run this command from your agent project directory")
        return

    config = json.loads(Path("astraeus.json").read_text())

    print(f"🤖 Agent: {config['name']}")
    print(f"📋 Description: {config['description']}")
    print(f"🌐 Network: {config['network']}")
    print(f"\n📍 Check full status at:")
    print(f"   {config['network']}/agents/{config['name']}")
    print()


def validate_agent_card():
    """Validate agent card compliance"""
    print("\n🔍 ASTRAEUS Agent Card Validator\n")

    endpoint = input("Enter agent endpoint (default: http://localhost:8000): ").strip() or "http://localhost:8000"

    print(f"\nValidating agent at: {endpoint}\n")
    print("Importing validator...")

    try:
        # Import validator module
        sys.path.insert(0, str(Path(__file__).parent))
        from validator import validate_agent_command
        import asyncio

        # Run validation
        asyncio.run(validate_agent_command(endpoint))

    except ImportError as e:
        print(f"❌ Failed to import validator: {e}")
        print("   Make sure astraeus-sdk is properly installed")
    except Exception as e:
        print(f"❌ Validation failed: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ASTRAEUS - AI Agent Network CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  astraeus init              Create a new agent project
  astraeus init "MyAgent"    Create agent with specific name
  astraeus start             Start your agent server
  astraeus register          Register on ASTRAEUS network
  astraeus deploy            Deploy to production
  astraeus status            Check agent status

For more info: https://docs.astraeus.ai
        """
    )

    parser.add_argument(
        "command",
        choices=["init", "register", "start", "login", "deploy", "status", "validate"],
        help="Command to execute"
    )

    parser.add_argument(
        "name",
        nargs="?",
        help="Agent name (for init command)"
    )

    args = parser.parse_args()

    if args.command == "init":
        init_agent_project(args.name)
    elif args.command == "register":
        register_agent()
    elif args.command == "start":
        start_agent()
    elif args.command == "login":
        login()
    elif args.command == "deploy":
        deploy_agent()
    elif args.command == "status":
        check_status()
    elif args.command == "validate":
        validate_agent_card()


if __name__ == "__main__":
    main()
