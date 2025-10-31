"""
Multi-Agent Collaboration Patterns

Implements various collaboration patterns for multi-agent coordination:
- Sequential (Pipeline): A → B → C
- Parallel: Independent execution
- Vote: Consensus voting
- Debate: Multi-round deliberation
- Swarm: Distributed problem-solving
- Consensus: Byzantine-style agreement

Sprint 2: Orchestration & Intelligence
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Agent
from backend.database.models_orchestration import (
    AgentCollaboration,
    CollaborationResult,
    CollaborationPattern,
    OrchestrationStatus
)

logger = logging.getLogger(__name__)


class ResultSynthesizer:
    """Synthesizes results from multiple agents"""

    @staticmethod
    def merge(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results by combining all outputs"""
        merged = {
            "type": "merged",
            "sources": [r.get("agent") for r in results],
            "outputs": [r.get("result") for r in results],
            "confidence": sum(r.get("confidence", 0) for r in results) / len(results)
        }
        return merged

    @staticmethod
    def vote(results: List[Dict[str, Any]], weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """Vote on results, optionally with weighted voting"""
        if not weights:
            weights = [1.0] * len(results)

        # Count votes (assuming results have a "vote" field or use the result itself)
        votes = Counter()
        for result, weight in zip(results, weights):
            vote_value = str(result.get("result"))
            votes[vote_value] += weight

        # Get winner
        winner, score = votes.most_common(1)[0]
        total_votes = sum(votes.values())

        return {
            "type": "vote",
            "winner": winner,
            "confidence": score / total_votes,
            "vote_distribution": dict(votes),
            "total_votes": total_votes
        }

    @staticmethod
    def debate_winner(
        results: List[Dict[str, Any]],
        rounds: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Determine debate winner based on final round quality"""
        # Use last round results
        final_round = rounds[-1] if rounds else results

        # Score based on confidence and quality
        scored = [
            (r, r.get("confidence", 0) * r.get("quality", 1.0))
            for r in final_round
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        winner = scored[0][0] if scored else results[0]

        return {
            "type": "debate_winner",
            "winner": winner.get("result"),
            "rounds": len(rounds),
            "confidence": winner.get("confidence", 0),
            "agent": winner.get("agent")
        }

    @staticmethod
    def consensus(results: List[Dict[str, Any]], threshold: float = 0.66) -> Dict[str, Any]:
        """Determine consensus if agreement exceeds threshold"""
        # Group similar results
        result_groups = {}
        for r in results:
            key = str(r.get("result"))
            if key not in result_groups:
                result_groups[key] = []
            result_groups[key].append(r)

        # Check if any group exceeds threshold
        total = len(results)
        for key, group in result_groups.items():
            if len(group) / total >= threshold:
                return {
                    "type": "consensus",
                    "result": key,
                    "agreement": len(group) / total,
                    "threshold": threshold,
                    "supporting_agents": [r.get("agent") for r in group]
                }

        # No consensus reached
        return {
            "type": "no_consensus",
            "threshold": threshold,
            "groups": {k: len(v) for k, v in result_groups.items()}
        }


class CollaborationEngine:
    """Executes different collaboration patterns"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.synthesizer = ResultSynthesizer()

    async def execute_pattern(
        self,
        pattern: CollaborationPattern,
        agents: List[Agent],
        task: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a collaboration pattern.

        Args:
            pattern: Collaboration pattern to use
            agents: List of agents to coordinate
            task: Task description
            config: Pattern-specific configuration

        Returns:
            Synthesized result from all agents
        """
        config = config or {}

        if pattern == CollaborationPattern.SEQUENTIAL:
            return await self.sequential(agents, task, config)
        elif pattern == CollaborationPattern.PARALLEL:
            return await self.parallel(agents, task, config)
        elif pattern == CollaborationPattern.VOTE:
            return await self.vote(agents, task, config)
        elif pattern == CollaborationPattern.DEBATE:
            return await self.debate(agents, task, config)
        elif pattern == CollaborationPattern.SWARM:
            return await self.swarm(agents, task, config)
        elif pattern == CollaborationPattern.CONSENSUS:
            return await self.consensus(agents, task, config)
        else:
            raise ValueError(f"Unknown pattern: {pattern}")

    async def sequential(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sequential execution (pipeline).
        Output of agent N becomes input to agent N+1.
        """
        logger.info(f"Sequential execution with {len(agents)} agents")

        context = {"task": task}
        results = []

        for i, agent in enumerate(agents):
            step_task = f"Step {i+1}: {task}"
            if i > 0:
                step_task += f"\nPrevious result: {results[-1].get('result')}"

            result = await self._execute_agent(agent, step_task, context)
            results.append(result)

            # Update context with result
            context[f"step_{i}"] = result

        return {
            "pattern": "sequential",
            "results": results,
            "final_output": results[-1] if results else None
        }

    async def parallel(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parallel execution.
        All agents work independently and simultaneously.
        """
        logger.info(f"Parallel execution with {len(agents)} agents")

        # Execute all agents in parallel
        tasks = [self._execute_agent(agent, task, {}) for agent in agents]
        results = await asyncio.gather(*tasks)

        # Synthesize results
        synthesized = self.synthesizer.merge(results)

        return {
            "pattern": "parallel",
            "results": results,
            "synthesized": synthesized
        }

    async def vote(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Voting pattern.
        All agents vote, majority wins.
        """
        logger.info(f"Vote execution with {len(agents)} agents")

        # Get votes from all agents
        tasks = [self._execute_agent(agent, task, {}) for agent in agents]
        results = await asyncio.gather(*tasks)

        # Calculate weighted votes (weight by trust score)
        weights = [agent.trust_score for agent in agents]
        synthesized = self.synthesizer.vote(results, weights)

        return {
            "pattern": "vote",
            "results": results,
            "synthesized": synthesized
        }

    async def debate(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Debate pattern.
        Multiple rounds where agents see each other's responses.
        """
        rounds_count = config.get("rounds", 3)
        logger.info(f"Debate execution with {len(agents)} agents, {rounds_count} rounds")

        all_rounds = []
        context = {"task": task}

        for round_num in range(rounds_count):
            logger.info(f"Debate round {round_num + 1}/{rounds_count}")

            # Each agent responds seeing previous round results
            round_task = task
            if round_num > 0:
                round_task += f"\n\nPrevious responses:\n"
                for r in all_rounds[-1]:
                    round_task += f"- {r.get('agent')}: {r.get('result')}\n"

            tasks = [self._execute_agent(agent, round_task, context) for agent in agents]
            round_results = await asyncio.gather(*tasks)

            all_rounds.append(round_results)
            context[f"round_{round_num}"] = round_results

        # Determine winner based on final round
        synthesized = self.synthesizer.debate_winner(
            results=all_rounds[-1],
            rounds=all_rounds
        )

        return {
            "pattern": "debate",
            "rounds": all_rounds,
            "synthesized": synthesized
        }

    async def swarm(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Swarm intelligence pattern.
        Agents share partial solutions and converge.
        """
        iterations = config.get("iterations", 3)
        logger.info(f"Swarm execution with {len(agents)} agents, {iterations} iterations")

        shared_knowledge = []
        all_iterations = []

        for iteration in range(iterations):
            # Each agent works with shared knowledge
            context = {
                "task": task,
                "shared_knowledge": shared_knowledge
            }

            tasks = [self._execute_agent(agent, task, context) for agent in agents]
            results = await asyncio.gather(*tasks)

            # Update shared knowledge with best results
            shared_knowledge.extend([
                r.get("result") for r in results
                if r.get("confidence", 0) > 0.7
            ])

            all_iterations.append(results)

        # Final synthesis
        final_results = all_iterations[-1]
        synthesized = self.synthesizer.merge(final_results)

        return {
            "pattern": "swarm",
            "iterations": all_iterations,
            "synthesized": synthesized
        }

    async def consensus(
        self,
        agents: List[Agent],
        task: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consensus pattern.
        Byzantine-style agreement with threshold.
        """
        threshold = config.get("threshold", 0.66)
        max_rounds = config.get("max_rounds", 5)
        logger.info(f"Consensus execution with {len(agents)} agents, threshold={threshold}")

        all_rounds = []

        for round_num in range(max_rounds):
            # Execute all agents
            tasks = [self._execute_agent(agent, task, {"round": round_num}) for agent in agents]
            results = await asyncio.gather(*tasks)

            all_rounds.append(results)

            # Check for consensus
            consensus_result = self.synthesizer.consensus(results, threshold)

            if consensus_result["type"] == "consensus":
                return {
                    "pattern": "consensus",
                    "rounds": all_rounds,
                    "synthesized": consensus_result,
                    "converged": True
                }

        # No consensus reached within max rounds
        return {
            "pattern": "consensus",
            "rounds": all_rounds,
            "synthesized": self.synthesizer.vote(all_rounds[-1]),
            "converged": False
        }

    async def _execute_agent(
        self,
        agent: Agent,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single agent (stub implementation).

        In production, this would make HTTP calls to agent endpoints.
        """
        logger.info(f"Executing agent {agent.name}: {task[:100]}...")

        # Simulate agent execution
        await asyncio.sleep(0.1)  # Simulate network latency

        return {
            "agent": agent.name,
            "agent_id": agent.id,
            "task": task,
            "result": f"Result from {agent.name}",
            "confidence": 0.85,
            "duration": 0.1,
            "cost": agent.cost_per_request
        }


class CollaborationFactory:
    """Factory for creating collaboration instances"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = CollaborationEngine(db)

    async def create_collaboration(
        self,
        plan_id: str,
        step_id: str,
        pattern: CollaborationPattern,
        agents: List[Agent],
        task: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AgentCollaboration:
        """
        Create and execute a collaboration.

        Returns:
            AgentCollaboration instance with results
        """
        # Create collaboration record
        collaboration = AgentCollaboration(
            plan_id=plan_id,
            pattern=pattern,
            step_id=step_id,
            step_description=task,
            agent_ids=[agent.id for agent in agents],
            config=config or {},
            status=OrchestrationStatus.EXECUTING
        )
        self.db.add(collaboration)
        await self.db.flush()

        # Execute pattern
        start_time = datetime.utcnow()
        result = await self.engine.execute_pattern(pattern, agents, task, config)
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Store individual results
        if "results" in result:
            for agent_result in result["results"]:
                collab_result = CollaborationResult(
                    collaboration_id=collaboration.id,
                    agent_id=agent_result.get("agent_id"),
                    result_data=agent_result,
                    confidence=agent_result.get("confidence"),
                    duration=agent_result.get("duration", 0),
                    cost=agent_result.get("cost", 0)
                )
                self.db.add(collab_result)

        # Update collaboration
        collaboration.synthesized_result = result.get("synthesized", result)
        collaboration.individual_results = result.get("results", [])
        collaboration.status = OrchestrationStatus.COMPLETED
        collaboration.completed_at = datetime.utcnow()
        collaboration.duration = duration

        await self.db.commit()

        return collaboration
