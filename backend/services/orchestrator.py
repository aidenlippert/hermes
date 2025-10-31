"""
Intelligent Multi-Agent Orchestrator

Analyzes user queries, decomposes tasks, resolves dependencies,
selects optimal agents, and coordinates multi-agent execution.

Sprint 2: Orchestration & Intelligence
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import logging
from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent, Task, TaskStatus, Execution
from backend.database.models_orchestration import (
    OrchestrationPlan,
    OrchestrationDependency,
    AgentCollaboration,
    CollaborationResult,
    OrchestrationMetric,
    AgentCapabilityCache,
    CollaborationPattern,
    OrchestrationStatus,
    DependencyType
)

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Analyzes user queries to extract intent and decompose into sub-tasks"""

    async def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query to extract structured intent.

        Returns:
            {
                "main_intent": str,
                "sub_intents": List[str],
                "complexity": float (0.0 - 1.0),
                "requires_orchestration": bool,
                "suggested_pattern": CollaborationPattern
            }
        """
        # Simple keyword-based intent analysis (replace with LLM in production)
        query_lower = query.lower()

        # Detect complexity indicators
        complexity_keywords = [
            "and", "then", "also", "multiple", "several", "all",
            "compare", "analyze", "comprehensive", "detailed"
        ]
        complexity = sum(1 for kw in complexity_keywords if kw in query_lower) / 10.0
        complexity = min(complexity, 1.0)

        # Detect orchestration need
        orchestration_keywords = [
            "and then", "after that", "compare", "versus", "vs",
            "all", "multiple", "both", "each"
        ]
        requires_orchestration = any(kw in query_lower for kw in orchestration_keywords)

        # Suggest pattern based on keywords
        pattern = self._suggest_pattern(query_lower)

        # Decompose into sub-intents (simple sentence splitting)
        sub_intents = self._decompose(query, pattern)

        return {
            "main_intent": query,
            "sub_intents": sub_intents,
            "complexity": complexity,
            "requires_orchestration": requires_orchestration,
            "suggested_pattern": pattern
        }

    def _suggest_pattern(self, query: str) -> CollaborationPattern:
        """Suggest collaboration pattern based on query structure"""
        if "then" in query or "after" in query or "next" in query:
            return CollaborationPattern.SEQUENTIAL
        elif "compare" in query or "versus" in query or "vs" in query:
            return CollaborationPattern.VOTE
        elif "debate" in query or "discuss" in query or "argue" in query:
            return CollaborationPattern.DEBATE
        elif "all" in query or "multiple" in query or "several" in query:
            return CollaborationPattern.PARALLEL
        else:
            return CollaborationPattern.SEQUENTIAL

    def _decompose(self, query: str, pattern: CollaborationPattern) -> List[str]:
        """Decompose query into sub-tasks based on pattern"""
        # Simple decomposition (replace with LLM in production)
        if pattern == CollaborationPattern.SEQUENTIAL:
            # Split on temporal connectors
            parts = query.replace(" and then ", "|").replace(" then ", "|").split("|")
            return [p.strip() for p in parts if p.strip()]
        elif pattern in [CollaborationPattern.PARALLEL, CollaborationPattern.VOTE]:
            # Split on "and" or commas
            parts = query.replace(" and ", "|").replace(", ", "|").split("|")
            return [p.strip() for p in parts if p.strip()]
        else:
            return [query]


class DependencyResolver:
    """Resolves task dependencies and creates execution DAG"""

    def build_graph(self, sub_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build dependency graph from sub-tasks.

        Args:
            sub_tasks: List of {id, description, required_capabilities}

        Returns:
            {
                "nodes": List[Dict],  # Task nodes
                "edges": List[Dict],  # Dependencies
                "execution_order": List[List[str]]  # Topologically sorted levels
            }
        """
        nodes = []
        edges = []

        for i, task in enumerate(sub_tasks):
            node_id = f"step_{i}"
            nodes.append({
                "id": node_id,
                "description": task.get("description", ""),
                "capabilities": task.get("required_capabilities", []),
                "index": i
            })

        # Detect dependencies (simple: sequential by default, parallel if independent)
        # In production, use LLM to detect semantic dependencies
        for i in range(len(nodes) - 1):
            edges.append({
                "source": nodes[i]["id"],
                "target": nodes[i + 1]["id"],
                "type": DependencyType.REQUIRES
            })

        # Topological sort for execution order
        execution_order = self._topological_sort(nodes, edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "execution_order": execution_order
        }

    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[List[str]]:
        """
        Topological sort with level assignment for parallel execution.

        Returns list of levels, where each level contains tasks that can run in parallel.
        """
        # Build adjacency list and in-degree map
        graph = defaultdict(list)
        in_degree = {node["id"]: 0 for node in nodes}

        for edge in edges:
            if edge["type"] == DependencyType.REQUIRES:
                graph[edge["source"]].append(edge["target"])
                in_degree[edge["target"]] += 1

        # BFS with level tracking
        levels = []
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])

        while queue:
            # All nodes in current level have no dependencies
            level = []
            level_size = len(queue)

            for _ in range(level_size):
                node = queue.popleft()
                level.append(node)

                # Reduce in-degree for neighbors
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            if level:
                levels.append(level)

        return levels


class AgentSelector:
    """Selects optimal agents for tasks based on capabilities and performance"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def select_agents(
        self,
        task_description: str,
        required_capabilities: List[str],
        count: int = 1
    ) -> List[Agent]:
        """
        Select optimal agents for a task.

        Args:
            task_description: Natural language task description
            required_capabilities: Required capabilities
            count: Number of agents to select

        Returns:
            List of selected Agent objects
        """
        # Query agents with required capabilities
        query = select(Agent).where(
            Agent.status == "active"
        )

        result = await self.db.execute(query)
        all_agents = result.scalars().all()

        # Score agents based on capabilities match and performance
        scored_agents = []
        for agent in all_agents:
            score = await self._score_agent(agent, required_capabilities, task_description)
            scored_agents.append((agent, score))

        # Sort by score (descending) and select top N
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return [agent for agent, _ in scored_agents[:count]]

    async def _score_agent(
        self,
        agent: Agent,
        required_capabilities: List[str],
        task_description: str
    ) -> float:
        """
        Score agent suitability for task.

        Factors:
        - Capability match (40%)
        - Trust score (30%)
        - Success rate (20%)
        - Cost efficiency (10%)
        """
        # Capability match
        agent_caps = set(agent.capabilities or [])
        required_caps = set(required_capabilities)
        capability_match = len(agent_caps & required_caps) / max(len(required_caps), 1)

        # Performance metrics
        success_rate = (
            agent.successful_calls / max(agent.total_calls, 1)
            if agent.total_calls > 0 else 0.5
        )
        trust_score = agent.trust_score

        # Cost efficiency (inverse of cost)
        cost_efficiency = 1.0 / (agent.cost_per_request + 0.01)  # Avoid division by zero

        # Weighted score
        score = (
            capability_match * 0.4 +
            trust_score * 0.3 +
            success_rate * 0.2 +
            min(cost_efficiency, 1.0) * 0.1
        )

        return score


class OrchestratorAgent:
    """
    Main orchestrator for intelligent multi-agent coordination.

    Workflow:
    1. Analyze intent and complexity
    2. Decompose into sub-tasks
    3. Build dependency graph
    4. Select optimal agents
    5. Coordinate execution (sequential, parallel, or hybrid)
    6. Synthesize results
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_analyzer = IntentAnalyzer()
        self.dependency_resolver = DependencyResolver()
        self.agent_selector = AgentSelector(db)

    async def orchestrate(
        self,
        user_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration entry point.

        Args:
            user_id: User ID making the request
            query: Natural language query
            context: Optional execution context

        Returns:
            {
                "plan_id": str,
                "status": str,
                "result": Any,
                "execution_summary": Dict
            }
        """
        start_time = datetime.utcnow()

        # Step 1: Intent analysis
        intent_data = await self.intent_analyzer.analyze(query)
        logger.info(f"Intent analysis: {intent_data}")

        # Step 2: Decompose into sub-tasks
        sub_tasks = [
            {
                "description": sub_intent,
                "required_capabilities": self._extract_capabilities(sub_intent)
            }
            for sub_intent in intent_data["sub_intents"]
        ]

        # Step 3: Build dependency graph
        graph = self.dependency_resolver.build_graph(sub_tasks)

        # Step 4: Create orchestration plan
        plan = OrchestrationPlan(
            user_id=user_id,
            query=query,
            pattern=intent_data["suggested_pattern"],
            parsed_intents=intent_data,
            complexity_score=intent_data["complexity"],
            execution_graph=graph,
            status=OrchestrationStatus.PLANNING
        )
        self.db.add(plan)
        await self.db.flush()

        # Step 5: Agent selection for each step
        agent_assignments = {}
        for node in graph["nodes"]:
            agents = await self.agent_selector.select_agents(
                task_description=node["description"],
                required_capabilities=node["capabilities"],
                count=1
            )
            if agents:
                agent_assignments[node["id"]] = agents[0].id

        plan.agent_assignments = agent_assignments
        plan.status = OrchestrationStatus.READY

        # Step 6: Execute based on pattern
        if intent_data["suggested_pattern"] == CollaborationPattern.SEQUENTIAL:
            result = await self._execute_sequential(plan, graph, agent_assignments)
        elif intent_data["suggested_pattern"] == CollaborationPattern.PARALLEL:
            result = await self._execute_parallel(plan, graph, agent_assignments)
        else:
            # Default to sequential
            result = await self._execute_sequential(plan, graph, agent_assignments)

        # Step 7: Finalize plan
        plan.final_result = result
        plan.status = OrchestrationStatus.COMPLETED
        plan.completed_at = datetime.utcnow()
        plan.total_duration = (datetime.utcnow() - start_time).total_seconds()

        await self.db.commit()

        return {
            "plan_id": plan.id,
            "status": plan.status.value,
            "result": result,
            "execution_summary": {
                "pattern": plan.pattern.value,
                "steps": plan.total_steps,
                "duration": plan.total_duration,
                "cost": plan.total_cost
            }
        }

    async def _execute_sequential(
        self,
        plan: OrchestrationPlan,
        graph: Dict[str, Any],
        agent_assignments: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute tasks sequentially (pipeline)"""
        results = {}
        context = {}

        for level in graph["execution_order"]:
            for step_id in level:
                # Find node details
                node = next(n for n in graph["nodes"] if n["id"] == step_id)
                agent_id = agent_assignments.get(step_id)

                if not agent_id:
                    logger.warning(f"No agent assigned for step {step_id}")
                    continue

                # Execute step (stub - replace with actual agent call)
                result = await self._execute_step(
                    agent_id=agent_id,
                    task_description=node["description"],
                    context=context
                )

                results[step_id] = result
                context[step_id] = result  # Pass result to next step

                plan.completed_steps += 1

        return {"results": results, "final_output": results.get(graph["nodes"][-1]["id"])}

    async def _execute_parallel(
        self,
        plan: OrchestrationPlan,
        graph: Dict[str, Any],
        agent_assignments: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute independent tasks in parallel"""
        all_results = {}

        for level in graph["execution_order"]:
            # Execute all tasks in this level in parallel
            tasks = []
            for step_id in level:
                node = next(n for n in graph["nodes"] if n["id"] == step_id)
                agent_id = agent_assignments.get(step_id)

                if agent_id:
                    task = self._execute_step(
                        agent_id=agent_id,
                        task_description=node["description"],
                        context=all_results
                    )
                    tasks.append((step_id, task))

            # Wait for all tasks in this level to complete
            results = await asyncio.gather(*[task for _, task in tasks])

            # Store results
            for (step_id, _), result in zip(tasks, results):
                all_results[step_id] = result
                plan.completed_steps += 1

        return {"results": all_results}

    async def _execute_step(
        self,
        agent_id: str,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single step with an agent.

        In production, this would make actual HTTP calls to agents.
        For now, returns a stub result.
        """
        # Get agent details
        agent = await self.db.get(Agent, agent_id)

        # Simulate agent execution (replace with actual API call)
        logger.info(f"Executing step with agent {agent.name}: {task_description}")

        return {
            "agent": agent.name,
            "task": task_description,
            "result": f"Result from {agent.name}",
            "confidence": 0.9,
            "duration": 1.0
        }

    def _extract_capabilities(self, task_description: str) -> List[str]:
        """Extract required capabilities from task description"""
        # Simple keyword matching (replace with LLM in production)
        capability_keywords = {
            "search": ["search", "find", "lookup", "query"],
            "generate": ["generate", "create", "write", "compose"],
            "analyze": ["analyze", "evaluate", "assess", "review"],
            "translate": ["translate", "convert", "transform"],
            "summarize": ["summarize", "condense", "brief"]
        }

        task_lower = task_description.lower()
        capabilities = []

        for capability, keywords in capability_keywords.items():
            if any(kw in task_lower for kw in keywords):
                capabilities.append(capability)

        return capabilities or ["general"]
