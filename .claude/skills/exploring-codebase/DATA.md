# Gym Bro Data Reference

## Contents
- Pydantic Models (type definitions)
- JSON File Schemas
- Data Layer Operations
- Migration Patterns

---

## Pydantic Models

**File**: `/Users/franklindickinson/Projects/gym-bro/src/models.py` (204 LOC)

### Core Workout Models

#### Set
```python
class Set(BaseModel):
    """A single set within an exercise."""
    reps: int
    weight_lbs: float | None = None
    rpe: int | None = Field(None, ge=1, le=10)  # Rate of Perceived Exertion
    notes: str | None = None
```

---

#### Exercise
```python
class Exercise(BaseModel):
    """An exercise with its sets."""
    name: str
    sets: list[Set]
    notes: str | None = None
```

---

#### SupplementaryWork
```python
class SupplementaryWork(BaseModel):
    """Structured supplementary work (e.g., abs session)."""
    type: str  # "abs", "cardio", "stretching"
    template_id: str | None = None
    exercises: list[SupplementaryExercise] = []
    notes: str | None = None
```

**Migration Note**: Old format was `list[str]` (e.g., `["abs"]`). New format is `list[SupplementaryWork]`. Migration handled in `data.py`.

---

#### Warmup
```python
class Warmup(BaseModel):
    """Warmup activity before workout."""
    type: str  # "jog", "incline walk", "bike"
    duration_min: float | None = None
    distance_miles: float | None = None
    notes: str | None = None
```

---

#### WorkoutLog
```python
WorkoutType = Literal["Push", "Pull", "Legs", "Upper", "Lower",
                      "Class", "Cardio", "Active Recovery", "Other"]

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
    created_at: datetime

    # Supplementary work
    supplementary_work: list[SupplementaryWork] | list[str] | None = None

    # Session tracking (plan vs actual)
    session_id: str | None = None
    suggested_type: str | None = None
    planned_template_id: str | None = None
    plan_adjustments: list[dict] | None = None
    deviations_detected: list[dict] | None = None
    equipment_unavailable: list[str] | None = None

    # Soft delete (30-day recovery window)
    deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: str = "user"
```

---

### Template Models

#### TemplateExercise
```python
class TemplateExercise(BaseModel):
    """An exercise in a workout template."""
    name: str
    target_sets: int
    target_reps: int | str  # Can be "8-12" or "max"
    rest_seconds: int = 90
    notes: str | None = None
```

---

#### WorkoutTemplate
```python
class WorkoutTemplate(BaseModel):
    """A workout template/plan."""
    id: str
    name: str
    type: WorkoutType
    exercises: list[TemplateExercise]
    supersets: list[Superset] = []
    notes: str | None = None

    # Adaptive templates
    mode: Literal["static", "adaptive"] = "static"
    generated_from_history: bool = False
    adaptations: list[str] | None = None
```

---

### Weekly Split Models

#### WeeklySplit
```python
class WeeklySplit(BaseModel):
    """Weekly workout split tracking."""
    config: WeeklySplitConfig
    current_week: CurrentWeek

class WeeklySplitConfig(BaseModel):
    """Split configuration."""
    types: list[str]  # ["Push", "Pull", "Legs", "Upper", "Lower"]
    rotation: list[str]
    weekly_targets: dict[str, int]  # {"Push": 1, "Pull": 1, "Legs": 2, ...}

class CurrentWeek(BaseModel):
    """Current week status."""
    start_date: date
    completed: dict[str, int]  # {"Push": 1, "Pull": 0, ...}
    next_in_rotation: str
```

---

### Other Models

#### ClassifiedIntent
```python
class ClassifiedIntent(BaseModel):
    """Result of intent classification."""
    intent: Intent  # "log", "query", "recommend", "chat", "admin"
    confidence: float
    reasoning: str
```

#### ProgressionStats
```python
class ProgressionStats(BaseModel):
    """Exercise progression statistics."""
    exercise: str
    trend: str  # "increasing", "stable", "decreasing", "insufficient_data"
    first_weight: float | None
    current_weight: float | None
    max_weight: float | None
    total_sessions: int
    avg_weekly_increase: float | None
```

---

## JSON File Schemas

Located in `/Users/franklindickinson/Projects/gym-bro/data/`

### workout_logs.json
```json
{
  "logs": [
    {
      "id": "2024-01-15-001",
      "date": "2024-01-15",
      "type": "Push",
      "template_id": "push_a",
      "exercises": [
        {
          "name": "Dumbbell Bench Press",
          "sets": [
            {"reps": 8, "weight_lbs": 45, "rpe": 7},
            {"reps": 8, "weight_lbs": 45, "rpe": 8}
          ],
          "notes": "Felt strong"
        }
      ],
      "warmup": {
        "type": "jog",
        "duration_min": 10,
        "distance_miles": 1.0
      },
      "supplementary_work": [
        {
          "type": "abs",
          "exercises": [
            {
              "name": "Plank",
              "sets": [{"reps": 1, "notes": "60 seconds"}]
            }
          ]
        }
      ],
      "notes": "Great workout",
      "completed": true,
      "created_at": "2024-01-15T18:30:00Z",
      "deleted": false
    }
  ]
}
```

---

### templates.json
```json
{
  "templates": [
    {
      "id": "push_a",
      "name": "Push Day A",
      "type": "Push",
      "exercises": [
        {
          "name": "Dumbbell Incline Bench Press",
          "target_sets": 4,
          "target_reps": 8,
          "rest_seconds": 90,
          "notes": "Focus on chest squeeze"
        }
      ],
      "supersets": [
        {
          "exercises": ["Cable Fly", "Push Ups"],
          "rounds": 3,
          "rest_seconds": 60
        }
      ],
      "mode": "static"
    }
  ]
}
```

---

### weekly_split.json
```json
{
  "config": {
    "types": ["Push", "Pull", "Legs", "Upper", "Lower"],
    "rotation": ["Push", "Pull", "Legs", "Upper", "Lower", "Legs"],
    "weekly_targets": {
      "Push": 1,
      "Pull": 1,
      "Legs": 2,
      "Upper": 1,
      "Lower": 1
    },
    "supplementary_targets": {
      "abs": 2
    }
  },
  "current_week": {
    "start_date": "2024-12-16",
    "completed": {
      "Push": 1,
      "Pull": 1,
      "Legs": 0
    },
    "next_in_rotation": "Legs"
  }
}
```

---

### exercises.json
```json
{
  "exercises": [
    {
      "name": "Dumbbell Bench Press",
      "primary_muscle": "Chest",
      "secondary_muscles": ["Triceps", "Shoulders"],
      "equipment": ["dumbbells"],
      "variations": [
        "Dumbbell Incline Bench Press",
        "Dumbbell Decline Bench Press"
      ]
    }
  ]
}
```

---

## Data Layer Operations

**File**: `/Users/franklindickinson/Projects/gym-bro/src/data.py` (635 LOC)

### Workout Log Operations

```python
# Read
get_all_logs(include_deleted=False) -> list[dict]
get_logs_by_date_range(start: date, end: date) -> list[dict]
get_logs_by_exercise(exercise_name: str) -> list[dict]
get_log_by_id(log_id: str) -> dict | None

# Write
add_log(log: dict) -> str  # Returns log_id
update_log(log_id: str, updates: dict) -> bool

# Soft Delete (30-day recovery)
delete_log(log_id: str) -> bool
restore_log(log_id: str) -> bool
cleanup_old_deleted_logs(days_threshold: int = 30) -> int
```

---

### Template Operations

```python
get_template(template_id: str) -> dict | None
get_all_templates() -> list[dict]
get_templates_by_type(workout_type: str) -> list[dict]
add_template(template: dict) -> str
```

---

### Weekly Split Operations

```python
get_weekly_split() -> dict
update_weekly_split(split: dict) -> bool
reset_weekly_split() -> bool  # Called on Monday
```

---

### Supplementary Work Operations

```python
get_supplementary_status(type: str = "abs") -> dict
can_do_supplementary_today(type: str = "abs") -> bool
```

**Returns**:
```json
{
  "type": "abs",
  "count": 1,
  "target": 2,
  "last_date": "2024-12-15",
  "can_do_today": true,
  "reason": "Last abs workout was 2 days ago"
}
```

---

### Exercise History

```python
get_exercise_history(exercise: str, days: int = 90) -> list[dict]
```

**Returns**:
```json
[
  {
    "date": "2024-12-15",
    "sets": [
      {"reps": 8, "weight_lbs": 135},
      {"reps": 7, "weight_lbs": 135}
    ],
    "workout_type": "Push",
    "log_id": "2024-12-15-001"
  }
]
```

---

### Stats Operations

```python
get_workout_count(days: int = 30, workout_type: str | None = None) -> int
get_last_workout_by_type(workout_type: str) -> dict | None
```

---

## Migration Patterns

### Supplementary Work Migration

**Old Format** (before Phase 5):
```json
{
  "supplementary_work": ["abs", "cardio"]
}
```

**New Format** (Phase 5+):
```json
{
  "supplementary_work": [
    {
      "type": "abs",
      "exercises": [
        {
          "name": "Plank",
          "sets": [{"reps": 1, "notes": "60 seconds"}]
        }
      ]
    }
  ]
}
```

**Migration**: Handled automatically in `data.py:_migrate_supplementary_work()`

When reading old logs:
- Detects `list[str]` format
- Converts to `list[SupplementaryWork]`
- Preserves type information
- Saves back in new format

---

### Soft Delete Migration

**Phase 7** added soft delete with 30-day recovery:
- Added `deleted`, `deleted_at`, `deleted_by` fields
- Old logs default to `deleted=False`
- Cleanup job runs daily to remove logs older than 30 days

---

## Data Access Patterns

### Reading Workout Logs
```python
from src.data import get_all_logs, get_logs_by_date_range

# Get all active logs
logs = get_all_logs(include_deleted=False)

# Get logs in date range
from datetime import date, timedelta
end = date.today()
start = end - timedelta(days=30)
recent_logs = get_logs_by_date_range(start, end)
```

---

### Creating a Workout Log
```python
from src.data import add_log
from datetime import date

log = {
    "date": date.today().isoformat(),
    "type": "Push",
    "exercises": [
        {
            "name": "Bench Press",
            "sets": [
                {"reps": 8, "weight_lbs": 135}
            ]
        }
    ],
    "completed": True
}

log_id = add_log(log)  # Returns generated ID like "2024-12-20-001"
```

---

### Querying Exercise History
```python
from src.data import get_exercise_history

# Get bench press history for last 90 days
history = get_exercise_history("bench press", days=90)

for session in history:
    print(f"{session['date']}: {session['sets']}")
```

---

## File Locations

**Data Files**:
- `/Users/franklindickinson/Projects/gym-bro/data/workout_logs.json`
- `/Users/franklindickinson/Projects/gym-bro/data/templates.json`
- `/Users/franklindickinson/Projects/gym-bro/data/weekly_split.json`
- `/Users/franklindickinson/Projects/gym-bro/data/exercises.json`

**Code Files**:
- `/Users/franklindickinson/Projects/gym-bro/src/data.py` - CRUD operations (635 LOC)
- `/Users/franklindickinson/Projects/gym-bro/src/models.py` - Pydantic models (204 LOC)

---

## Best Practices

1. **Always use data.py functions** - Don't read JSON directly
2. **Validate with Pydantic** - Use models for type safety
3. **Handle migrations** - Old formats are auto-converted
4. **Respect soft delete** - Use `include_deleted=False` by default
5. **Use date ranges** - Don't load all logs unnecessarily
6. **Fuzzy match exercises** - `data.py` normalizes exercise names
