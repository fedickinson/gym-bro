"""
Pydantic models for the fitness coach application.
These provide type safety and validation across the app.
"""

from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


# ============================================================================
# Core Workout Models
# ============================================================================

class Set(BaseModel):
    """A single set within an exercise."""
    reps: int
    weight_lbs: float | None = None
    rpe: int | None = Field(None, ge=1, le=10, description="Rate of Perceived Exertion 1-10")
    notes: str | None = None


class Exercise(BaseModel):
    """An exercise with its sets."""
    name: str
    sets: list[Set]
    notes: str | None = None


class Warmup(BaseModel):
    """Warmup activity before workout."""
    type: str  # "jog", "incline walk", "bike", etc.
    duration_min: float | None = None
    distance_miles: float | None = None
    notes: str | None = None


WorkoutType = Literal["Push", "Pull", "Legs", "Upper", "Lower", "Class", "Cardio", "Active Recovery", "Other"]


class WorkoutLog(BaseModel):
    """A logged workout session."""
    id: str
    date: date
    type: WorkoutType
    template_id: str | None = None
    exercises: list[Exercise] = []
    warmup: Warmup | None = None
    notes: str | None = None
    completed: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    # Phase 6: Session-based workout tracking (plan vs actual)
    session_id: str | None = None
    suggested_type: str | None = None  # What AI originally suggested
    planned_template_id: str | None = None  # ID of planned template
    plan_adjustments: list[dict] | None = None  # Chat modifications to plan
    deviations_detected: list[dict] | None = None  # Exercises that deviated from plan
    equipment_unavailable: list[str] | None = None  # Equipment constraints during session


# ============================================================================
# Template Models
# ============================================================================

class TemplateExercise(BaseModel):
    """An exercise in a workout template."""
    name: str
    target_sets: int
    target_reps: int | str  # Can be "8-12" or "max"
    rest_seconds: int = 90
    notes: str | None = None


class Superset(BaseModel):
    """A superset grouping in a template."""
    exercises: list[str]
    rounds: int
    rest_seconds: int = 60


class WorkoutTemplate(BaseModel):
    """A reusable workout template."""
    id: str
    name: str
    type: WorkoutType
    exercises: list[TemplateExercise]
    supersets: list[Superset] = []
    notes: str | None = None


# ============================================================================
# Weekly Split Models
# ============================================================================

class SplitConfig(BaseModel):
    """Configuration for the weekly workout split."""
    types: list[str] = ["Push", "Pull", "Legs", "Upper", "Lower"]
    rotation: list[str] = ["Push", "Pull", "Legs", "Upper", "Lower", "Legs"]
    weekly_targets: dict[str, int] = {
        "Push": 1,
        "Pull": 1,
        "Legs": 2,
        "Upper": 1,
        "Lower": 1
    }


class WeeklyProgress(BaseModel):
    """Current week's workout progress."""
    start_date: date
    completed: dict[str, list[date]] = {}  # type → list of dates completed
    next_in_rotation: str = "Push"


class WeeklySplit(BaseModel):
    """Full weekly split state."""
    config: SplitConfig = Field(default_factory=SplitConfig)
    current_week: WeeklyProgress


# ============================================================================
# Exercise Reference
# ============================================================================

class ExerciseInfo(BaseModel):
    """Reference information about an exercise."""
    canonical_name: str
    variations: list[str] = []
    muscle_groups: list[str] = []
    equipment: list[str] = []


# ============================================================================
# Agent/Tool Response Models
# ============================================================================

class ProgressionStats(BaseModel):
    """Stats about exercise progression."""
    exercise: str
    first_weight: float | None
    current_weight: float | None
    max_weight: float | None
    total_sessions: int
    trend: Literal["increasing", "stable", "decreasing", "insufficient_data"]
    avg_increase_per_week: float | None = None


class WeeklySplitStatus(BaseModel):
    """Current status of weekly split completion."""
    week_start: date
    completed: dict[str, int]  # type → count completed
    targets: dict[str, int]    # type → target count
    remaining: dict[str, int]  # type → remaining count
    next_suggested: str
    days_left_in_week: int


class WorkoutSuggestion(BaseModel):
    """A suggested workout."""
    type: WorkoutType
    reason: str
    template_id: str | None = None
    template_name: str | None = None


# ============================================================================
# Intent Classification
# ============================================================================

Intent = Literal["log", "query", "recommend", "chat", "admin"]


class ClassifiedIntent(BaseModel):
    """Result of intent classification."""
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    reasoning: str | None = None
