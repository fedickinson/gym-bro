"""
Tools for abs workout recommendations and history tracking.
"""

from langchain.tools import tool
from datetime import date, timedelta
import json
from pathlib import Path


@tool
def get_abs_history(days: int = 30) -> dict:
    """
    Get abs workout history for the specified period.

    Args:
        days: Number of days to look back (default: 30)

    Returns:
        Dictionary with:
        - total_sessions: Total number of abs sessions
        - last_session_date: Date of last abs session (ISO string)
        - days_since_last: Days since last abs session
        - exercises_done: List of exercises with counts [{"name": str, "count": int}]
        - avg_exercises_per_session: Average number of exercises per session
    """
    from src.data import get_logs_by_date_range

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    logs = get_logs_by_date_range(start_date, end_date)

    # Extract abs data from supplementary_work
    abs_sessions = []
    exercise_counts = {}

    for log in logs:
        supp_work = log.get('supplementary_work', [])
        if not supp_work:
            continue

        for work in supp_work:
            # Handle both old and new format
            if isinstance(work, str):
                # Old format: just "abs" flag, no exercises
                continue

            if work.get('type') == 'abs':
                abs_sessions.append({
                    'date': log['date'],
                    'exercises': work.get('exercises', [])
                })

                # Count exercises
                for ex in work.get('exercises', []):
                    ex_name = ex.get('name')
                    if ex_name:
                        exercise_counts[ex_name] = exercise_counts.get(ex_name, 0) + 1

    if not abs_sessions:
        return {
            "total_sessions": 0,
            "last_session_date": None,
            "days_since_last": None,
            "exercises_done": [],
            "avg_exercises_per_session": 0
        }

    # Sort by date
    abs_sessions.sort(key=lambda x: x['date'], reverse=True)
    last_date = date.fromisoformat(abs_sessions[0]['date'])
    days_since = (date.today() - last_date).days

    total_exercises = sum(len(s['exercises']) for s in abs_sessions)

    return {
        "total_sessions": len(abs_sessions),
        "last_session_date": str(last_date),
        "days_since_last": days_since,
        "exercises_done": [
            {"name": name, "count": count}
            for name, count in sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "avg_exercises_per_session": total_exercises / len(abs_sessions) if abs_sessions else 0
    }


@tool
def get_available_abs_templates() -> list[dict]:
    """
    Get all available abs templates with metadata.

    Returns:
        List of template metadata dicts with:
        - id: Template ID
        - name: Template name
        - category: Category (strength, endurance, stability)
        - difficulty: Difficulty level (beginner, intermediate, advanced)
        - estimated_duration_min: Estimated duration in minutes
        - num_exercises: Number of exercises in template
    """
    template_file = Path(__file__).parent.parent.parent / "data" / "abs_templates.json"

    if not template_file.exists():
        return []

    with open(template_file, 'r') as f:
        data = json.load(f)

    templates = data.get('templates', [])

    # Return metadata only
    return [
        {
            "id": t['id'],
            "name": t['name'],
            "category": t.get('category', 'general'),
            "difficulty": t.get('difficulty', 'intermediate'),
            "estimated_duration_min": t.get('estimated_duration_min', 15),
            "num_exercises": len(t.get('exercises', []))
        }
        for t in templates
    ]


def get_abs_template_by_id(template_id: str) -> dict | None:
    """
    Get full abs template by ID.

    Args:
        template_id: ID of the template to retrieve

    Returns:
        Full template dict or None if not found
    """
    template_file = Path(__file__).parent.parent.parent / "data" / "abs_templates.json"

    if not template_file.exists():
        return None

    with open(template_file, 'r') as f:
        data = json.load(f)

    templates = data.get('templates', [])

    for template in templates:
        if template['id'] == template_id:
            return template

    return None
