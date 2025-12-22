"""
Data layer for reading/writing workout data.
"""
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"

def _load_json(filename: str) -> dict:
    """Load a JSON file from the data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def _save_json(filename: str, data: dict) -> None:
    """Save data to a JSON file."""
    filepath = DATA_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)

# ============================================================================
# Workout Logs
# ============================================================================

def get_all_logs() -> list:
    """Get all workout logs."""
    data = _load_json("workout_logs.json")
    return data.get("logs", [])

def get_logs_by_date_range(start: date, end: date) -> list:
    """Get logs within a date range."""
    logs = get_all_logs()
    results = []
    for log in logs:
        log_date_str = log.get("date")
        if not log_date_str:
            continue
        try:
            log_date = date.fromisoformat(log_date_str)
            if start <= log_date <= end:
                results.append(log)
        except ValueError:
            continue
    return results

def get_logs_by_exercise(exercise_name: str) -> list:
    """Get all logs containing a specific exercise."""
    logs = get_all_logs()
    results = []
    for log in logs:
        for exercise in log.get("exercises", []):
            if exercise_name.lower() in exercise.get("name", "").lower():
                results.append(log)
                break
    return results

def add_log(log: dict) -> str:
    """Add a new workout log. Returns the log ID."""
    data = _load_json("workout_logs.json")
    if "logs" not in data:
        data["logs"] = []
    
    # Generate ID if not present
    if "id" not in log:
        date_str = log.get("date", date.today().isoformat())
        count = len([l for l in data["logs"] if l.get("date") == date_str]) + 1
        log["id"] = f"{date_str}-{count:03d}"
    
    log["created_at"] = datetime.now().isoformat()
    data["logs"].append(log)
    _save_json("workout_logs.json", data)
    
    # Update weekly split tracking
    _update_weekly_split_after_log(log)
    
    return log["id"]

def update_log(log_id: str, updates: dict) -> bool:
    """Update an existing log."""
    data = _load_json("workout_logs.json")
    for i, log in enumerate(data.get("logs", [])):
        if log.get("id") == log_id:
            data["logs"][i].update(updates)
            _save_json("workout_logs.json", data)
            return True
    return False

def delete_log(log_id: str) -> bool:
    """Delete a log by ID."""
    data = _load_json("workout_logs.json")
    original_count = len(data.get("logs", []))
    data["logs"] = [l for l in data.get("logs", []) if l.get("id") != log_id]
    if len(data["logs"]) < original_count:
        _save_json("workout_logs.json", data)
        return True
    return False

# ============================================================================
# Templates
# ============================================================================

def get_all_templates() -> list:
    """Get all workout templates."""
    data = _load_json("templates.json")
    return data.get("templates", [])

def get_template(template_id: str) -> Optional[dict]:
    """Get a specific template by ID or type name."""
    templates = get_all_templates()
    template_id_lower = template_id.lower()
    
    for template in templates:
        # Match by ID
        if template.get("id", "").lower() == template_id_lower:
            return template
        # Match by type
        if template.get("type", "").lower() == template_id_lower:
            return template
        # Match by name
        if template_id_lower in template.get("name", "").lower():
            return template
    return None

# ============================================================================
# Exercises
# ============================================================================

def get_all_exercises() -> list:
    """Get all exercise definitions."""
    data = _load_json("exercises.json")
    return data.get("exercises", [])

def normalize_exercise_name(name: str) -> str:
    """Convert exercise name to canonical form."""
    exercises = get_all_exercises()
    name_lower = name.lower().strip()
    
    for exercise in exercises:
        if name_lower == exercise.get("canonical", "").lower():
            return exercise["canonical"]
        for variation in exercise.get("variations", []):
            if name_lower == variation.lower():
                return exercise["canonical"]
    
    # Not found, return as-is with title case
    return name.title()

# ============================================================================
# Weekly Split
# ============================================================================

DEFAULT_SPLIT_CONFIG = {
    "types": ["Push", "Pull", "Legs", "Upper", "Lower"],
    "rotation": ["Push", "Pull", "Legs", "Upper", "Lower", "Legs"],
    "weekly_targets": {
        "Push": 1,
        "Pull": 1,
        "Legs": 2,
        "Upper": 1,
        "Lower": 1
    }
}

def get_weekly_split() -> dict:
    """Get the weekly split configuration and current progress."""
    data = _load_json("weekly_split.json")
    
    # Ensure defaults exist
    if not data:
        data = {
            "config": DEFAULT_SPLIT_CONFIG,
            "current_week": {
                "start_date": _get_week_start().isoformat(),
                "completed": {},
                "next_in_rotation": "Push"
            }
        }
        _save_json("weekly_split.json", data)
    
    return data

def update_weekly_split(data: dict) -> None:
    """Update the weekly split data."""
    _save_json("weekly_split.json", data)

def _get_week_start(for_date: date = None) -> date:
    """Get the Monday of the week for a given date."""
    if for_date is None:
        for_date = date.today()
    return for_date - timedelta(days=for_date.weekday())

def _update_weekly_split_after_log(log: dict) -> None:
    """Update weekly split tracking after a new log is added."""
    split = get_weekly_split()
    config = split.get("config", DEFAULT_SPLIT_CONFIG)
    current = split.get("current_week", {})
    
    log_date_str = log.get("date")
    if not log_date_str:
        return
        
    log_date = date.fromisoformat(log_date_str)
    log_type = log.get("type")
    
    if not log_type or log_type not in config.get("types", []):
        return
    
    # Check if this is the current week
    week_start = _get_week_start()
    if log_date >= week_start:
        # Update rotation pointer
        rotation = config.get("rotation", ["Push", "Pull", "Legs"])
        try:
            current_idx = rotation.index(log_type)
            next_idx = (current_idx + 1) % len(rotation)
            current["next_in_rotation"] = rotation[next_idx]
        except ValueError:
            pass
        
        split["current_week"] = current
        update_weekly_split(split)

# ============================================================================
# Stats
# ============================================================================

def get_workout_count(days: int = 30) -> int:
    """Get workout count for last N days."""
    end = date.today()
    start = end - timedelta(days=days)
    logs = get_logs_by_date_range(start, end)
    return len(logs)

def get_last_workout() -> Optional[dict]:
    """Get the most recent workout."""
    logs = get_all_logs()
    if not logs:
        return None
    return max(logs, key=lambda x: x.get("date", ""))

def get_exercise_history(exercise_name: str, days: int = 90) -> list:
    """Get weight/rep history for an exercise."""
    end = date.today()
    start = end - timedelta(days=days)
    
    logs = get_logs_by_exercise(exercise_name)
    history = []
    
    for log in sorted(logs, key=lambda x: x.get("date", "")):
        log_date_str = log.get("date")
        if not log_date_str:
            continue
        try:
            log_date = date.fromisoformat(log_date_str)
            if log_date < start:
                continue
        except ValueError:
            continue
            
        for exercise in log.get("exercises", []):
            if exercise_name.lower() in exercise.get("name", "").lower():
                sets = exercise.get("sets", [])
                max_weight = max(
                    (s.get("weight_lbs", 0) for s in sets if s.get("weight_lbs")),
                    default=0
                )
                history.append({
                    "date": log["date"],
                    "exercise": exercise["name"],
                    "max_weight": max_weight,
                    "sets": sets
                })
    
    return history
