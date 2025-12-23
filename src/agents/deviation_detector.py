"""
Deviation Detector - Detects when user goes off-plan during workout.

Analyzes:
- Exercise similarity (did user do something similar or completely different?)
- Workout type impact (does deviation change the workout type?)
- Severity: minor_variation vs major_deviation
"""

from typing import Literal
from difflib import SequenceMatcher


def detect_deviation(
    current_exercise: dict,
    planned_exercise: dict | None,
    current_workout_type: str
) -> dict:
    """
    Detect if user deviated from the plan.

    Args:
        current_exercise: Exercise user actually performed
        planned_exercise: Exercise that was planned (from template)
        current_workout_type: Current workout type (Push/Pull/Legs)

    Returns:
        Deviation analysis dict:
        {
            "is_deviation": bool,
            "severity": "none" | "minor_variation" | "major_deviation",
            "similarity_score": float (0-1),
            "planned_name": str | None,
            "actual_name": str,
            "impact_description": str,
            "changes_workout_type": bool,
            "new_workout_type": str | None
        }
    """
    actual_name = current_exercise.get('name', 'Unknown')

    # No planned exercise - can't detect deviation
    if not planned_exercise:
        return {
            "is_deviation": False,
            "severity": "none",
            "similarity_score": 1.0,
            "planned_name": None,
            "actual_name": actual_name,
            "impact_description": "No plan to compare against",
            "changes_workout_type": False,
            "new_workout_type": None
        }

    planned_name = planned_exercise.get('name', 'Unknown')

    # Calculate similarity
    similarity = _calculate_exercise_similarity(actual_name, planned_name)

    # Determine severity
    if similarity >= 0.85:
        # Very similar - not a deviation (e.g., "Bench Press" vs "Barbell Bench Press")
        severity = "none"
        is_deviation = False
    elif similarity >= 0.50:
        # Somewhat similar - minor variation (e.g., "Dumbbell Bench" vs "Barbell Bench")
        severity = "minor_variation"
        is_deviation = True
    else:
        # Very different - major deviation (e.g., "Squat" vs "Bench Press")
        severity = "major_deviation"
        is_deviation = True

    # Analyze workout type impact
    changes_type, new_type = _analyze_workout_type_impact(
        actual_name,
        planned_name,
        current_workout_type
    )

    # Generate impact description
    impact_description = _generate_impact_description(
        severity,
        planned_name,
        actual_name,
        changes_type,
        new_type
    )

    return {
        "is_deviation": is_deviation,
        "severity": severity,
        "similarity_score": similarity,
        "planned_name": planned_name,
        "actual_name": actual_name,
        "impact_description": impact_description,
        "changes_workout_type": changes_type,
        "new_workout_type": new_type
    }


def _calculate_exercise_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two exercise names.

    Uses a combination of:
    - String similarity (SequenceMatcher)
    - Common word matching
    - Equipment variations

    Args:
        name1: First exercise name
        name2: Second exercise name

    Returns:
        Similarity score 0-1 (1 = identical, 0 = completely different)
    """
    # Normalize names
    norm1 = name1.lower().strip()
    norm2 = name2.lower().strip()

    # Exact match
    if norm1 == norm2:
        return 1.0

    # Sequence matching
    seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()

    # Word-based matching (for equipment variations)
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    # Remove common equipment words for core exercise matching
    equipment_words = {'barbell', 'dumbbell', 'cable', 'machine', 'smith', 'ez', 'trap', 'band'}

    core_words1 = words1 - equipment_words
    core_words2 = words2 - equipment_words

    # If core exercises match (after removing equipment), it's a minor variation
    if core_words1 and core_words2:
        word_overlap = len(core_words1 & core_words2) / max(len(core_words1), len(core_words2))

        # Boost score if core exercises match
        if word_overlap >= 0.5:
            return max(seq_similarity, 0.6)  # At least 0.6 for equipment variations

    return seq_similarity


def _analyze_workout_type_impact(
    actual_exercise: str,
    planned_exercise: str,
    current_type: str
) -> tuple[bool, str | None]:
    """
    Analyze if deviation changes the workout type.

    Args:
        actual_exercise: Exercise user did
        planned_exercise: Exercise that was planned
        current_type: Current workout type

    Returns:
        Tuple of (changes_type: bool, new_type: str | None)
    """
    # Simple heuristic based on exercise name keywords
    # In Phase 4, this could be enhanced with an LLM classification

    push_keywords = ['press', 'push', 'tricep', 'chest', 'shoulder', 'delt', 'fly']
    pull_keywords = ['pull', 'row', 'curl', 'bicep', 'lat', 'back', 'chin', 'deadlift']
    leg_keywords = ['squat', 'leg', 'lunge', 'calf', 'quad', 'hamstring', 'glute']

    def classify_exercise(name: str) -> str:
        """Classify exercise into Push/Pull/Legs."""
        name_lower = name.lower()

        # Check each category
        push_score = sum(1 for kw in push_keywords if kw in name_lower)
        pull_score = sum(1 for kw in pull_keywords if kw in name_lower)
        leg_score = sum(1 for kw in leg_keywords if kw in name_lower)

        # Return category with highest score
        if push_score > pull_score and push_score > leg_score:
            return "Push"
        elif pull_score > push_score and pull_score > leg_score:
            return "Pull"
        elif leg_score > 0:
            return "Legs"
        else:
            return current_type  # Default to current type if unclear

    # Classify both exercises
    actual_type = classify_exercise(actual_exercise)
    planned_type = classify_exercise(planned_exercise)

    # Check if types differ
    if actual_type != planned_type:
        return True, actual_type
    else:
        return False, None


def _generate_impact_description(
    severity: str,
    planned_name: str,
    actual_name: str,
    changes_type: bool,
    new_type: str | None
) -> str:
    """
    Generate human-readable impact description.

    Args:
        severity: Deviation severity
        planned_name: Planned exercise name
        actual_name: Actual exercise name
        changes_type: Whether workout type changed
        new_type: New workout type if changed

    Returns:
        Impact description string
    """
    if severity == "none":
        return f"On plan - {actual_name}"

    if severity == "minor_variation":
        if changes_type:
            return f"Minor variation: Did {actual_name} instead of {planned_name}. Changes workout from {new_type or 'Unknown'}."
        else:
            return f"Equipment variation: {actual_name} instead of {planned_name} (same muscle group)"

    # Major deviation
    if changes_type:
        return f"Off-plan: Did {actual_name} instead of {planned_name}. Changes workout to {new_type}."
    else:
        return f"Different exercise: {actual_name} instead of {planned_name}"
