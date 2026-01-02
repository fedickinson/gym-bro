---
name: testing-agents
description: Tests agent responses and LangGraph workflows without running Streamlit. Use when validating agents, debugging workflows, or testing with sample inputs before deployment.
---

# Agent & Workflow Tester

## Quick Test Workflow

Copy this checklist:

```
Testing Progress:
- [ ] Step 1: Select test target (orchestrator, agent, tool, workflow)
- [ ] Step 2: Prepare test input
- [ ] Step 3: Execute test
- [ ] Step 4: Analyze output
- [ ] Step 5: Iterate if needed
```

## Test Target Selection

### 1. Test Full Orchestrator
Tests complete routing flow: input → classification → handler → response

```python
# Create test file: test_orchestrator.py
from src.agents.main import GymBroOrchestrator
from dotenv import load_dotenv

load_dotenv()

orchestrator = GymBroOrchestrator()
response, metadata = orchestrator.process_message("What did I bench last week?")

print(f"Intent: {metadata.get('intent')}")
print(f"Handler: {metadata.get('handler')}")
print(f"Response: {response}")
```

**Run**: `python test_orchestrator.py`

---

### 2. Test Specific Agent

**QueryAgent Example:**
```python
# test_query_agent.py
from src.agents.query_agent import QueryAgent
from dotenv import load_dotenv

load_dotenv()

agent = QueryAgent()
response = agent.query("Show me my bench press progression")

print(response)
```

**RecommendAgent Example:**
```python
# test_recommend_agent.py
from src.agents.recommend_agent import RecommendAgent
from dotenv import load_dotenv

load_dotenv()

agent = RecommendAgent()
response = agent.recommend("What should I do today?")

print(response)
```

---

### 3. Test Individual Tool

```python
# test_tool.py
from src.tools.query_tools import calculate_progression

result = calculate_progression.invoke({"exercise": "Bench Press"})
print(result)
```

**No .env needed** - tools access data directly

---

### 4. Test LangGraph Workflow

**Session Graph Example:**
```python
# test_session_graph.py
from src.agents.session_graph import initialize_planning_session
from dotenv import load_dotenv

load_dotenv()

# Initialize session with constraints
state = initialize_planning_session()
state['equipment_unavailable'] = ['barbell']

# Test initialization node
from src.agents.session_graph import initialize_planning
result = initialize_planning(state)

print("Suggested Type:", result['suggested_type'])
print("Template:", result['planned_template']['name'])
print("Adaptations:", result['planned_template'].get('adaptations', []))
```

---

## Output Analysis

### Successful Test Output

**Orchestrator**:
```
Intent: query
Handler: QueryAgent
Response: Based on your workout history, you benched 135 lbs for 3 sets of 8 reps on December 15th...
```

**Agent with Tools**:
```
> Entering new AgentExecutor chain...
Action: search_workouts
Action Input: {"query": "bench press", "days": 7}
Observation: [{"date": "2024-12-15", "type": "Push", ...}]
Thought: I found the bench press workout...
Final Answer: You benched 135 lbs last week...
> Finished chain.
```

**Tool**:
```json
{
  "exercise": "Bench Press",
  "trend": "increasing",
  "first_weight": 115.0,
  "current_weight": 135.0,
  "max_weight": 135.0,
  "total_sessions": 12,
  "avg_weekly_increase": 2.5
}
```

---

### Error Diagnosis

**Common Issues:**

1. **"ANTHROPIC_API_KEY not found"**
   - Check `.env` file exists
   - Verify `ANTHROPIC_API_KEY=sk-ant-...` is set
   - Run `load_dotenv()` before agent initialization

2. **"Tool not found"**
   - Verify tool is in agent's tool list
   - Check import statement
   - Ensure tool is exported in `QUERY_TOOLS` or `RECOMMEND_TOOLS`

3. **"No data found for exercise"**
   - Check exercise name spelling
   - Try fuzzy match: "bench" instead of "Bench Press"
   - Verify workout_logs.json has data

4. **LangGraph state errors**
   - Check required state fields
   - Verify state type matches graph definition
   - Review state transitions in graph

---

## Test Examples

See [TEST-EXAMPLES.md](TEST-EXAMPLES.md) for common scenarios:
- Testing intent routing
- Testing with equipment constraints
- Testing catch-up mode
- Testing deviation detection

See [TRACING.md](TRACING.md) for interpreting execution traces

---

## Performance Metrics

Track these for optimization:

```python
import time

start = time.time()
response = orchestrator.process_message("What did I bench?")
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
```

**Benchmarks** (approximate):
- Tool execution: 0.1-0.5s
- Simple agent: 1-3s
- Complex agent: 3-7s
- LangGraph workflow: 2-5s per node

---

## Validation Loops

**Pattern**: Test → Validate → Fix → Repeat

```python
# test_with_validation.py
def test_progression_calculation():
    """Test progression calculation for bench press."""
    from src.tools.query_tools import calculate_progression

    result = calculate_progression.invoke({"exercise": "Bench Press"})

    # Validation checks
    assert result["trend"] in ["increasing", "stable", "decreasing", "insufficient_data"]
    assert result["total_sessions"] >= 0
    if result["trend"] != "insufficient_data":
        assert result["current_weight"] is not None

    print("✓ Progression calculation validated")
    return result

# Run test
test_progression_calculation()
```

---

## Multi-Turn Conversation Testing

```python
# test_conversation.py
orchestrator = GymBroOrchestrator()

# Turn 1
response1, metadata1 = orchestrator.process_message("I need a workout")
print(f"Turn 1: {response1}\n")

# Turn 2 (with history)
chat_history = [
    {"role": "user", "content": "I need a workout"},
    {"role": "assistant", "content": response1}
]
response2, metadata2 = orchestrator.process_message(
    "I don't have a barbell",
    chat_history=chat_history
)
print(f"Turn 2: {response2}\n")
```

---

## Integration with CI/CD

**Create test suite**: `tests/test_agents.py`

```python
import pytest
from src.agents.query_agent import QueryAgent

@pytest.fixture
def query_agent():
    return QueryAgent()

def test_search_workouts(query_agent):
    response = query_agent.query("Show workouts from last week")
    assert "workout" in response.lower()

def test_exercise_history(query_agent):
    response = query_agent.query("Bench press history")
    # Check response contains relevant data
    assert any(word in response.lower() for word in ["bench", "press", "weight"])
```

**Run**: `pytest tests/test_agents.py`

---

## Quick Commands

```bash
# Test orchestrator
python -c "from src.agents.main import GymBroOrchestrator; from dotenv import load_dotenv; load_dotenv(); print(GymBroOrchestrator().process_message('What did I bench?'))"

# Test specific tool
python -c "from src.tools.query_tools import calculate_progression; print(calculate_progression.invoke({'exercise': 'Bench Press'}))"

# Test data access
python -c "from src.data import get_all_logs; print(f'Total logs: {len(get_all_logs())}')"
```

---

For detailed examples and tracing guides:
- [TEST-EXAMPLES.md](TEST-EXAMPLES.md) - Common test scenarios
- [TRACING.md](TRACING.md) - Interpreting agent execution traces
