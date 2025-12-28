"""
Adaptive Template Generator.

Generates personalized workout templates based on historical patterns,
progression data, and training phase.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from src.data import get_template, get_exercise_history
from src.analysis.workout_patterns import (
    analyze_exercise_patterns,
    analyze_volume_tolerance,
    analyze_progression_velocity
)


def generate_adaptive_template(workout_type: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate a personalized workout template based on user's training history.

    Algorithm:
    1. Start with base template (static fallback)
    2. Analyze patterns (which exercises user actually does)
    3. Get progression data (current weights)
    4. Adjust volume (based on user's typical volume)
    5. Suggest weights (based on last workout + progression)
    6. Add coaching notes (explain adaptations)

    Args:
        workout_type: Push, Pull, Legs, Upper, Lower
        context: Optional context dict (e.g., {"feeling": "fatigued"})

    Returns:
        Adaptive template with:
        - exercises: List of exercises with suggested weights and reasoning
        - coaching_notes: List of coaching insights
        - adaptations: List of changes made from base template
        - mode: "adaptive"
    """
    # 1. Get base template
    base_template = get_template(workout_type.lower() + "_a")

    if not base_template:
        return {
            "error": f"No base template found for {workout_type}",
            "mode": "error"
        }

    # 2. Analyze patterns (all-time data for best understanding)
    patterns = analyze_exercise_patterns(workout_type, days=0)
    volume = analyze_volume_tolerance(workout_type, days=0)

    # Check if user has sufficient history to personalize
    has_history = patterns.get('total_workouts', 0) >= 3  # Need at least 3 workouts to personalize

    # 3. Build exercise list (prioritize common exercises if history exists)
    adapted_exercises = []
    removed_exercises = []

    for exercise in base_template.get("exercises", []):
        exercise_name = exercise.get("name", "")

        if not exercise_name:
            continue

        # Only filter by frequency if user has history
        if has_history:
            frequency = _get_exercise_frequency(exercise_name, patterns)

            if frequency < 0.3:  # Skip rarely done exercises
                removed_exercises.append(exercise_name)
                continue

        # Get progression status (only if user has history)
        if has_history:
            progression = analyze_progression_velocity(exercise_name, days=0)
            history = get_exercise_history(exercise_name, days=0)  # All-time history

            # Determine suggested weight
            if history and len(history) > 0:
                last_weight = history[-1]["max_weight"]

                if progression["suggested_action"] == "increase":
                    suggested_weight = last_weight + max(2.5, progression["avg_weekly_increase"])
                elif progression["suggested_action"] == "deload":
                    suggested_weight = last_weight * 0.9  # 10% deload
                else:
                    suggested_weight = last_weight  # maintain
            else:
                # No history for this exercise yet - use beginner weight
                from src.agents.suggestion_engine import _get_beginner_weight
                suggested_weight, _ = _get_beginner_weight(exercise_name)

            # Determine sets/reps (use user's typical or template default)
            user_avg_sets = _get_avg_sets_for_exercise(exercise_name, patterns)
            target_sets = int(user_avg_sets) if user_avg_sets else exercise.get("target_sets", 4)
            reasoning = _build_reasoning(exercise_name, progression, history)
        else:
            # No history - use beginner weight from catalog
            from src.agents.suggestion_engine import _get_beginner_weight
            suggested_weight, beginner_reasoning = _get_beginner_weight(exercise_name)
            target_sets = exercise.get("target_sets", 4)
            reasoning = beginner_reasoning

        # Build adapted exercise
        adapted_exercises.append({
            "name": exercise_name,
            "suggested_weight_lbs": round(suggested_weight, 1) if suggested_weight else None,
            "target_sets": target_sets,
            "target_reps": exercise.get("target_reps", "8-10"),
            "rest_seconds": exercise.get("rest_seconds", 90),
            "reasoning": reasoning
        })

    # 4. Build coaching notes (only for users with history)
    coaching_notes = []

    if has_history:
        if volume["volume_trend"] == "increasing":
            pct_increase = ((volume["recent_avg_sets"] - volume["older_avg_sets"]) /
                           volume["older_avg_sets"] * 100) if volume["older_avg_sets"] > 0 else 0
            if pct_increase > 15:
                coaching_notes.append(
                    f"⚠️ Volume has increased {pct_increase:.0f}% over time. "
                    "Consider a deload if feeling fatigued."
                )

        if volume["volume_trend"] == "decreasing":
            coaching_notes.append(
                "📉 Volume has decreased recently. Consider increasing if recovering well."
            )

    # 5. Build adaptations summary
    adaptations = []

    if not has_history:
        # User is new - using base template
        adaptations.append("Using base template - we'll personalize as you build history")
    else:
        # User has history - show personalizations
        if removed_exercises:
            adaptations.append(
                f"Removed {len(removed_exercises)} rarely-done exercises"
            )

        if len(adapted_exercises) > 0:
            weights_adjusted = sum(1 for ex in adapted_exercises if ex.get("suggested_weight_lbs"))
            if weights_adjusted > 0:
                adaptations.append(
                    f"Suggested weights for {weights_adjusted} exercises based on your last workout"
                )

        if volume.get('avg_total_sets', 0) > 0:
            adaptations.append(
                f"Volume adjusted to {volume['avg_total_sets']:.0f} sets (your typical)"
            )

    # 6. Return adaptive template
    return {
        "id": f"adaptive_{workout_type.lower()}",
        "name": f"Adaptive {workout_type} Workout",
        "type": workout_type,
        "exercises": adapted_exercises,
        "coaching_notes": coaching_notes,
        "adaptations": adaptations,
        "mode": "adaptive",
        "generated_at": datetime.now().isoformat()
    }


def _get_exercise_frequency(exercise_name: str, patterns: Dict) -> float:
    """Get frequency of an exercise from pattern analysis."""
    for ex in patterns.get("common_exercises", []):
        if ex.get("name", "").lower() == exercise_name.lower():
            return ex.get("frequency", 0)

    # Not in common exercises, check if in rarely done
    if exercise_name in patterns.get("rarely_done", []):
        return 0.1  # Low frequency

    return 0.5  # Default: moderate frequency


def _get_avg_sets_for_exercise(exercise_name: str, patterns: Dict) -> Optional[float]:
    """Get average sets per workout for an exercise."""
    for ex in patterns.get("common_exercises", []):
        if ex.get("name", "").lower() == exercise_name.lower():
            return ex.get("avg_sets")
    return None


def _build_reasoning(exercise_name: str, progression: Dict, history: List) -> str:
    """
    Generate human-readable reasoning for exercise prescription.

    Args:
        exercise_name: Name of exercise
        progression: Progression analysis dict
        history: Exercise history list

    Returns:
        Reasoning string explaining the suggested weight
    """
    if not history or len(history) == 0:
        return "No recent history. Start with a comfortable weight and focus on form."

    last_weight = history[-1]["max_weight"]
    suggested_action = progression.get("suggested_action", "maintain")

    if suggested_action == "increase":
        new_weight = last_weight + max(2.5, progression.get("avg_weekly_increase", 2.5))
        return (
            f"Last workout: {last_weight} lbs. You've been progressing well. "
            f"Try {new_weight:.0f} lbs today."
        )

    elif suggested_action == "deload":
        weeks = progression.get("weeks_at_current_weight", 4)
        deload_weight = last_weight * 0.9
        return (
            f"Plateau detected at {last_weight} lbs for {weeks} weeks. "
            f"Deload to {deload_weight:.0f} lbs and rebuild."
        )

    else:  # maintain
        data_points = progression.get("data_points", 0)
        if data_points < 3:
            return (
                f"Continue at {last_weight} lbs. Build more consistency "
                "before increasing weight."
            )
        else:
            return (
                f"Maintain {last_weight} lbs. Focus on hitting all reps with good form "
                "before progressing."
            )
