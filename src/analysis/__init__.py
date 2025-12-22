"""
Pattern Analysis Module for Adaptive Coaching.

This module learns from workout history to detect patterns,
preferences, and progression trends.
"""

from .workout_patterns import (
    analyze_exercise_patterns,
    analyze_volume_tolerance,
    analyze_progression_velocity,
    analyze_recovery_patterns,
    detect_overtraining_signals
)

__all__ = [
    'analyze_exercise_patterns',
    'analyze_volume_tolerance',
    'analyze_progression_velocity',
    'analyze_recovery_patterns',
    'detect_overtraining_signals'
]
