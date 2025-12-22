"""
Query Tools - Tools for searching and analyzing workout history.

These tools are used by the Query Agent (ReAct) to answer questions
about workout history, exercise progression, etc.
"""

from datetime import date, timedelta
from langchain_core.tools import tool
from src.data import (
    get_all_logs, 
    get_logs_by_date_range, 
    get_exercise_history as _get_exercise_history
)
from src.models import ProgressionStats


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
    history = _get_exercise_history(exercise, days)
    return history


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
            "message": "No weight data recorded"
        }
    
    # Calculate stats
    first_weight = weights[0] if weights else None
    current_weight = weights[-1] if weights else None
    max_weight = max(weights) if weights else None
    
    # Determine trend (simple: compare first half avg to second half avg)
    if len(weights) >= 4:
        mid = len(weights) // 2
        first_half_avg = sum(weights[:mid]) / mid
        second_half_avg = sum(weights[mid:]) / (len(weights) - mid)
        
        if second_half_avg > first_half_avg * 1.05:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Calculate weekly increase (if we have date data)
    first_date = history[0].get("date") if history else None
    last_date = history[-1].get("date") if history else None
    
    avg_increase = None
    if first_date and last_date and first_weight and current_weight:
        days_span = (date.fromisoformat(last_date) - date.fromisoformat(first_date)).days
        if days_span > 7:
            weeks = days_span / 7
            total_increase = current_weight - first_weight
            avg_increase = round(total_increase / weeks, 2)
    
    return {
        "exercise": exercise,
        "first_weight": first_weight,
        "current_weight": current_weight,
        "max_weight": max_weight,
        "total_sessions": len(history),
        "trend": trend,
        "avg_increase_per_week": avg_increase
    }


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
    stats1 = calculate_progression.invoke({"exercise": exercise1})
    stats2 = calculate_progression.invoke({"exercise": exercise2})
    
    return {
        "comparison": [stats1, stats2],
        "summary": _generate_comparison_summary(stats1, stats2)
    }


@tool
def get_workout_count(days: int = 30, workout_type: str | None = None) -> dict:
    """
    Count workouts in a time period, optionally filtered by type.
    
    Args:
        days: Number of days to count (default 30)
        workout_type: Optional filter by type (Push, Pull, Legs, etc.)
    
    Returns:
        Count and breakdown by type
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    logs = get_logs_by_date_range(start_date, end_date)
    
    if workout_type:
        logs = [l for l in logs if l.get("type", "").lower() == workout_type.lower()]
    
    # Count by type
    by_type = {}
    for log in logs:
        t = log.get("type", "Unknown")
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        "total": len(logs),
        "days": days,
        "by_type": by_type,
        "filter": workout_type
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _summarize_log(log: dict) -> dict:
    """Create a summary of a workout log for search results."""
    exercises = [ex.get("name") for ex in log.get("exercises", [])]
    return {
        "date": log.get("date"),
        "type": log.get("type"),
        "exercises": exercises[:5],  # First 5 exercises
        "exercise_count": len(exercises),
        "notes": log.get("notes")
    }


def _generate_comparison_summary(stats1: dict, stats2: dict) -> str:
    """Generate a human-readable comparison summary."""
    ex1 = stats1.get("exercise", "Exercise 1")
    ex2 = stats2.get("exercise", "Exercise 2")
    
    lines = []
    
    # Compare trends
    t1, t2 = stats1.get("trend"), stats2.get("trend")
    if t1 == "increasing" and t2 != "increasing":
        lines.append(f"{ex1} is progressing better than {ex2}")
    elif t2 == "increasing" and t1 != "increasing":
        lines.append(f"{ex2} is progressing better than {ex1}")
    elif t1 == t2:
        lines.append(f"Both exercises have {t1} trends")
    
    # Compare session counts
    s1, s2 = stats1.get("total_sessions", 0), stats2.get("total_sessions", 0)
    if abs(s1 - s2) > 3:
        more = ex1 if s1 > s2 else ex2
        lines.append(f"You train {more} more frequently")
    
    return " | ".join(lines) if lines else "Similar progression patterns"


# Export all tools for the agent
QUERY_TOOLS = [
    search_workouts,
    get_exercise_history,
    calculate_progression,
    compare_exercises,
    get_workout_count
]
