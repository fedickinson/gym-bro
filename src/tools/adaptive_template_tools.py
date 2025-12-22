"""
Adaptive Template Tools - LangChain tools for pattern analysis and adaptive templates.

These tools are used by agents to access:
- Pattern analysis (exercise preferences, volume tolerance, progression)
- Adaptive template generation
- Training fatigue detection
"""

from langchain_core.tools import tool
from src.analysis.workout_patterns import (
    analyze_exercise_patterns,
    analyze_volume_tolerance,
    analyze_progression_velocity,
    analyze_recovery_patterns,
    detect_overtraining_signals
)
from src.agents.template_generator import generate_adaptive_template


@tool
def analyze_workout_patterns(workout_type: str) -> dict:
    """
    Analyze user's training patterns for a workout type.

    Use this to understand:
    - Which exercises the user actually does (vs skips)
    - Their typical volume and intensity
    - Progression rates per exercise

    Args:
        workout_type: Push, Pull, Legs, Upper, or Lower

    Returns:
        Comprehensive pattern analysis including:
        - exercise_patterns: Common exercises, rarely done, frequency
        - volume_tolerance: Avg sets, volume trend
        - recovery_patterns: Optimal rest days, frequency

    Example:
        patterns = analyze_workout_patterns("Pull")
        # Returns analysis of Pull workout patterns
    """
    return {
        "workout_type": workout_type,
        "exercise_patterns": analyze_exercise_patterns(workout_type, days=0),
        "volume_tolerance": analyze_volume_tolerance(workout_type, days=0),
        "recovery_patterns": analyze_recovery_patterns(workout_type.lower(), days=0)
    }


@tool
def check_progression_status(exercise_name: str) -> dict:
    """
    Check if an exercise is ready for weight increase, deload, or variation.

    Use this when user asks about progression or when generating adaptive templates.

    Args:
        exercise_name: Name of exercise (e.g., "Lat Pulldown", "Bench Press")

    Returns:
        Progression analysis with:
        - current_weight: Most recent weight used
        - velocity: slow/moderate/fast/plateau
        - suggested_action: increase/maintain/deload
        - reasoning: Why this suggestion

    Example:
        status = check_progression_status("Lat Pulldown")
        if status["suggested_action"] == "increase":
            # Suggest higher weight
    """
    return analyze_progression_velocity(exercise_name, days=0)


@tool
def detect_training_fatigue() -> dict:
    """
    Detect signs of overtraining and recommend deload if needed.

    Use this when:
    - User reports feeling tired
    - Generating recommendations for next workout
    - User asks about recovery

    Returns:
        Fatigue analysis with:
        - overtraining_risk: low/moderate/high
        - signals: List of warning signs
        - recommendation: continue/monitor/deload_recommended

    Example:
        fatigue = detect_training_fatigue()
        if fatigue["overtraining_risk"] == "high":
            # Recommend deload week
    """
    return detect_overtraining_signals(days=30)


@tool
def generate_personalized_template(workout_type: str) -> dict:
    """
    Generate a personalized workout template based on user's training history.

    This is the PRIMARY tool for creating adaptive workouts. It combines:
    - Pattern analysis (which exercises user does)
    - Progression data (suggested weights)
    - Volume adjustment (user's typical sets/reps)

    Args:
        workout_type: Push, Pull, Legs, Upper, or Lower

    Returns:
        Adaptive template with:
        - exercises: List with suggested weights and reasoning
        - coaching_notes: Personalized insights
        - adaptations: What changed from base template
        - mode: "adaptive"

    Example:
        template = generate_personalized_template("Pull")
        # Returns personalized Pull workout based on history
    """
    return generate_adaptive_template(workout_type)
