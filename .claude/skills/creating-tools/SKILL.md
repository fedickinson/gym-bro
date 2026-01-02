---
name: creating-tools
description: Generates new tools with @tool decorators, type hints, and proper integration. Use when adding capabilities to agents, creating data access functions, or extending agent toolsets.
---

# Tool Generator

## Quick Tool Creation Workflow

Copy this checklist:

```
Tool Creation:
- [ ] Step 1: Define tool requirements (name, purpose, params)
- [ ] Step 2: Choose tool module (query/recommend/session)
- [ ] Step 3: Generate tool function with @tool decorator
- [ ] Step 4: Add to tool list export
- [ ] Step 5: Update agent system prompt
- [ ] Step 6: Test tool
```

## Tool Template

```python
from langchain_core.tools import tool
from src.data import [relevant_data_functions]

@tool
def tool_name(param1: str, param2: int = 30) -> dict:
    """
    Brief description of what this tool does.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default 30)

    Returns:
        Dict with result data

    Example:
        >>> tool_name("bench press", days=60)
        {"exercise": "bench press", "data": [...]}
    """
    # Implementation
    result = perform_operation(param1, param2)

    # Always return dict for extensibility
    return {
        "param1": param1,  # Echo inputs for context
        "param2": param2,
        "result": result,
        "message": "Success"
    }
```

---

## Tool Modules

### Query Tools (`src/tools/query_tools.py`)

**Purpose**: Historical data access and analysis

**Existing Tools**:
- `search_workouts` - Find workouts by keyword
- `get_exercise_history` - Weight/rep progression
- `calculate_progression` - Stats and trends
- `compare_exercises` - Side-by-side comparison
- `get_workout_count` - Count by type/time

**Used by**: QueryAgent, ChatAgent

**Add new tool here if**: Answering questions about PAST workout data

---

### Recommend Tools (`src/tools/recommend_tools.py`)

**Purpose**: Workout planning and recommendations

**Existing Tools**:
- `get_weekly_split_status` - Week completion status
- `suggest_next_workout` - Smart recommendations
- `get_last_workout_by_type` - Most recent by type
- `check_muscle_balance` - Push/pull/legs ratios
- `get_workout_template` - Template retrieval
- `get_abs_status` - Ab workout tracking

**Used by**: RecommendAgent, ChatAgent

**Add new tool here if**: Planning FUTURE workouts or tracking splits

---

### Session Tools (`src/tools/session_tools.py`)

**Purpose**: Workout session management

**Existing Tools**:
- `start_workout_session` - Initiate planning session

**Used by**: ChatAgent

**Add new tool here if**: Managing active workout sessions

---

## Example: Create Estimated 1RM Tool

### Step 1: Requirements
- **Name**: `calculate_estimated_1rm`
- **Purpose**: Calculate estimated one-rep max from weight/reps
- **Parameters**: `weight_lbs` (float), `reps` (int)
- **Return**: `dict` with estimated_1rm, formula, confidence
- **Module**: query_tools.py (data analysis)

### Step 2: Generate Tool Function

```python
# Add to src/tools/query_tools.py

@tool
def calculate_estimated_1rm(weight_lbs: float, reps: int) -> dict:
    """
    Calculate estimated one-rep max using Epley formula.

    Formula: 1RM = weight × (1 + reps/30)

    Args:
        weight_lbs: Weight lifted in pounds
        reps: Number of reps completed (1-20 recommended)

    Returns:
        Dict with estimated_1rm, formula_used, confidence_level

    Example:
        >>> calculate_estimated_1rm(225, 5)
        {"estimated_1rm": 262.5, "formula_used": "Epley", ...}
    """
    if reps < 1:
        return {
            "error": "Reps must be at least 1",
            "estimated_1rm": None
        }

    if reps == 1:
        # Already a 1RM
        return {
            "estimated_1rm": weight_lbs,
            "formula_used": "actual",
            "confidence_level": "exact",
            "weight_lbs": weight_lbs,
            "reps": reps
        }

    # Epley formula
    estimated_1rm = round(weight_lbs * (1 + reps / 30), 1)

    # Confidence decreases with higher reps
    if reps <= 5:
        confidence = "high"
    elif reps <= 10:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "estimated_1rm": estimated_1rm,
        "formula_used": "Epley",
        "confidence_level": confidence,
        "weight_lbs": weight_lbs,
        "reps": reps,
        "note": "Formula: weight × (1 + reps/30)"
    }
```

### Step 3: Add to Tool List

```python
# At bottom of src/tools/query_tools.py

QUERY_TOOLS = [
    search_workouts,
    get_exercise_history,
    calculate_progression,
    compare_exercises,
    get_workout_count,
    calculate_estimated_1rm  # NEW TOOL
]
```

### Step 4: Update Agent System Prompt

```python
# In src/agents/query_agent.py

QUERY_AGENT_PROMPT = """You are a fitness data analyst...

Your tools:
- search_workouts: Find workouts by keyword
- get_exercise_history: Get weight/rep history
- calculate_progression: Calculate trends and PRs
- compare_exercises: Side-by-side comparison
- get_workout_count: Count workouts
- calculate_estimated_1rm: Calculate estimated 1RM from weight/reps  # NEW

...
"""
```

### Step 5: Test Tool

```python
# test_1rm_tool.py
from src.tools.query_tools import calculate_estimated_1rm

# Test 1: Normal case
result = calculate_estimated_1rm.invoke({"weight_lbs": 225, "reps": 5})
print(result)
# {"estimated_1rm": 262.5, "formula_used": "Epley", ...}

# Test 2: Edge case - 1 rep (already max)
result2 = calculate_estimated_1rm.invoke({"weight_lbs": 315, "reps": 1})
print(result2)
# {"estimated_1rm": 315.0, "formula_used": "actual", ...}

# Test 3: Error case
result3 = calculate_estimated_1rm.invoke({"weight_lbs": 135, "reps": 0})
print(result3)
# {"error": "Reps must be at least 1", ...}
```

---

## Tool Best Practices

### 1. Return Dicts (Not Primitives)

**Good**:
```python
return {"count": 5, "workouts": [...]}
```

**Bad**:
```python
return 5  # Hard to extend later
```

### 2. Echo Inputs in Output

**Good**:
```python
return {
    "exercise": exercise,  # Echo input
    "days": days,          # Echo input
    "history": [...]
}
```

**Why**: Helps agent track what it asked for

### 3. Handle Edge Cases Gracefully

```python
if not data:
    return {
        "exercise": exercise,
        "message": f"No data found for {exercise}",
        "history": []
    }
```

### 4. Use Clear Docstrings

Include:
- Brief description
- Args section with types
- Returns section with structure
- Example usage

### 5. Type Hints for All Parameters

```python
def tool_name(param1: str, param2: int = 30) -> dict:
    ...
```

---

## Common Tool Patterns

### Pattern 1: Data Query Tool

```python
@tool
def get_workout_by_id(workout_id: str) -> dict | None:
    """Get a specific workout by ID."""
    from src.data import get_log_by_id
    return get_log_by_id(workout_id)
```

---

### Pattern 2: Calculation Tool

```python
@tool
def calculate_volume(workout_id: str) -> dict:
    """Calculate total volume for a workout."""
    from src.data import get_log_by_id

    log = get_log_by_id(workout_id)
    if not log:
        return {"error": "Workout not found", "volume": 0}

    total_volume = 0
    for ex in log.get("exercises", []):
        for set_data in ex.get("sets", []):
            reps = set_data.get("reps", 0)
            weight = set_data.get("weight_lbs", 0)
            total_volume += reps * weight

    return {
        "workout_id": workout_id,
        "total_volume": total_volume,
        "unit": "lbs"
    }
```

---

### Pattern 3: Comparison Tool

```python
@tool
def compare_weeks(week1_start: str, week2_start: str) -> dict:
    """Compare workout volume between two weeks."""
    from src.data import get_logs_by_date_range
    from datetime import date, timedelta

    # Get week 1 logs
    w1_start = date.fromisoformat(week1_start)
    w1_end = w1_start + timedelta(days=6)
    w1_logs = get_logs_by_date_range(w1_start, w1_end)

    # Get week 2 logs
    w2_start = date.fromisoformat(week2_start)
    w2_end = w2_start + timedelta(days=6)
    w2_logs = get_logs_by_date_range(w2_start, w2_end)

    return {
        "week1": {
            "start": week1_start,
            "workout_count": len(w1_logs),
            "types": [log["type"] for log in w1_logs]
        },
        "week2": {
            "start": week2_start,
            "workout_count": len(w2_logs),
            "types": [log["type"] for log in w2_logs]
        }
    }
```

---

## Integration Checklist

When adding a new tool:

1. ✓ Add `@tool` decorator
2. ✓ Include complete docstring (Args, Returns, Example)
3. ✓ Use type hints
4. ✓ Return dict (not primitive)
5. ✓ Echo inputs in output
6. ✓ Handle edge cases
7. ✓ Add to tool list export
8. ✓ Update agent system prompt
9. ✓ Test tool independently
10. ✓ Test with agent

---

## Reference Files

- [TOOL-EXAMPLES.md](TOOL-EXAMPLES.md) - More examples from existing tools
- [TESTING.md](TESTING.md) - Testing patterns and validation

For exploring existing tools, use the `exploring-codebase` skill.
