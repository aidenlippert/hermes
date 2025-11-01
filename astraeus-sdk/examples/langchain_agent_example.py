"""
LangChain Agent Integration Example

This example shows how to wrap an existing LangChain agent and publish it
to the ASTRAEUS network using the LangChainAdapter.
"""

from astraeus.adapters import LangChainAdapter


class MockLangChainAgent:
    """
    Mock LangChain agent for demonstration
    Replace this with your actual LangChain agent:

    from langchain.agents import create_openai_agent
    from langchain.tools import Tool
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4")
    tools = [...]
    langchain_agent = create_openai_agent(llm, tools)
    """

    async def invoke(self, query: str) -> str:
        """Mock invoke method - replace with real LangChain agent"""

        responses = {
            "hello": "Hello! I'm a LangChain agent running on ASTRAEUS.",
            "weather": "I can help with weather by using my integrated tools.",
            "help": "I'm an AI assistant powered by LangChain and deployed on ASTRAEUS network.",
        }

        query_lower = query.lower()
        for keyword, response in responses.items():
            if keyword in query_lower:
                return response

        return f"I received your query: '{query}'. I'm a demo LangChain agent. Replace me with a real implementation!"


def create_langchain_agent():
    """
    Create and configure your LangChain agent here

    Example with real LangChain:
    ```python
    from langchain.agents import create_openai_agent
    from langchain.tools import Tool
    from langchain_openai import ChatOpenAI

    def search_web(query: str) -> str:
        # Your search implementation
        return f"Search results for: {query}"

    def calculate(expression: str) -> str:
        # Your calculator implementation
        return str(eval(expression))

    tools = [
        Tool(name="search", func=search_web, description="Search the web"),
        Tool(name="calculator", func=calculate, description="Calculate math")
    ]

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    agent = create_openai_agent(llm, tools)

    return agent
    ```
    """
    return MockLangChainAgent()


if __name__ == "__main__":
    print("\n🦜 LangChain Agent on ASTRAEUS Network")
    print("=" * 50)
    print("This example shows how to:")
    print("  • Wrap existing LangChain agents")
    print("  • Publish to ASTRAEUS network")
    print("  • Auto-register capabilities")
    print("  • Enable A2A communication")
    print("=" * 50)
    print()

    langchain_agent = create_langchain_agent()

    astraeus_agent = LangChainAdapter(
        agent=langchain_agent,
        name="LangChain-Assistant",
        description="AI assistant powered by LangChain with web search and calculator tools",
        api_key="astraeus_demo_key_12345",
        owner="demo@example.com",
        cost_per_call=0.03
    )

    print("💡 To use with real LangChain:")
    print("   1. Install: pip install 'astraeus-sdk[langchain]'")
    print("   2. Replace MockLangChainAgent with your agent")
    print("   3. Add your OpenAI API key")
    print("   4. Configure tools and prompts")
    print()

    astraeus_agent.serve(host="0.0.0.0", port=8003, register=True)
