"""
Data layer for reading/writing workout data.

Migrated from JSON files to Supabase (Postgres) for persistent cloud storage.
All function signatures remain unchanged for backward compatibility.
"""

from datetime import datetime, date, timedelta
from typing import Optional
from src.database import get_supabase_client


def migrate_supplementary_work(log: dict) -> dict:
    """
    Migrate old supplementary_work format to new structured format.

    OLD: supplementary_work: ["abs"]  (just a flag)
    NEW: supplementary_work: [{"type": "abs", "template_id": null, "exercises": [], "notes": null}]

    Args:
        log: Workout log dict (may be old or new format)

    Returns:
        Migrated log dict
    """
    supp_work = log.get('supplementary_work')

    # No supplementary work, nothing to migrate
    if supp_work is None:
        return log

    # Empty list, nothing to migrate
    if not supp_work:
        return log

    # Check if already new format (list of dicts with 'type' key)
    if isinstance(supp_work[0], dict) and 'type' in supp_work[0]:
        return log  # Already migrated

    # Old format: list of strings like ["abs"]
    if isinstance(supp_work[0], str):
        migrated = []
        for supp_type in supp_work:
            migrated.append({
                "type": supp_type,
                "template_id": None,
                "exercises": [],  # No exercise data in old format
                "notes": "Migrated from legacy format"
            })
        log['supplementary_work'] = migrated

    return log


# ============================================================================
# Workout Logs
# ============================================================================

def get_all_logs(include_deleted: bool = False) -> list:
    """
    Get all workout logs.

    Args:
        include_deleted: If True, include deleted logs. Default False (exclude deleted).

    Returns:
        List of workout logs
    """
    sb = get_supabase_client()

    query = sb.table("workout_logs").select("*").order("date", desc=True)
    if not include_deleted:
        query = query.eq("deleted", False)

    result = query.execute()
    logs = result.data

    # Migrate supplementary_work field from old format to new
    logs = [migrate_supplementary_work(log) for log in logs]

    return logs


def get_logs_by_date_range(start: date, end: date, include_deleted: bool = False) -> list:
    """
    Get logs within a date range.

    Args:
        start: Start date (inclusive)
        end: End date (inclusive)
        include_deleted: If True, include deleted logs. Default False.

    Returns:
        List of workout logs in date range
    """
    sb = get_supabase_client()

    query = sb.table("workout_logs").select("*") \
        .gte("date", start.isoformat()) \
        .lte("date", end.isoformat()) \
        .order("date", desc=True)

    if not include_deleted:
        query = query.eq("deleted", False)

    result = query.execute()
    logs = result.data

    # Migrate supplementary_work field
    logs = [migrate_supplementary_work(log) for log in logs]

    return logs


def get_logs_by_exercise(exercise_name: str, include_deleted: bool = False) -> list:
    """
    Get all logs containing a specific exercise.

    Args:
        exercise_name: Name of exercise to search for
        include_deleted: If True, include deleted logs. Default False.

    Returns:
        List of workout logs containing the exercise
    """
    # Get all logs and filter in-memory for now
    # Could optimize with JSONB containment queries in future
    logs = get_all_logs(include_deleted=include_deleted)

    results = []
    for log in logs:
        for exercise in log.get("exercises", []):
            if exercise_name.lower() in exercise.get("name", "").lower():
                results.append(log)
                break

    return results


def add_log(log: dict) -> str:
    """
    Add a new workout log. Returns the log ID.

    Raises:
        ValueError: If workout log is missing required 'type' field
    """
    # VALIDATION: Ensure workout type is present (critical for weekly split tracking)
    workout_type = log.get("type")
    if not workout_type or workout_type == "":
        raise ValueError(
            "Cannot save workout without a type. "
            "This is a system error - workout type should be set before calling add_log(). "
            f"Log data: {log.get('id', 'unknown')} with {len(log.get('exercises', []))} exercises"
        )

    # Migrate supplementary_work if needed (handles both old and new format)
    log = migrate_supplementary_work(log)

    sb = get_supabase_client()

    # Generate ID if not present
    if "id" not in log:
        date_str = log.get("date", date.today().isoformat())
        # Query existing logs for this date to get count
        existing = sb.table("workout_logs") \
            .select("id") \
            .eq("date", date_str) \
            .execute()
        count = len(existing.data) + 1
        log["id"] = f"{date_str}-{count:03d}"

    # Ensure created_at is set
    if "created_at" not in log:
        log["created_at"] = datetime.now().isoformat()

    # Insert into database
    sb.table("workout_logs").insert(log).execute()

    # Update weekly split tracking
    _update_weekly_split_after_log(log)

    return log["id"]


def update_log(log_id: str, updates: dict) -> bool:
    """Update an existing log."""
    sb = get_supabase_client()

    result = sb.table("workout_logs") \
        .update(updates) \
        .eq("id", log_id) \
        .execute()

    return len(result.data) > 0


def delete_log(log_id: str) -> bool:
    """
    Soft delete a log by ID.

    Sets deleted=True and deleted_at timestamp.
    Log is hidden from normal queries but recoverable for 30 days.

    Args:
        log_id: ID of the workout log to delete

    Returns:
        True if successful, False if log not found
    """
    sb = get_supabase_client()

    result = sb.table("workout_logs") \
        .update({
            "deleted": True,
            "deleted_at": datetime.now().isoformat()
        }) \
        .eq("id", log_id) \
        .execute()

    return len(result.data) > 0


def restore_log(log_id: str) -> bool:
    """
    Restore a soft-deleted log.

    Clears deleted flag and deleted_at timestamp.

    Args:
        log_id: ID of the workout log to restore

    Returns:
        True if successful, False if log not found or not deleted
    """
    sb = get_supabase_client()

    # First check if log exists and is deleted
    check = sb.table("workout_logs") \
        .select("deleted") \
        .eq("id", log_id) \
        .execute()

    if not check.data or not check.data[0].get("deleted", False):
        return False  # Log not found or not deleted

    # Restore the log
    result = sb.table("workout_logs") \
        .update({
            "deleted": False,
            "deleted_at": None
        }) \
        .eq("id", log_id) \
        .execute()

    return len(result.data) > 0


def delete_log_permanent(log_id: str) -> bool:
    """
    Permanently delete a log (hard delete).

    WARNING: This is irreversible! Use with caution.
    Typically only called by cleanup job for 30+ day old deleted logs.

    Args:
        log_id: ID of the workout log to permanently delete

    Returns:
        True if successful, False if log not found
    """
    sb = get_supabase_client()

    result = sb.table("workout_logs") \
        .delete() \
        .eq("id", log_id) \
        .execute()

    return len(result.data) > 0


def bulk_delete_logs(log_ids: list[str]) -> dict:
    """
    Soft delete multiple logs at once.

    Args:
        log_ids: List of log IDs to delete

    Returns:
        Dict with success count and failed IDs
    """
    deleted_count = 0
    failed_ids = []

    for log_id in log_ids:
        try:
            if delete_log(log_id):
                deleted_count += 1
            else:
                failed_ids.append(log_id)
        except Exception:
            failed_ids.append(log_id)

    return {
        "deleted_count": deleted_count,
        "failed_ids": failed_ids,
        "total_attempted": len(log_ids)
    }


def get_deleted_logs() -> list:
    """
    Get all soft-deleted logs.

    Returns logs where deleted=True, sorted by deletion date (most recent first).
    Useful for undo UI and cleanup jobs.

    Returns:
        List of deleted workout logs
    """
    sb = get_supabase_client()

    result = sb.table("workout_logs") \
        .select("*") \
        .eq("deleted", True) \
        .order("deleted_at", desc=True) \
        .execute()

    return result.data


def cleanup_old_deleted_logs(days_threshold: int = 30) -> dict:
    """
    Permanently delete logs that have been soft-deleted for more than threshold days.

    Args:
        days_threshold: Number of days to keep deleted logs (default 30)

    Returns:
        Dict with cleanup stats (deleted_count, ids, cutoff_date)
    """
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    deleted_logs = get_deleted_logs()

    to_delete = []
    for log in deleted_logs:
        deleted_at_str = log.get("deleted_at")
        if deleted_at_str:
            try:
                deleted_at = datetime.fromisoformat(deleted_at_str)
                if deleted_at < cutoff_date:
                    to_delete.append(log.get("id"))
            except ValueError:
                continue

    # Permanently delete old logs
    deleted_count = 0
    for log_id in to_delete:
        if delete_log_permanent(log_id):
            deleted_count += 1

    return {
        "deleted_count": deleted_count,
        "deleted_ids": to_delete,
        "cutoff_date": cutoff_date.isoformat()
    }


# ============================================================================
# Templates
# ============================================================================

def get_all_templates() -> list:
    """Get all workout templates."""
    sb = get_supabase_client()

    result = sb.table("templates") \
        .select("*") \
        .order("type") \
        .execute()

    return result.data


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
    sb = get_supabase_client()

    result = sb.table("exercises") \
        .select("*") \
        .order("canonical_name") \
        .execute()

    # Convert to old format for compatibility
    exercises = []
    for row in result.data:
        exercises.append({
            "canonical": row["canonical_name"],
            "variations": row.get("variations", []),
            "muscle_groups": row.get("muscle_groups", []),
            "equipment": row.get("equipment", [])
        })

    return exercises


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
    sb = get_supabase_client()

    # Get the latest weekly split row
    result = sb.table("weekly_split") \
        .select("*") \
        .order("id", desc=True) \
        .limit(1) \
        .execute()

    if not result.data:
        # Initialize with defaults
        data = {
            "config": DEFAULT_SPLIT_CONFIG,
            "current_week": {
                "start_date": _get_week_start().isoformat(),
                "completed": {},
                "next_in_rotation": "Push"
            }
        }
        # Insert default
        sb.table("weekly_split").insert(data).execute()
        return data

    row = result.data[0]
    return {
        "config": row["config"],
        "current_week": row["current_week"]
    }


def update_weekly_split(data: dict) -> None:
    """Update the weekly split data."""
    sb = get_supabase_client()

    # Get current row ID
    current = sb.table("weekly_split") \
        .select("id") \
        .order("id", desc=True) \
        .limit(1) \
        .execute()

    if current.data:
        # Update existing row
        row_id = current.data[0]["id"]
        sb.table("weekly_split") \
            .update({
                "config": data.get("config", DEFAULT_SPLIT_CONFIG),
                "current_week": data.get("current_week", {})
            }) \
            .eq("id", row_id) \
            .execute()
    else:
        # Insert new row
        sb.table("weekly_split").insert(data).execute()


def _get_week_start(for_date: Optional[date] = None) -> date:
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

        # Track supplementary work (e.g., abs)
        supplementary = log.get("supplementary_work", [])
        if supplementary and "abs" in supplementary:
            # Initialize supplementary_completed if not exists
            if "supplementary_completed" not in current:
                current["supplementary_completed"] = {}

            supp_completed = current["supplementary_completed"]

            # Initialize abs tracking if not exists
            if "abs" not in supp_completed:
                supp_completed["abs"] = {"count": 0, "dates": []}

            abs_data = supp_completed["abs"]

            # Add this date if not already counted
            if log_date_str not in abs_data["dates"]:
                abs_data["count"] += 1
                abs_data["dates"].append(log_date_str)

            supp_completed["abs"] = abs_data
            current["supplementary_completed"] = supp_completed

        split["current_week"] = current
        update_weekly_split(split)


def get_supplementary_status(supplementary_type: str = "abs") -> dict:
    """
    Get weekly completion status for supplementary work.

    Args:
        supplementary_type: Type of supplementary work (default: "abs")

    Returns:
        Dict with count, target, dates, and on_track status
    """
    split = get_weekly_split()
    current = split.get("current_week", {})
    config = split.get("config", {})

    supp_config = config.get("supplementary_work", {}).get(supplementary_type, {})
    supp_data = current.get("supplementary_completed", {}).get(supplementary_type, {})

    count = supp_data.get("count", 0)
    target = supp_config.get("weekly_target", 2)

    return {
        "type": supplementary_type,
        "count": count,
        "target": target,
        "dates": supp_data.get("dates", []),
        "min_spacing_days": supp_config.get("min_spacing_days", 1),
        "on_track": count >= target
    }


def can_do_supplementary_today(supplementary_type: str = "abs", target_date: Optional[date] = None) -> dict:
    """
    Check if supplementary work can be done on a given date based on spacing rules.

    Args:
        supplementary_type: Type of supplementary work (default: "abs")
        target_date: Date to check (default: today)

    Returns:
        Dict with can_do (bool) and reason (str)
    """
    if target_date is None:
        target_date = date.today()

    status = get_supplementary_status(supplementary_type)
    last_dates = status["dates"]
    min_spacing = status["min_spacing_days"]

    if not last_dates:
        return {"can_do": True, "reason": "No previous sessions this week"}

    # Check spacing from most recent session
    last_date = date.fromisoformat(max(last_dates))
    days_since = (target_date - last_date).days

    if days_since <= min_spacing:
        return {
            "can_do": False,
            "reason": f"Too soon (last session was {days_since} day(s) ago, minimum spacing: {min_spacing+1} days)"
        }

    return {"can_do": True, "reason": f"Ready ({days_since} days since last session)"}


# ============================================================================
# Stats
# ============================================================================

def get_workout_count(days: int = 30) -> int:
    """Get workout count for last N days."""
    end = date.today()
    start = end - timedelta(days=days)
    logs = get_logs_by_date_range(start, end)
    return len(logs)


def get_last_workout(include_deleted: bool = False) -> Optional[dict]:
    """
    Get the most recent workout.

    Args:
        include_deleted: If True, include deleted logs. Default False.

    Returns:
        Most recent workout log or None if no workouts exist
    """
    sb = get_supabase_client()

    query = sb.table("workout_logs") \
        .select("*") \
        .order("date", desc=True) \
        .limit(1)

    if not include_deleted:
        query = query.eq("deleted", False)

    result = query.execute()

    if not result.data:
        return None

    return result.data[0]


def get_exercise_history(exercise_name: str, days: int = 90) -> list:
    """
    Get weight/rep history for an exercise.

    Args:
        exercise_name: Name of exercise (partial match)
        days: Number of days to look back (0 = all time)

    Returns:
        List of exercise history with date, max_weight, sets
    """
    if days == 0:
        # Get all logs (no date filtering)
        logs = get_logs_by_exercise(exercise_name)
    else:
        # Filter by date range
        end = date.today()
        start = end - timedelta(days=days)
        all_logs = get_logs_by_exercise(exercise_name)

        logs = []
        for log in all_logs:
            log_date_str = log.get("date")
            if not log_date_str:
                continue
            try:
                log_date = date.fromisoformat(log_date_str)
                if log_date >= start:
                    logs.append(log)
            except ValueError:
                continue

    history = []

    for log in sorted(logs, key=lambda x: x.get("date", "")):
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
