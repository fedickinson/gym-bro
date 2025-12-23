"""
Plan Adapter - AI-powered plan regeneration when user deviates mid-workout.

When user goes off-plan and chooses to adapt:
- Analyzes exercises completed so far
- Determines actual workout type
- Generates complementary exercises for the remaining workout
- Updates plan with adaptation reasoning
"""

from typing import Literal
from src.tools.recommend_tools import get_workout_template


def adapt_plan_for_deviation(
    accumulated_exercises: list[dict],
    new_workout_type: str,
    equipment_unavailable: list[str] | None = None
) -> dict:
    """
    Regenerate workout plan based on actual exercises performed.

    Called when user deviates significantly and chooses "Adapt rest of plan".

    Args:
        accumulated_exercises: Exercises completed so far (including deviated exercise)
        new_workout_type: Detected workout type based on actual exercises
        equipment_unavailable: Equipment constraints to respect

    Returns:
        Adapted plan dict:
        {
            "adapted_template": dict,  # New template for remaining workout
            "adaptation_reason": str,  # Why plan was adapted
            "original_type": str,  # What was originally planned
            "new_type": str,  # What user is actually doing
            "exercises_completed": int,  # How many exercises done before adaptation
            "timestamp": str  # When adaptation occurred
        }
    """
    from datetime import datetime

    # Analyze completed exercises
    exercises_done = len(accumulated_exercises)
    exercises_done_names = [ex.get('name') for ex in accumulated_exercises]

    # Get fresh adaptive template for the new workout type
    template_result = get_workout_template.invoke({
        "workout_type": new_workout_type,
        "adaptive": True
    })

    if not template_result or not template_result.get('found'):
        # Fallback: Create minimal template
        adapted_template = {
            "id": f"adapted_{new_workout_type.lower()}",
            "name": f"Adapted {new_workout_type} Workout",
            "type": new_workout_type,
            "exercises": [],
            "mode": "adaptive",
            "coaching_notes": [
                f"Plan adapted mid-workout to {new_workout_type}"
            ]
        }
    else:
        adapted_template = template_result

    # Filter out exercises already completed
    remaining_exercises = []
    for ex in adapted_template.get('exercises', []):
        # Don't suggest exercises we've already done
        if ex.get('name') not in exercises_done_names:
            remaining_exercises.append(ex)

    # Update template with remaining exercises
    adapted_template['exercises'] = remaining_exercises

    # Add adaptation metadata
    adapted_template['adapted'] = True
    adapted_template['adaptation_timestamp'] = datetime.now().isoformat()

    # Generate adaptation reason
    adaptation_reason = _generate_adaptation_reason(
        exercises_done,
        exercises_done_names,
        new_workout_type
    )

    return {
        "adapted_template": adapted_template,
        "adaptation_reason": adaptation_reason,
        "new_type": new_workout_type,
        "exercises_completed": exercises_done,
        "timestamp": datetime.now().isoformat()
    }


def _generate_adaptation_reason(
    exercises_count: int,
    exercise_names: list[str],
    new_type: str
) -> str:
    """
    Generate human-readable explanation for why plan was adapted.

    Args:
        exercises_count: Number of exercises completed
        exercise_names: Names of exercises done
        new_type: New workout type

    Returns:
        Adaptation reason string
    """
    if exercises_count == 1:
        return f"Plan adapted to {new_type} after completing {exercise_names[0]}"
    else:
        exercises_str = ", ".join(exercise_names[-2:])  # Show last 2
        return f"Plan adapted to {new_type} after {exercises_count} exercises ({exercises_str})"
