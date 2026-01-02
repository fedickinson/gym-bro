# Tool Testing Patterns

## Basic Tool Test

```python
# test_my_tool.py
from src.tools.query_tools import my_new_tool

# Test with valid input
result = my_new_tool.invoke({"param1": "value1", "param2": 30})

print("Result:", result)
assert "expected_key" in result
assert result["param1"] == "value1"  # Echo check
```

---

## Test Checklist

```
Tool Testing:
- [ ] Test with valid inputs
- [ ] Test with edge cases (empty, null, extreme values)
- [ ] Test error handling
- [ ] Verify output structure (dict with expected keys)
- [ ] Check input echoing
- [ ] Validate type hints match actual types
- [ ] Test with agent (integration test)
```

---

## Pattern 1: Data Query Tool Tests

```python
def test_search_workouts():
    """Test search_workouts tool."""
    from src.tools.query_tools import search_workouts

    # Test 1: Search by exercise
    result = search_workouts.invoke({"query": "bench press", "days": 30})
    assert isinstance(result, list)
    for log in result:
        assert "date" in log
        assert "type" in log

    # Test 2: Search by type
    result2 = search_workouts.invoke({"query": "Push", "days": 7})
    assert isinstance(result2, list)

    # Test 3: No results
    result3 = search_workouts.invoke({"query": "nonexistent_exercise", "days": 30})
    assert result3 == []  # Should return empty list, not error
```

---

## Pattern 2: Calculation Tool Tests

```python
def test_calculate_estimated_1rm():
    """Test 1RM calculation tool."""
    from src.tools.query_tools import calculate_estimated_1rm

    # Test 1: Normal case
    result = calculate_estimated_1rm.invoke({"weight_lbs": 225, "reps": 5})
    assert result["estimated_1rm"] == 262.5
    assert result["confidence_level"] == "high"
    assert result["weight_lbs"] == 225  # Echo check
    assert result["reps"] == 5

    # Test 2: Already 1RM (1 rep)
    result2 = calculate_estimated_1rm.invoke({"weight_lbs": 315, "reps": 1})
    assert result2["estimated_1rm"] == 315.0
    assert result2["formula_used"] == "actual"

    # Test 3: High reps (lower confidence)
    result3 = calculate_estimated_1rm.invoke({"weight_lbs": 135, "reps": 15})
    assert result3["confidence_level"] == "low"

    # Test 4: Error case
    result4 = calculate_estimated_1rm.invoke({"weight_lbs": 135, "reps": 0})
    assert "error" in result4
```

---

## Pattern 3: Aggregation Tool Tests

```python
def test_get_weekly_split_status():
    """Test weekly split status tool."""
    from src.tools.recommend_tools import get_weekly_split_status

    result = get_weekly_split_status.invoke({})

    # Check structure
    assert "week_start" in result
    assert "completed" in result
    assert "targets" in result
    assert "remaining" in result
    assert "days_left_in_week" in result

    # Check types
    assert isinstance(result["completed"], dict)
    assert isinstance(result["targets"], dict)
    assert isinstance(result["remaining"], dict)

    # Check logic
    for workout_type, target in result["targets"].items():
        completed = result["completed"].get(workout_type, 0)
        remaining = result["remaining"].get(workout_type, 0)
        assert completed + remaining == target  # Math should work out
```

---

## Edge Case Testing

```python
def test_edge_cases():
    """Test tool with edge cases."""
    from src.tools.query_tools import get_exercise_history

    # Test 1: Empty exercise name
    result1 = get_exercise_history.invoke({"exercise": "", "days": 30})
    assert result1 == []  # Graceful handling

    # Test 2: Negative days
    try:
        result2 = get_exercise_history.invoke({"exercise": "bench", "days": -1})
        # Should either handle gracefully or raise clear error
    except ValueError as e:
        assert "days" in str(e).lower()

    # Test 3: Very large days value
    result3 = get_exercise_history.invoke({"exercise": "bench", "days": 10000})
    assert isinstance(result3, list)  # Should still work

    # Test 4: Special characters in exercise name
    result4 = get_exercise_history.invoke({"exercise": "bench@#$%", "days": 30})
    assert result4 == []  # No match is fine
```

---

## Integration Testing with Agent

```python
def test_tool_with_agent():
    """Test tool works correctly when used by agent."""
    from src.agents.query_agent import QueryAgent
    from dotenv import load_dotenv

    load_dotenv()
    agent = QueryAgent()

    # Ask question that should trigger the tool
    response = agent.query("Calculate my estimated 1RM if I can bench 225 for 5 reps")

    # Verify agent used tool and got correct answer
    assert "262" in response or "263" in response  # Should mention 262.5
    assert "1rm" in response.lower() or "max" in response.lower()
```

---

## Performance Testing

```python
import time

def test_tool_performance():
    """Test tool executes within acceptable time."""
    from src.tools.query_tools import calculate_progression

    start = time.time()
    result = calculate_progression.invoke({"exercise": "bench press"})
    elapsed = time.time() - start

    assert elapsed < 1.0  # Should complete in under 1 second
    print(f"Performance: {elapsed*1000:.1f}ms")
```

---

## Validation Testing

```python
def test_tool_output_schema():
    """Test tool returns expected structure."""
    from src.tools.query_tools import calculate_progression

    result = calculate_progression.invoke({"exercise": "bench press"})

    # Check all expected keys are present
    expected_keys = [
        "exercise",
        "trend",
        "first_weight",
        "current_weight",
        "max_weight",
        "total_sessions",
        "avg_weekly_increase"
    ]

    for key in expected_keys:
        assert key in result, f"Missing key: {key}"

    # Check value types
    assert isinstance(result["exercise"], str)
    assert isinstance(result["trend"], str)
    assert result["trend"] in ["increasing", "decreasing", "stable", "insufficient_data"]
    assert isinstance(result["total_sessions"], int)
```

---

## Pytest Integration

```python
# tests/test_tools.py
import pytest
from src.tools.query_tools import (
    search_workouts,
    get_exercise_history,
    calculate_progression,
    calculate_estimated_1rm
)

class TestQueryTools:
    """Test suite for query tools."""

    def test_search_workouts_valid_input(self):
        result = search_workouts.invoke({"query": "bench", "days": 30})
        assert isinstance(result, list)

    def test_search_workouts_no_results(self):
        result = search_workouts.invoke({"query": "xyz123", "days": 30})
        assert result == []

    def test_calculate_1rm_normal(self):
        result = calculate_estimated_1rm.invoke({"weight_lbs": 225, "reps": 5})
        assert result["estimated_1rm"] == 262.5

    def test_calculate_1rm_error(self):
        result = calculate_estimated_1rm.invoke({"weight_lbs": 135, "reps": 0})
        assert "error" in result

# Run: pytest tests/test_tools.py
```

---

## Validation Loop Pattern

```python
def test_tool_with_validation_loop():
    """Test tool with iterative validation."""
    from src.tools.recommend_tools import suggest_next_workout

    for i in range(3):  # Run 3 times
        result = suggest_next_workout.invoke({})

        # Validate structure every time
        assert "suggested_type" in result
        assert "reason" in result
        assert result["suggested_type"] in ["Push", "Pull", "Legs", "Upper", "Lower"]

        print(f"Iteration {i+1}: {result['suggested_type']}")
```

---

## Mock Data Testing

```python
def test_tool_with_mock_data():
    """Test tool with controlled mock data."""
    from src.tools.query_tools import calculate_progression
    from unittest.mock import patch

    # Mock the data layer
    mock_history = [
        {"date": "2024-12-01", "sets": [{"weight_lbs": 115}]},
        {"date": "2024-12-08", "sets": [{"weight_lbs": 125}]},
        {"date": "2024-12-15", "sets": [{"weight_lbs": 135}]},
    ]

    with patch('src.tools.query_tools._get_exercise_history', return_value=mock_history):
        result = calculate_progression.invoke({"exercise": "bench press"})

        assert result["first_weight"] == 115
        assert result["current_weight"] == 135
        assert result["trend"] == "increasing"
```

---

See [TOOL-EXAMPLES.md](TOOL-EXAMPLES.md) for more tool patterns.
