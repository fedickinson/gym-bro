"""
Suggestion Engine - AI-powered exercise suggestions during workouts.

Provides next exercise suggestions based on:
- Planned template (if user is following the plan)
- AI-generated adaptive suggestions (if off-plan or template exhausted)
- Weight progression from historical data
"""

from typing import Literal
from src.tools.recommend_tools import get_workout_template
from src.data import get_exercise_history


def suggest_next_exercise(
    session_state: dict,
    source: Literal["auto", "plan", "adaptive"] = "auto"
) -> dict:
    """
    Generate next exercise suggestion for the user.

    Args:
        session_state: Current SessionWithPlanState
        source: Suggestion source - "auto" (default), "plan" (force plan), "adaptive" (force AI)

    Returns:
        Suggestion dict with:
        {
            "source": "plan" | "adaptive",
            "exercise_name": str,
            "target_sets": int,
            "target_reps": int,
            "suggested_weight_lbs": float | None,
            "rest_seconds": int,
            "reasoning": str,
            "plan_index": int | None  # Position in plan if from plan
        }
    """
    planned_template = session_state.get('planned_template', {})
    current_index = session_state.get('current_exercise_index', 0)
    accumulated = session_state.get('accumulated_exercises', [])
    workout_type = session_state.get('actual_workout_type', session_state.get('suggested_type'))

    # Auto-detect source if not specified
    if source == "auto":
        # Check if plan has next exercise
        plan_exercises = planned_template.get('exercises', [])
        if current_index < len(plan_exercises):
            source = "plan"
        else:
            source = "adaptive"

    # Get suggestion based on source
    if source == "plan":
        return _suggest_from_plan(
            planned_template,
            current_index,
            accumulated
        )
    else:
        return _suggest_adaptive(
            workout_type,
            accumulated,
            session_state.get('equipment_unavailable', [])
        )


def _suggest_from_plan(
    planned_template: dict,
    current_index: int,
    accumulated_exercises: list[dict]
) -> dict:
    """
    Get next exercise from the planned template.

    Args:
        planned_template: The workout template
        current_index: Current position in plan (0-based)
        accumulated_exercises: Exercises completed so far

    Returns:
        Suggestion dict with source="plan"
    """
    plan_exercises = planned_template.get('exercises', [])

    # Check if index is valid
    if current_index >= len(plan_exercises):
        # Template exhausted - return empty suggestion
        return {
            "source": "plan",
            "exercise_name": None,
            "target_sets": 0,
            "target_reps": 0,
            "suggested_weight_lbs": None,
            "rest_seconds": 0,
            "reasoning": "You've completed the planned template!",
            "plan_index": None
        }

    # Get next exercise from plan
    next_exercise = plan_exercises[current_index]

    # Get weight suggestion from history (if available)
    exercise_name = next_exercise.get('name')
    suggested_weight = next_exercise.get('suggested_weight_lbs')

    # If template doesn't have weight suggestion, check history
    if not suggested_weight and exercise_name:
        suggested_weight = _get_progressive_weight(exercise_name)

    return {
        "source": "plan",
        "exercise_name": exercise_name,
        "target_sets": next_exercise.get('target_sets', 3),
        "target_reps": next_exercise.get('target_reps', 10),
        "suggested_weight_lbs": suggested_weight,
        "rest_seconds": next_exercise.get('rest_seconds', 90),
        "reasoning": next_exercise.get('reasoning', f"Next from your {planned_template.get('type', 'workout')} plan"),
        "plan_index": current_index
    }


def _suggest_adaptive(
    workout_type: str,
    accumulated_exercises: list[dict],
    equipment_unavailable: list[str] | None
) -> dict:
    """
    Generate AI-powered adaptive suggestion.

    Used when:
    - User has gone off-plan
    - Template is exhausted but user wants to continue
    - No template available

    Args:
        workout_type: Current workout type (Push/Pull/Legs)
        accumulated_exercises: Exercises done so far
        equipment_unavailable: Equipment constraints

    Returns:
        Suggestion dict with source="adaptive"
    """
    from src.tools.recommend_tools import suggest_next_workout

    # For Phase 2, use a simplified adaptive suggestion
    # In future phases, we'll make this more sophisticated

    # Get exercises already done
    done_exercise_names = [ex.get('name') for ex in accumulated_exercises]

    # Get a fresh template for this workout type (adaptive mode)
    template_result = get_workout_template.invoke({
        "workout_type": workout_type,
        "adaptive": True
    })

    if template_result and template_result.get('found'):
        template = template_result
        exercises = template.get('exercises', [])

        # Find first exercise NOT already done
        for ex in exercises:
            if ex.get('name') not in done_exercise_names:
                # Get progressive weight
                suggested_weight = ex.get('suggested_weight_lbs')
                if not suggested_weight:
                    suggested_weight = _get_progressive_weight(ex.get('name'))

                return {
                    "source": "adaptive",
                    "exercise_name": ex.get('name'),
                    "target_sets": ex.get('target_sets', 3),
                    "target_reps": ex.get('target_reps', 10),
                    "suggested_weight_lbs": suggested_weight,
                    "rest_seconds": ex.get('rest_seconds', 90),
                    "reasoning": f"AI suggests complementary {workout_type} exercise",
                    "plan_index": None
                }

    # Fallback: No suggestion available
    return {
        "source": "adaptive",
        "exercise_name": None,
        "target_sets": 0,
        "target_reps": 0,
        "suggested_weight_lbs": None,
        "rest_seconds": 0,
        "reasoning": "Great workout! Consider finishing or adding your own exercise.",
        "plan_index": None
    }


def _get_progressive_weight(exercise_name: str) -> float | None:
    """
    Get suggested weight with progressive overload.

    Args:
        exercise_name: Name of the exercise

    Returns:
        Suggested weight in lbs, or None if no history
    """
    try:
        # Get recent history for this exercise (last 90 days)
        history = get_exercise_history.invoke({
            "exercise": exercise_name,
            "days": 90
        })

        if not history or not isinstance(history, list) or len(history) == 0:
            return None

        # Get most recent workout
        latest = history[0]
        if not latest or 'sets' not in latest:
            return None

        # Find max weight used in latest workout
        max_weight = 0
        for workout_set in latest['sets']:
            weight = workout_set.get('weight_lbs', 0)
            if weight and weight > max_weight:
                max_weight = weight

        if max_weight == 0:
            return None

        # Progressive overload: +2.5 lbs for upper body, +5 lbs for lower body
        # Determine if lower body based on exercise name
        lower_body_keywords = ['squat', 'leg', 'deadlift', 'calf', 'lunge', 'hip']
        is_lower_body = any(keyword in exercise_name.lower() for keyword in lower_body_keywords)

        increment = 5 if is_lower_body else 2.5

        return max_weight + increment

    except Exception as e:
        # If anything fails, return None (no suggestion)
        return None
