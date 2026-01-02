# Gym Bro Tools Reference

## Contents
- Query Tools (5)
- Recommend Tools (6)
- Session Tools (1)
- Abs Tools (2)
- Adaptive Template Tools (1)

**Total**: 15 tools across 5 modules

---

## Query Tools

**File**: `/Users/franklindickinson/Projects/gym-bro/src/tools/query_tools.py` (253 LOC)

Used by: QueryAgent, ChatAgent

### 1. search_workouts
```python
@tool
def search_workouts(query: str, days: int = 30) -> list[dict]:
    """
    Search workout logs by keyword, exercise name, or workout type.

    Args:
        query: Search term (exercise name, workout type, or keyword)
        days: Number of days to search back (default 30)

    Returns:
        List of matching workout logs with date, type, and exercises
    """
```

**Example Usage**:
- `search_workouts("bench press", days=60)`
- `search_workouts("Push", days=14)`

---

### 2. get_exercise_history
```python
@tool
def get_exercise_history(exercise: str, days: int = 90) -> list[dict]:
    """
    Get weight and rep history for a specific exercise over time.

    Args:
        exercise: Name of the exercise (fuzzy matching supported)
        days: Number of days to look back (default 90)

    Returns:
        List of sessions with date, sets, weights, and reps
    """
```

**Output Format**:
```json
[
  {
    "date": "2024-12-15",
    "sets": [
      {"reps": 8, "weight_lbs": 135},
      {"reps": 7, "weight_lbs": 135}
    ]
  }
]
```

---

### 3. calculate_progression
```python
@tool
def calculate_progression(exercise: str) -> dict:
    """
    Calculate progression statistics for an exercise.

    Args:
        exercise: Name of the exercise

    Returns:
        Stats including first/current/max weight, trend, and average weekly increase
    """
```

**Output Format**:
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

### 4. compare_exercises
```python
@tool
def compare_exercises(exercise1: str, exercise2: str) -> dict:
    """
    Compare progression between two exercises.

    Args:
        exercise1: First exercise name
        exercise2: Second exercise name

    Returns:
        Side-by-side comparison of progression stats
    """
```

---

### 5. get_workout_count
```python
@tool
def get_workout_count(days: int = 30, workout_type: str | None = None) -> dict:
    """
    Count workouts in a time period, optionally filtered by type.

    Args:
        days: Number of days to look back
        workout_type: Optional filter (Push, Pull, Legs, Upper, Lower)

    Returns:
        Total count and breakdown by type
    """
```

---

## Recommend Tools

**File**: `/Users/franklindickinson/Projects/gym-bro/src/tools/recommend_tools.py` (430 LOC)

Used by: RecommendAgent, ChatAgent

### 1. get_weekly_split_status
```python
@tool
def get_weekly_split_status() -> dict:
    """
    Get current week's workout completion status by type.

    Returns:
        Dict with completed counts, targets, remaining, and next suggested workout
    """
```

**Output Format**:
```json
{
  "week_start": "2024-12-16",
  "completed": {"Push": 1, "Pull": 1},
  "targets": {"Push": 1, "Pull": 1, "Legs": 2, "Upper": 1, "Lower": 1},
  "remaining": {"Legs": 2, "Upper": 1, "Lower": 1},
  "next_suggested": "Legs",
  "days_left_in_week": 5,
  "supplementary": {"abs": {"count": 1, "target": 2, "can_do_today": true}}
}
```

---

### 2. suggest_next_workout
```python
@tool
def suggest_next_workout() -> dict:
    """
    Suggest next workout based on weekly split rotation and completion status.

    Includes "catch-up mode" detection if user is behind on targets.

    Returns:
        Suggested workout type with reasoning
    """
```

**Output Format**:
```json
{
  "suggested_type": "Legs",
  "reason": "Next in rotation, 0/2 legs workouts this week",
  "catch_up_mode": true,
  "catch_up_details": "Need 2 legs workouts with only 3 days left"
}
```

---

### 3. get_last_workout_by_type
```python
@tool
def get_last_workout_by_type(workout_type: str) -> dict:
    """
    Get the most recent workout of a specific type.

    Args:
        workout_type: Push, Pull, Legs, Upper, or Lower

    Returns:
        Last workout of that type with date and exercises
    """
```

---

### 4. check_muscle_balance
```python
@tool
def check_muscle_balance() -> dict:
    """
    Analyze if any muscle groups are under/over trained.

    Returns:
        Push/pull/legs ratio analysis with recommendations
    """
```

---

### 5. get_workout_template
```python
@tool
def get_workout_template(workout_type: str, adaptive: bool = True) -> dict:
    """
    Get workout template for a specific type.

    Args:
        workout_type: Push, Pull, Legs, Upper, Lower
        adaptive: If True, uses TemplateGenerator for personalized template

    Returns:
        Template with exercises, sets, reps, rest periods
    """
```

---

### 6. get_abs_status
```python
@tool
def get_abs_status() -> dict:
    """
    Get ab workout status for the current week.

    Returns:
        Count, target, spacing (can do today), on-track status
    """
```

---

## Session Tools

**File**: `/Users/franklindickinson/Projects/gym-bro/src/tools/session_tools.py` (146 LOC)

Used by: ChatAgent

### start_workout_session
```python
@tool
def start_workout_session(
    workout_type: str | None = None,
    equipment_unavailable: list[str] | None = None
) -> dict:
    """
    Start a new workout session with AI planning.

    Args:
        workout_type: Optional type (Push/Pull/Legs/Upper/Lower)
        equipment_unavailable: List of unavailable equipment

    Returns:
        Session ID and initial state
    """
```

**Triggers SessionGraph** (session_graph.py)

---

## Abs Tools

**File**: `/Users/franklindickinson/Projects/gym-bro/src/tools/abs_tools.py` (150 LOC)

### 1. get_abs_recommendation
```python
@tool
def get_abs_recommendation() -> dict:
    """
    Get abs workout recommendation based on spacing rules.

    Enforces:
    - Target: 2 ab workouts per week
    - Spacing: No consecutive day ab work

    Returns:
        Should do abs today, reason, exercises
    """
```

---

### 2. validate_abs_spacing
```python
@tool
def validate_abs_spacing(planned_date: str) -> dict:
    """
    Validate if abs workout can be scheduled on a specific date.

    Args:
        planned_date: Date in ISO format (YYYY-MM-DD)

    Returns:
        Valid (bool) and reason
    """
```

---

## Adaptive Template Tools

**File**: `/Users/franklindickinson/Projects/gym-bro/src/tools/adaptive_template_tools.py` (125 LOC)

### generate_adaptive_template
```python
@tool
def generate_adaptive_template(
    workout_type: str,
    equipment_unavailable: list[str] | None = None
) -> dict:
    """
    Generate adaptive workout template based on training history.

    Uses TemplateGenerator agent to create personalized template with:
    - Progressive overload weights
    - Equipment substitutions
    - Rep/set adjustments

    Args:
        workout_type: Push, Pull, Legs, Upper, Lower
        equipment_unavailable: Equipment to exclude

    Returns:
        Adaptive template with reasoning
    """
```

**Fallback**: Static template if insufficient history

---

## Tool Discovery Commands

```bash
# Find all @tool decorators
grep -n "@tool" src/tools/*.py

# Find tool by name
grep -n "def tool_name" src/tools/*.py

# List all tool exports
grep -n "TOOLS = \[" src/tools/*.py
```

---

## Integration Pattern

**Adding a New Tool:**

1. Create tool function in appropriate `src/tools/*.py` file
2. Use `@tool` decorator from `langchain_core.tools`
3. Add docstring with Args and Returns
4. Add to tool list export (e.g., `QUERY_TOOLS = [...]`)
5. Update agent to include tool in tool list
6. Update agent's system prompt to mention tool

See `creating-tools` skill for scaffolding.

---

## Tool Pattern Best Practices

From existing tools:

1. **Return Dicts** (not primitives) for extensibility
2. **Include Context** in return (echo inputs)
3. **Handle Edge Cases** gracefully
4. **Clear Docstrings** with Args/Returns
5. **Use Type Hints** for all parameters
6. **Fuzzy Matching** where appropriate (exercise names)
7. **Sensible Defaults** for optional parameters
