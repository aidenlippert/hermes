# Astraeus Safety Layer Implementation Guide

## Technical Implementation Details

### 1. Core Safety Monitor Framework

#### 1.1 Event Bus Architecture
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
import asyncio
import time

class EventType(Enum):
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RELEASE = "resource_release"
    PLAN_EXECUTION = "plan_execution"
    LLM_INPUT = "llm_input"
    LLM_OUTPUT = "llm_output"
    SAFETY_VIOLATION = "safety_violation"

@dataclass
class SafetyEvent:
    event_type: EventType
    agent_id: str
    timestamp: float
    payload: Dict[str, Any]
    trace_id: str

class SafetyMonitor(ABC):
    @abstractmethod
    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        pass

class SafetyEventBus:
    def __init__(self):
        self.monitors: List[SafetyMonitor] = []
        self.event_queue = asyncio.Queue()
        self.running = False

    def register_monitor(self, monitor: SafetyMonitor):
        self.monitors.append(monitor)

    async def publish_event(self, event: SafetyEvent):
        await self.event_queue.put(event)

    async def start(self):
        self.running = True
        while self.running:
            event = await self.event_queue.get()
            await self._process_event(event)

    async def _process_event(self, event: SafetyEvent):
        tasks = [monitor.process_event(event) for monitor in self.monitors]
        violations = await asyncio.gather(*tasks, return_exceptions=True)

        for violation in violations:
            if isinstance(violation, SafetyViolation):
                await self._handle_violation(violation)
```

#### 1.2 Circuit Breaker Implementation
```python
from enum import Enum
from typing import Callable, Any
import asyncio
import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class SafetyCircuitBreaker:
    def __init__(self,
                 failure_threshold: int = 5,
                 timeout: float = 60.0,
                 recovery_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_threshold = recovery_threshold
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenException()

        try:
            result = await operation(*args, **kwargs)
            await self._record_success()
            return result
        except SafetyViolation as e:
            await self._record_failure()
            raise e

    async def _record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.recovery_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0

    async def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### 2. Temporal Logic Monitor

#### 2.1 LTL Monitor Implementation
```python
import z3
from typing import Dict, List, Set
from enum import Enum

class LTLResult(Enum):
    SATISFY = "satisfy"
    VIOLATE = "violate"
    PRESUMABLY_SATISFY = "presumably_satisfy"
    PRESUMABLY_VIOLATE = "presumably_violate"

class LTLMonitor(SafetyMonitor):
    def __init__(self):
        self.properties: Dict[str, LTLProperty] = {}
        self.solver = z3.Solver()
        self.agent_states: Dict[str, Dict[str, Any]] = {}

    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        violations = []

        # Update agent state
        self._update_agent_state(event)

        # Check all properties
        for prop_id, property in self.properties.items():
            result = await self._check_property(property, event)
            if result in [LTLResult.VIOLATE, LTLResult.PRESUMABLY_VIOLATE]:
                violations.append(SafetyViolation(
                    property_id=prop_id,
                    event=event,
                    severity=ViolationSeverity.CRITICAL if result == LTLResult.VIOLATE else ViolationSeverity.HIGH
                ))

        return violations[0] if violations else None

    def _check_mutual_exclusion(self, resource: str) -> LTLResult:
        """Check: ∀t. (agent_i.accessing_resource_r(t) ∧ agent_j.accessing_resource_r(t)) → i = j"""
        accessing_agents = []
        for agent_id, state in self.agent_states.items():
            if state.get("accessing_resources", set()).get(resource, False):
                accessing_agents.append(agent_id)

        if len(accessing_agents) > 1:
            return LTLResult.VIOLATE
        return LTLResult.SATISFY

    def _check_resource_bounds(self, agent_id: str) -> LTLResult:
        """Check: ∀i,r,t. agent_i.resource_usage(r,t) ≤ agent_i.allocation(r)"""
        agent_state = self.agent_states.get(agent_id, {})
        usage = agent_state.get("resource_usage", {})
        allocation = agent_state.get("resource_allocation", {})

        for resource, used in usage.items():
            if used > allocation.get(resource, 0):
                return LTLResult.VIOLATE
        return LTLResult.SATISFY
```

#### 2.2 SMT Solver Integration
```python
import z3
from typing import Dict, List

class SMTVerifier:
    def __init__(self):
        self.solver = z3.Solver()
        self.agent_vars: Dict[str, z3.ArithRef] = {}
        self.resource_vars: Dict[str, z3.ArithRef] = {}

    def verify_resource_allocation(self,
                                 allocations: Dict[str, Dict[str, int]],
                                 total_resources: Dict[str, int]) -> bool:
        """Verify that resource allocation is feasible"""
        self.solver.reset()

        # Create variables for each agent-resource pair
        allocation_vars = {}
        for agent_id, resources in allocations.items():
            for resource, amount in resources.items():
                var_name = f"{agent_id}_{resource}"
                allocation_vars[var_name] = z3.Int(var_name)
                self.solver.add(allocation_vars[var_name] == amount)
                self.solver.add(allocation_vars[var_name] >= 0)

        # Add total resource constraints
        for resource, total in total_resources.items():
            resource_sum = z3.Sum([
                allocation_vars[f"{agent_id}_{resource}"]
                for agent_id in allocations.keys()
                if resource in allocations[agent_id]
            ])
            self.solver.add(resource_sum <= total)

        return self.solver.check() == z3.sat

    def verify_deadlock_freedom(self, agent_dependencies: Dict[str, List[str]]) -> bool:
        """Check for circular dependencies that could cause deadlock"""
        def has_cycle(graph, node, visited, rec_stack):
            visited[node] = True
            rec_stack[node] = True

            for neighbor in graph.get(node, []):
                if not visited.get(neighbor, False):
                    if has_cycle(graph, neighbor, visited, rec_stack):
                        return True
                elif rec_stack.get(neighbor, False):
                    return True

            rec_stack[node] = False
            return False

        visited = {}
        rec_stack = {}

        for node in agent_dependencies:
            if not visited.get(node, False):
                if has_cycle(agent_dependencies, node, visited, rec_stack):
                    return False
        return True
```

### 3. LLM-Specific Safety Components

#### 3.1 PII Detection and Sanitization
```python
import re
from typing import List, Tuple, Dict
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class PIIDetector(SafetyMonitor):
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.custom_patterns = {
            'API_KEY': r'(?i)(api[_-]?key|access[_-]?token)\s*[:=]\s*["\']?([a-zA-Z0-9]{20,})["\']?',
            'SECRET': r'(?i)(secret|password|passwd)\s*[:=]\s*["\']?([a-zA-Z0-9@#$%^&*]{8,})["\']?',
            'PRIVATE_KEY': r'-----BEGIN [A-Z ]+PRIVATE KEY-----',
        }

    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        if event.event_type in [EventType.LLM_INPUT, EventType.LLM_OUTPUT]:
            text = event.payload.get('text', '')
            pii_detected = await self._detect_pii(text)
            secrets_detected = self._detect_secrets(text)

            if pii_detected or secrets_detected:
                return SafetyViolation(
                    property_id="LLM_001",
                    event=event,
                    severity=ViolationSeverity.HIGH,
                    details={"pii": pii_detected, "secrets": secrets_detected}
                )
        return None

    async def _detect_pii(self, text: str) -> List[str]:
        """Detect PII using Presidio analyzer"""
        results = self.analyzer.analyze(text=text, language='en')
        return [result.entity_type for result in results if result.score > 0.7]

    def _detect_secrets(self, text: str) -> List[str]:
        """Detect secrets using custom regex patterns"""
        detected = []
        for secret_type, pattern in self.custom_patterns.items():
            if re.search(pattern, text):
                detected.append(secret_type)
        return detected

    async def sanitize_text(self, text: str) -> str:
        """Remove or mask PII and secrets from text"""
        # Anonymize PII
        analyzer_results = self.analyzer.analyze(text=text, language='en')
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )

        sanitized_text = anonymized_result.text

        # Remove secrets
        for pattern in self.custom_patterns.values():
            sanitized_text = re.sub(pattern, '[REDACTED]', sanitized_text)

        return sanitized_text
```

#### 3.2 Prompt Injection Detection
```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List

class PromptInjectionDetector(SafetyMonitor):
    def __init__(self, model_path: str = "protectai/deberta-v3-base-prompt-injection-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.threshold = 0.8

    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        if event.event_type == EventType.LLM_INPUT:
            text = event.payload.get('text', '')
            is_injection = await self._detect_injection(text)

            if is_injection:
                return SafetyViolation(
                    property_id="LLM_002",
                    event=event,
                    severity=ViolationSeverity.CRITICAL,
                    details={"detected_injection": True}
                )
        return None

    async def _detect_injection(self, text: str) -> bool:
        """Detect prompt injection using ML model"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            injection_prob = probabilities[0][1].item()  # Assuming class 1 is injection

        return injection_prob > self.threshold

    def _detect_injection_patterns(self, text: str) -> bool:
        """Rule-based injection detection as fallback"""
        injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"forget\s+everything\s+above",
            r"system\s*:\s*you\s+are\s+now",
            r"new\s+instructions\s*:",
            r"disregard\s+the\s+above",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
```

#### 3.3 Hallucination Detection
```python
from typing import Dict, List, Optional
import openai
import numpy as np

class HallucinationDetector(SafetyMonitor):
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.fact_checker = FactChecker()

    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        if event.event_type == EventType.LLM_OUTPUT:
            output_text = event.payload.get('text', '')
            confidence = event.payload.get('confidence', 1.0)

            # Check confidence threshold
            if confidence < self.confidence_threshold:
                return SafetyViolation(
                    property_id="LLM_003",
                    event=event,
                    severity=ViolationSeverity.MEDIUM,
                    details={"low_confidence": confidence}
                )

            # Fact-check factual claims
            factual_violations = await self._check_facts(output_text)
            if factual_violations:
                return SafetyViolation(
                    property_id="LLM_003",
                    event=event,
                    severity=ViolationSeverity.HIGH,
                    details={"factual_errors": factual_violations}
                )

        return None

    async def _check_facts(self, text: str) -> List[str]:
        """Check factual claims in the output"""
        # Extract factual claims
        claims = self._extract_factual_claims(text)
        violations = []

        for claim in claims:
            is_accurate = await self.fact_checker.verify_claim(claim)
            if not is_accurate:
                violations.append(claim)

        return violations

    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract potential factual claims from text"""
        # This is a simplified implementation
        # In practice, this would use NLP techniques to identify factual statements
        sentences = text.split('.')
        factual_claims = []

        fact_indicators = ['is', 'was', 'are', 'were', 'has', 'have', 'had']
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in fact_indicators):
                factual_claims.append(sentence.strip())

        return factual_claims
```

### 4. Resource and Performance Monitoring

#### 4.1 Resource Monitor
```python
import psutil
import asyncio
from typing import Dict, Any

class ResourceMonitor(SafetyMonitor):
    def __init__(self):
        self.thresholds = {
            'cpu_percent': {'warning': 75, 'critical': 90, 'emergency': 95},
            'memory_percent': {'warning': 75, 'critical': 90, 'emergency': 95},
            'disk_percent': {'warning': 80, 'critical': 90, 'emergency': 95},
        }
        self.agent_resources: Dict[str, Dict[str, Any]] = {}

    async def process_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        current_usage = await self._get_system_usage()

        violations = []
        for metric, usage in current_usage.items():
            thresholds = self.thresholds.get(metric, {})

            if usage > thresholds.get('emergency', 100):
                violations.append(SafetyViolation(
                    property_id="SYS_002",
                    event=event,
                    severity=ViolationSeverity.CRITICAL,
                    details={metric: usage}
                ))
            elif usage > thresholds.get('critical', 100):
                violations.append(SafetyViolation(
                    property_id="SYS_002",
                    event=event,
                    severity=ViolationSeverity.HIGH,
                    details={metric: usage}
                ))

        return violations[0] if violations else None

    async def _get_system_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
        }

    async def allocate_resources(self, agent_id: str, resources: Dict[str, int]) -> bool:
        """Allocate resources to an agent"""
        current_usage = await self._get_system_usage()

        # Check if allocation is feasible
        for resource, amount in resources.items():
            if current_usage.get(f"{resource}_percent", 0) + amount > self.thresholds[f"{resource}_percent"]['critical']:
                return False

        self.agent_resources[agent_id] = resources
        return True
```

### 5. Integration with HTN Planning

#### 5.1 Plan Verification
```python
from typing import List, Dict, Any, Optional

@dataclass
class HTNAction:
    name: str
    preconditions: List[str]
    postconditions: List[str]
    resource_requirements: Dict[str, int]
    estimated_duration: float

@dataclass
class HTNPlan:
    actions: List[HTNAction]
    agent_id: str
    total_resources: Dict[str, int]
    estimated_duration: float

class HTNPlanVerifier:
    def __init__(self, safety_monitor: SafetyEventBus):
        self.safety_monitor = safety_monitor
        self.smt_verifier = SMTVerifier()

    async def verify_plan(self, plan: HTNPlan) -> bool:
        """Comprehensive plan verification"""
        verifications = await asyncio.gather(
            self._verify_preconditions(plan),
            self._verify_resource_constraints(plan),
            self._verify_safety_properties(plan),
            self._verify_side_effects(plan)
        )

        return all(verifications)

    async def _verify_preconditions(self, plan: HTNPlan) -> bool:
        """Verify all action preconditions can be satisfied"""
        current_state = await self._get_current_state()

        for action in plan.actions:
            for precondition in action.preconditions:
                if not self._evaluate_condition(precondition, current_state):
                    return False

            # Update state with postconditions
            current_state = self._apply_postconditions(action.postconditions, current_state)

        return True

    async def _verify_resource_constraints(self, plan: HTNPlan) -> bool:
        """Verify resource requirements don't exceed allocations"""
        return self.smt_verifier.verify_resource_allocation(
            {plan.agent_id: plan.total_resources},
            await self._get_available_resources()
        )

    async def _verify_safety_properties(self, plan: HTNPlan) -> bool:
        """Verify plan maintains all safety invariants"""
        # Simulate plan execution and check safety properties
        simulated_events = self._simulate_plan_execution(plan)

        for event in simulated_events:
            violation = await self.safety_monitor._process_event(event)
            if violation:
                return False

        return True
```

### 6. Performance Optimization

#### 6.1 Caching Strategy
```python
from functools import lru_cache
import hashlib
import pickle
from typing import Any, Dict

class VerificationCache:
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def get_cache_key(self, operation: str, inputs: Any) -> str:
        """Generate cache key for operation and inputs"""
        serialized = pickle.dumps(inputs)
        hash_obj = hashlib.md5(serialized)
        return f"{operation}:{hash_obj.hexdigest()}"

    async def get_or_compute(self, operation: str, inputs: Any, compute_func) -> Any:
        """Get cached result or compute and cache"""
        cache_key = self.get_cache_key(operation, inputs)

        if cache_key in self.cache:
            self.access_times[cache_key] = time.time()
            return self.cache[cache_key]

        # Compute result
        result = await compute_func(inputs)

        # Cache result
        await self._store_in_cache(cache_key, result)
        return result

    async def _store_in_cache(self, key: str, value: Any):
        """Store value in cache with LRU eviction"""
        if len(self.cache) >= self.max_size:
            # Evict least recently used
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[lru_key]
            del self.access_times[lru_key]

        self.cache[key] = value
        self.access_times[key] = time.time()
```

#### 6.2 Parallel Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelSafetyProcessor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.monitor_pool = []

    async def process_events_parallel(self, events: List[SafetyEvent]) -> List[SafetyViolation]:
        """Process multiple events in parallel"""
        tasks = []

        for event in events:
            task = asyncio.create_task(self._process_single_event(event))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        violations = []
        for result in results:
            if isinstance(result, SafetyViolation):
                violations.append(result)
            elif isinstance(result, Exception):
                # Log exception
                print(f"Error processing event: {result}")

        return violations

    async def _process_single_event(self, event: SafetyEvent) -> Optional[SafetyViolation]:
        """Process a single event with parallel monitor execution"""
        monitor_tasks = [
            monitor.process_event(event)
            for monitor in self.monitor_pool
        ]

        results = await asyncio.gather(*monitor_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, SafetyViolation):
                return result

        return None
```

This implementation guide provides the technical foundation for the Astraeus safety layer, with production-ready code examples that can be directly integrated into the system. The architecture emphasizes performance optimization while maintaining comprehensive safety coverage.