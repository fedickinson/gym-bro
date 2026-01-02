# Tool Examples from Existing Code

## Example 1: search_workouts (Query Tool)

**Location**: `/Users/franklindickinson/Projects/gym-bro/src/tools/query_tools.py:19`

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
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    logs = get_logs_by_date_range(start_date, end_date)
    query_lower = query.lower()

    results = []
    for log in logs:
        # Check workout type
        if query_lower in (log.get("type") or "").lower():
            results.append(_summarize_log(log))
            continue

        # Check exercise names
        for ex in log.get("exercises", []):
            if query_lower in (ex.get("name") or "").lower():
                results.append(_summarize_log(log))
                break

        # Check notes
        if query_lower in (log.get("notes") or "").lower():
            results.append(_summarize_log(log))

    return results
```

**Key Patterns**:
- Uses data layer (`get_logs_by_date_range`)
- Fuzzy matching (lowercase comparison)
- Multiple search criteria (type, exercise, notes)
- Helper function (`_summarize_log`) for clean output

---

## Example 2: get_weekly_split_status (Recommend Tool)

**Location**: `/Users/franklindickinson/Projects/gym-bro/src/tools/recommend_tools.py:23`

```python
@tool
def get_weekly_split_status() -> dict:
    """
    Get current week's workout completion status by type.

    Returns:
        Dict with completed counts, targets, remaining, and next suggested workout
    """
    split = get_weekly_split()
    config = split.get("config", {})
    current = split.get("current_week", {})

    # Get this week's date range
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday

    # Check if we need to reset the week
    stored_start = current.get("start_date")
    if stored_start:
        stored_start_date = date.fromisoformat(stored_start)
        if stored_start_date < week_start:
            # New week - reset
            current = {
                "start_date": week_start.isoformat(),
                "completed": {},
                "next_in_rotation": config.get("rotation", ["Push"])[0]
            }
            update_weekly_split({"config": config, "current_week": current})

    # Get workouts from this week
    logs = get_logs_by_date_range(week_start, today)

    # Count by type
    completed = {}
    for log in logs:
        t = log.get("type", "Other")
        if t in config.get("types", []):
            completed[t] = completed.get(t, 0) + 1

    # Calculate remaining
    targets = config.get("weekly_targets", {})
    remaining = {}
    for t, target in targets.items():
        done = completed.get(t, 0)
        remaining[t] = max(0, target - done)

    # [... more logic ...]

    return {
        "week_start": week_start.isoformat(),
        "completed": completed,
        "targets": targets,
        "remaining": remaining,
        "next_suggested": next_suggested,
        "days_left_in_week": days_left,
        "summary": _generate_split_summary(completed, targets, remaining)
    }
```

**Key Patterns**:
- Auto-reset logic (week boundary detection)
- Rich return dict with multiple data points
- Calculation and aggregation
- Helper function for summary

---

## Example 3: calculate_progression (Analysis Tool)

**Location**: `/Users/franklindickinson/Projects/gym-bro/src/tools/query_tools.py:73`

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
    history = _get_exercise_history(exercise, days=180)

    if not history:
        return {
            "exercise": exercise,
            "trend": "insufficient_data",
            "total_sessions": 0,
            "message": f"No data found for {exercise}"
        }

    weights = []
    for session in history:
        for set_data in session.get("sets", []):
            if set_data.get("weight_lbs"):
                weights.append(set_data["weight_lbs"])

    if not weights:
        return {
            "exercise": exercise,
            "trend": "insufficient_data",
            "total_sessions": len(history),
            "message": "No weight data available"
        }

    first_weight = weights[0]
    current_weight = weights[-1]
    max_weight = max(weights)

    # Determine trend
    if current_weight > first_weight * 1.05:
        trend = "increasing"
    elif current_weight < first_weight * 0.95:
        trend = "decreasing"
    else:
        trend = "stable"

    # Calculate weekly increase
    weeks = len(history) / 7.0  # Rough estimate
    if weeks > 0:
        avg_weekly_increase = (current_weight - first_weight) / weeks
    else:
        avg_weekly_increase = 0

    return {
        "exercise": exercise,
        "trend": trend,
        "first_weight": first_weight,
        "current_weight": current_weight,
        "max_weight": max_weight,
        "total_sessions": len(history),
        "avg_weekly_increase": round(avg_weekly_increase, 2)
    }
```

**Key Patterns**:
- Graceful degradation (no data → still returns dict)
- Statistical calculations
- Clear trend categorization
- Echo exercise name in output

---

## Example 4: start_workout_session (Session Tool)

**Location**: `/Users/franklindickinson/Projects/gym-bro/src/tools/session_tools.py`

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
    import uuid
    from src.agents.session_graph import initialize_planning_session

    # Generate session ID
    session_id = str(uuid.uuid4())

    # Initialize session state
    initial_state = initialize_planning_session()
    initial_state['session_id'] = session_id

    if workout_type:
        initial_state['actual_workout_type'] = workout_type

    if equipment_unavailable:
        initial_state['equipment_unavailable'] = equipment_unavailable

    return {
        "session_id": session_id,
        "status": "initialized",
        "workout_type": workout_type,
        "equipment_unavailable": equipment_unavailable or [],
        "message": "Workout session initialized. Ready for planning."
    }
```

**Key Patterns**:
- Delegates to workflow (SessionGraph)
- Generates unique IDs
- Optional parameters with defaults
- Clear status messages

---

## Pattern Summary

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Data Query** | Retrieve existing data | search_workouts, get_exercise_history |
| **Calculation** | Compute from data | calculate_progression, calculate_volume |
| **Aggregation** | Summarize multiple records | get_weekly_split_status, get_workout_count |
| **Comparison** | Side-by-side analysis | compare_exercises, compare_weeks |
| **State Management** | Workflow coordination | start_workout_session |
| **Validation** | Check constraints | validate_abs_spacing |

See [TESTING.md](TESTING.md) for testing these patterns.
