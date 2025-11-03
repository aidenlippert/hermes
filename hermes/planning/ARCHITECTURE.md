# HTN Planning System Architecture
**Version**: 1.0
**Status**: Implementation Phase
**Owner**: Astraeus Core Team

## Overview

Production-grade Hierarchical Task Network (HTN) planning system combining LLM creativity with symbolic reasoning for reliable multi-agent task decomposition.

## Design Principles

1. **Performance First**: <500ms for simple plans, <2s for complex plans
2. **Reliability**: Idempotent, replayable, recoverable
3. **Observability**: Full OpenTelemetry tracing
4. **Testability**: >90% code coverage
5. **Type Safety**: Complete type hints with runtime validation

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: API Interface (FastAPI endpoints)        │
├─────────────────────────────────────────────────────┤
│  Layer 2: HTN Planning Orchestrator                │
│  - Plan coordination                                │
│  - Caching layer                                    │
│  - Performance monitoring                           │
├─────────────────────────────────────────────────────┤
│  Layer 3: Hybrid Planning Engine                   │
│  ┌─────────────────┬──────────────────────────────┐│
│  │ LLM Decomposer  │ Symbolic Validator          ││
│  │ (Gemini 2.0)    │ (HTN Core)                  ││
│  └─────────────────┴──────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│  Layer 4: Plan Persistence & Serialization         │
│  - JSON serialization                               │
│  - Plan versioning                                  │
│  - State recovery                                   │
├─────────────────────────────────────────────────────┤
│  Layer 5: Incremental Learning Module              │
│  - Plan pattern recognition                         │
│  - Performance optimization                         │
│  - Failure analysis                                 │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. HTN Planning Core (`htn_core.py`)

**Purpose**: Symbolic HTN planning engine

**Key Classes**:
- `HTNState`: Immutable world state representation
- `HTNTask`: Atomic or composite task definition
- `HTNMethod`: Task decomposition strategy
- `HTNOperator`: Primitive action with preconditions/effects
- `HTNDomain`: Collection of methods and operators
- `HTNPlanner`: Core planning algorithm

**Performance Targets**:
- Simple decomposition: <50ms
- Complex decomposition: <200ms
- Plan validation: <10ms

### 2. LLM Integration (`llm_planner.py`)

**Purpose**: Gemini 2.0 Flash integration for creative decomposition

**Key Classes**:
- `LLMPlanner`: Gemini API wrapper with retries
- `PromptTemplate`: Structured prompts for decomposition
- `LLMCache`: Response caching for common patterns

**Features**:
- Structured output (JSON mode)
- Retry logic with exponential backoff
- Token usage tracking
- Prompt versioning

### 3. Hybrid Orchestrator (`hybrid_planner.py`)

**Purpose**: Combines LLM and symbolic planning

**Workflow**:
```python
async def plan(user_intent, context):
    # 1. LLM generates high-level decomposition
    llm_plan = await llm_planner.decompose(user_intent)

    # 2. Validate with symbolic planner
    validated_plan = htn_core.validate(llm_plan, domain)

    # 3. If invalid, regenerate with constraints
    if not validated_plan.is_valid:
        llm_plan = await llm_planner.decompose(
            user_intent,
            constraints=validated_plan.violations
        )
        validated_plan = htn_core.validate(llm_plan, domain)

    # 4. Optimize plan
    optimized_plan = optimizer.optimize(validated_plan)

    # 5. Persist and return
    await persistence.save(optimized_plan)
    return optimized_plan
```

### 4. Plan Persistence (`plan_storage.py`)

**Purpose**: Reliable plan storage and recovery

**Storage Format**:
```json
{
  "plan_id": "uuid",
  "version": "1.0",
  "created_at": "2025-01-02T10:30:00Z",
  "user_intent": "Book flight to NYC",
  "tasks": [
    {
      "task_id": "t1",
      "type": "primitive",
      "operator": "search_flights",
      "parameters": {"destination": "NYC"},
      "preconditions": [],
      "effects": ["flights_found"]
    }
  ],
  "dependencies": [
    {"from": "t1", "to": "t2", "type": "sequential"}
  ],
  "metadata": {
    "complexity": 0.6,
    "estimated_duration": 4.2,
    "confidence": 0.95
  }
}
```

### 5. Incremental Learning (`learning.py`)

**Purpose**: Improve planning over time

**Learning Strategies**:
1. **Pattern Recognition**: Identify common task decompositions
2. **Performance Tracking**: Monitor success rates
3. **Failure Analysis**: Learn from execution failures
4. **Plan Optimization**: Improve based on execution metrics

## Data Models

```python
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class TaskType(str, Enum):
    PRIMITIVE = "primitive"
    COMPOSITE = "composite"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class HTNTask(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Human-readable task name")
    type: TaskType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    preconditions: List[str] = Field(default_factory=list)
    effects: List[str] = Field(default_factory=list)
    subtasks: Optional[List['HTNTask']] = None

    class Config:
        frozen = True  # Immutable

class HTNPlan(BaseModel):
    plan_id: str
    version: str = "1.0"
    created_at: datetime
    user_intent: str
    tasks: List[HTNTask]
    dependencies: List[Dict[str, str]]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_execution_graph(self) -> 'ExecutionGraph':
        """Convert to DAG for execution"""
        pass

    def validate(self) -> bool:
        """Validate plan consistency"""
        pass
```

## Testing Strategy

### Unit Tests (>90% coverage)
- `test_htn_core.py`: Core planning logic
- `test_llm_planner.py`: LLM integration (mocked)
- `test_hybrid_planner.py`: Orchestration logic
- `test_plan_storage.py`: Persistence layer
- `test_learning.py`: Learning algorithms

### Integration Tests
- `test_end_to_end.py`: Full planning pipeline
- `test_gemini_integration.py`: Real Gemini API calls
- `test_performance.py`: Performance benchmarks

### Performance Tests
```python
@pytest.mark.benchmark
def test_simple_plan_performance():
    """Target: <500ms for simple plans"""
    start = time.time()
    plan = planner.plan("Get weather for NYC")
    duration = time.time() - start
    assert duration < 0.5

@pytest.mark.benchmark
def test_complex_plan_performance():
    """Target: <2s for complex plans"""
    start = time.time()
    plan = planner.plan("Book flight to NYC, hotel for 3 nights, reserve restaurant")
    duration = time.time() - start
    assert duration < 2.0
```

## Observability

### OpenTelemetry Tracing
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def plan(user_intent):
    with tracer.start_as_current_span("htn_plan") as span:
        span.set_attribute("intent", user_intent)

        with tracer.start_as_current_span("llm_decompose"):
            llm_result = await llm.decompose(user_intent)
            span.set_attribute("llm_tokens", llm_result.token_count)

        with tracer.start_as_current_span("symbolic_validate"):
            validated = validate(llm_result)
            span.set_attribute("valid", validated.is_valid)

        return validated
```

### Metrics
- `htn_plan_duration_seconds{complexity="simple|complex"}`
- `htn_plan_success_rate{}`
- `htn_llm_token_usage{}`
- `htn_cache_hit_rate{}`
- `htn_plan_validation_failures{reason="..."}`

### Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "plan_created",
    plan_id=plan.plan_id,
    complexity=plan.metadata["complexity"],
    task_count=len(plan.tasks),
    duration_ms=duration * 1000
)
```

## Error Handling

### Error Types
1. **Planning Failures**: Invalid decomposition, unsolvable constraints
2. **LLM Failures**: API errors, timeouts, invalid responses
3. **Validation Failures**: Inconsistent plans, constraint violations
4. **Persistence Failures**: Database errors, serialization issues

### Recovery Strategies
```python
async def plan_with_retry(user_intent, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await plan(user_intent)
        except LLMError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning("llm_error_retry", attempt=attempt, error=str(e))
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except ValidationError as e:
            logger.error("validation_error", error=str(e))
            raise  # Don't retry validation errors
```

## Performance Optimization

### Caching Strategy
```python
# 1. LLM Response Cache (Redis)
@cache(ttl=3600)  # 1 hour
async def llm_decompose(user_intent: str) -> LLMResult:
    pass

# 2. Plan Template Cache
@cache(ttl=86400)  # 24 hours
def get_plan_template(intent_type: str) -> PlanTemplate:
    pass

# 3. Validation Rule Cache
@lru_cache(maxsize=1000)
def get_validation_rules(domain: str) -> List[Rule]:
    pass
```

### Batch Processing
```python
async def plan_batch(intents: List[str]) -> List[HTNPlan]:
    """Process multiple plans in parallel"""
    tasks = [plan(intent) for intent in intents]
    return await asyncio.gather(*tasks)
```

## Security Considerations

1. **Input Validation**: Strict validation of user intents
2. **LLM Output Sanitization**: Validate all LLM outputs
3. **Resource Limits**: Max task count, max depth, timeouts
4. **Rate Limiting**: Prevent abuse of planning API
5. **Audit Logging**: Track all planning requests

## Migration Strategy

### Phase 1: Parallel Run (Week 1-2)
- Deploy new HTN planner alongside existing planner
- Route 10% of traffic to new planner
- Compare results and performance

### Phase 2: Gradual Rollout (Week 3-4)
- Increase traffic to 50% if metrics are good
- Monitor for issues
- Fine-tune performance

### Phase 3: Full Migration (Week 5-6)
- Route 100% traffic to new planner
- Deprecate old planner
- Clean up old code

## Future Enhancements

1. **Multi-Agent Planning**: Coordinate plans across multiple agents
2. **Temporal Planning**: Handle time constraints explicitly
3. **Probabilistic Planning**: Handle uncertain outcomes
4. **Real-time Replanning**: Adapt plans during execution
5. **Formal Verification**: Prove plan correctness

## References

- [HTN Planning Research](../ASTRAEUS_SOTA_ARCHITECTURE.md#layer-2-orchestration--planning)
- [Sprint Roadmap](../SPRINT_ROADMAP.md#sprint-1-2-htn-planning--knowledge-foundation)
- [OpenTelemetry Python](https://opentelemetry-python.readthedocs.io/)
