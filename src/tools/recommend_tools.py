"""
Recommend Tools - Tools for workout recommendations and planning.

These tools are used by the Recommend Agent (ReAct) to suggest workouts,
track weekly split completion, and plan training.
"""

from datetime import date, timedelta
from langchain_core.tools import tool
from src.data import (
    get_all_logs,
    get_logs_by_date_range,
    get_template,
    get_all_templates,
    get_weekly_split,
    update_weekly_split,
    get_supplementary_status,
    can_do_supplementary_today
)


@tool
def get_weekly_split_status() -> dict:
    """
    Get current week's workout completion status by type.
    
    Returns:
        Dict with completed counts, targets, remaining, and next suggested workout
    """
    split = get_weekly_split()
    config = split.get("config", {})
    current = split.get("current_week", {})
    
    # Get this week's date range
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)  # Sunday
    
    # Check if we need to reset the week
    stored_start = current.get("start_date")
    if stored_start:
        stored_start_date = date.fromisoformat(stored_start)
        if stored_start_date < week_start:
            # New week - reset
            current = {
                "start_date": week_start.isoformat(),
                "completed": {},
                "next_in_rotation": config.get("rotation", ["Push"])[0]
            }
            update_weekly_split({"config": config, "current_week": current})
    
    # Get workouts from this week
    logs = get_logs_by_date_range(week_start, today)
    
    # Count by type
    completed = {}
    for log in logs:
        t = log.get("type", "Other")
        if t in config.get("types", []):
            completed[t] = completed.get(t, 0) + 1
    
    # Calculate remaining
    targets = config.get("weekly_targets", {})
    remaining = {}
    for t, target in targets.items():
        done = completed.get(t, 0)
        remaining[t] = max(0, target - done)
    
    # Determine next suggested
    rotation = config.get("rotation", ["Push", "Pull", "Legs"])
    next_suggested = current.get("next_in_rotation", rotation[0])
    
    # If next_suggested is complete for the week, find next incomplete
    while remaining.get(next_suggested, 0) == 0:
        try:
            idx = rotation.index(next_suggested)
            next_idx = (idx + 1) % len(rotation)
            next_suggested = rotation[next_idx]
            # Prevent infinite loop
            if next_suggested == current.get("next_in_rotation"):
                break
        except ValueError:
            break
    
    days_left = (week_end - today).days + 1

    # Add supplementary work status
    abs_status = get_supplementary_status("abs")

    return {
        "week_start": week_start.isoformat(),
        "completed": completed,
        "targets": targets,
        "remaining": remaining,
        "next_suggested": next_suggested,
        "days_left_in_week": days_left,
        "summary": _generate_split_summary(completed, targets, remaining),
        "supplementary": {
            "abs": {
                "count": abs_status["count"],
                "target": abs_status["target"],
                "on_track": abs_status["on_track"]
            }
        }
    }


def _group_workouts_into_combos(needed_types: list[str], days_left: int) -> list[dict]:
    """
    Group workouts into realistic daily combos for catch-up mode.

    Pairing Strategy:
    - Legs + Upper (non-overlapping muscle groups)
    - Push + Lower (chest/shoulders + legs)
    - Pull + Legs (back/biceps + legs)
    - Standalone if only 1 workout remaining

    Args:
        needed_types: List of workout types to complete (e.g., ["Legs", "Push", "Upper"])
        days_left: Days remaining in week

    Returns:
        List of combo dicts:
        [
            {
                "day": "Today",
                "types": ["Legs", "Upper"],
                "duration_min": 70,
                "rest_between_min": 5
            },
            {
                "day": "Tomorrow",
                "types": ["Push"],
                "duration_min": 35
            }
        ]
    """
    # Pairing preferences (complementary muscle groups)
    pairings = {
        "Legs": ["Upper"],  # Legs + Upper body
        "Upper": ["Legs"],
        "Push": ["Lower", "Legs"],  # Push + Legs variations
        "Pull": ["Lower", "Legs"],  # Pull + Legs variations
        "Lower": ["Push", "Pull"]
    }

    combos = []
    remaining = needed_types.copy()
    day_labels = ["Today", "Tomorrow"] + [f"Day {i}" for i in range(3, 8)]

    day_idx = 0

    while remaining and day_idx < days_left:
        if len(remaining) == 1:
            # Single workout remaining
            combos.append({
                "day": day_labels[day_idx],
                "types": [remaining[0]],
                "duration_min": 35,  # Express mode default
                "rest_between_min": 0
            })
            remaining = []
        else:
            # Try to pair first workout with complementary type
            first = remaining[0]
            paired = False

            for preferred_pair in pairings.get(first, []):
                if preferred_pair in remaining:
                    # Found a pair!
                    combos.append({
                        "day": day_labels[day_idx],
                        "types": [first, preferred_pair],
                        "duration_min": 70,  # 2 x 35 min express
                        "rest_between_min": 5
                    })
                    remaining.remove(first)
                    remaining.remove(preferred_pair)
                    paired = True
                    break

            if not paired:
                # No good pair found - do first workout solo
                combos.append({
                    "day": day_labels[day_idx],
                    "types": [first],
                    "duration_min": 35,
                    "rest_between_min": 0
                })
                remaining.remove(first)

        day_idx += 1

    # If more workouts than days, add overflow to last day
    if remaining:
        if combos:
            combos[-1]["types"].extend(remaining)
            combos[-1]["duration_min"] += len(remaining) * 35
        else:
            # Edge case: no combos created yet
            combos.append({
                "day": "Today",
                "types": remaining,
                "duration_min": len(remaining) * 35,
                "rest_between_min": 5 if len(remaining) > 1 else 0
            })

    return combos


@tool
def suggest_next_workout() -> dict:
    """
    Suggest the next workout based on rotation and weekly progress.

    NEW: Includes catch-up mode detection when multiple workouts needed with limited time.
    Returns smart workout combos for catch-up mode.

    Returns:
        Suggested workout type with reasoning, plus catch-up mode info if applicable
    """
    status = get_weekly_split_status.invoke({})

    suggested = status.get("next_suggested", "Push")
    remaining = status.get("remaining", {})
    days_left = status.get("days_left_in_week", 7)

    # NEW: Calculate total workouts needed
    total_remaining = sum(remaining.values())

    # NEW: Catch-up mode detection
    catch_up_mode = total_remaining > days_left and days_left > 0

    if catch_up_mode:
        # Get all workout types that need to be done
        needed_types = [t for t, count in remaining.items() if count > 0]

        # Sort needed types to prioritize the suggested one first
        if suggested in needed_types:
            needed_types.remove(suggested)
            needed_types.insert(0, suggested)

        # NEW: Group into smart combos
        combos = _group_workouts_into_combos(needed_types, days_left)

        # First combo for today
        today_combo = combos[0]
        first_type_today = today_combo["types"][0]

        # Get template if available (for backward compatibility)
        template = get_template(first_type_today.lower())
        template_id = template.get("id") if template else None
        template_name = template.get("name") if template else None

        return {
            "suggested_type": first_type_today,  # First type in today's combo
            "reason": f"Catch-up mode: {total_remaining} workouts needed in {days_left} day(s)",
            "template_id": template_id,
            "template_name": template_name,
            "weekly_status": status,
            "catch_up_mode": True,
            "catch_up_combos": combos,  # NEW: Structured combos instead of flat list
            "catch_up_workouts": needed_types,  # Keep for backward compatibility
            "catch_up_count": total_remaining,
            "express_recommended": True,
            "days_left_in_week": days_left
        }

    # Normal mode (existing logic)
    reasons = []

    # Check if behind on this type
    if remaining.get(suggested, 0) > 0:
        reasons.append(f"{suggested} is next in rotation")
        if remaining[suggested] > 1:
            reasons.append(f"You have {remaining[suggested]} more {suggested} workouts to hit your target")

    # Check if any types are critically behind
    urgent = []
    for t, count in remaining.items():
        if count > 0 and count >= days_left:
            urgent.append(t)

    if urgent and suggested not in urgent:
        reasons.append(f"Consider prioritizing: {', '.join(urgent)}")

    # Get template if available
    template = get_template(suggested.lower())
    template_id = template.get("id") if template else None
    template_name = template.get("name") if template else None

    return {
        "suggested_type": suggested,
        "reason": " | ".join(reasons) if reasons else "Next in standard rotation",
        "template_id": template_id,
        "template_name": template_name,
        "weekly_status": status,
        "catch_up_mode": False
    }


@tool
def get_last_workout_by_type(workout_type: str) -> dict:
    """
    Get the most recent workout of a specific type.
    
    Args:
        workout_type: The type of workout (Push, Pull, Legs, etc.)
    
    Returns:
        The most recent workout of that type, or None if not found
    """
    logs = get_all_logs()
    
    # Filter by type and sort by date descending
    typed_logs = [
        l for l in logs 
        if l.get("type", "").lower() == workout_type.lower()
    ]
    
    if not typed_logs:
        return {
            "found": False,
            "type": workout_type,
            "message": f"No {workout_type} workouts found"
        }
    
    # Sort by date descending
    typed_logs.sort(key=lambda x: x.get("date", ""), reverse=True)
    last = typed_logs[0]
    
    # Calculate days since
    last_date = date.fromisoformat(last.get("date"))
    days_since = (date.today() - last_date).days
    
    return {
        "found": True,
        "date": last.get("date"),
        "days_since": days_since,
        "exercises": [ex.get("name") for ex in last.get("exercises", [])],
        "notes": last.get("notes")
    }


@tool
def check_muscle_balance() -> dict:
    """
    Analyze if any muscle groups are being under or over trained.
    
    Returns:
        Balance report with counts and recommendations
    """
    # Look at last 14 days
    end_date = date.today()
    start_date = end_date - timedelta(days=14)
    logs = get_logs_by_date_range(start_date, end_date)
    
    # Count by type
    counts = {}
    for log in logs:
        t = log.get("type", "Other")
        counts[t] = counts.get(t, 0) + 1
    
    # Analyze balance
    total = sum(counts.values())
    issues = []
    
    if total == 0:
        return {
            "period_days": 14,
            "total_workouts": 0,
            "balance": "No data - no workouts in last 14 days",
            "recommendation": "Any workout is a good workout!"
        }
    
    # Check for imbalances
    push = counts.get("Push", 0) + counts.get("Upper", 0) * 0.5
    pull = counts.get("Pull", 0) + counts.get("Upper", 0) * 0.5
    legs = counts.get("Legs", 0) + counts.get("Lower", 0)
    
    if push > pull * 1.5:
        issues.append("More pushing than pulling - add more back work")
    elif pull > push * 1.5:
        issues.append("More pulling than pushing - add more chest/shoulder work")
    
    if legs < (push + pull) * 0.3:
        issues.append("Legs are undertrained relative to upper body")
    
    balance = "balanced" if not issues else "imbalanced"
    
    return {
        "period_days": 14,
        "total_workouts": total,
        "by_type": counts,
        "balance": balance,
        "issues": issues,
        "recommendation": issues[0] if issues else "Keep up the good balance!"
    }


@tool 
def get_workout_template(workout_type: str, adaptive: bool = True) -> dict:
    """
    Get the workout template for a given type.

    NEW: Now supports adaptive template generation based on training history!

    Args:
        workout_type: The type of workout (Push, Pull, Legs, etc.)
        adaptive: Use adaptive templates (default: True). Set to False for static templates.

    Returns:
        Template with exercises, sets, reps, and (if adaptive) personalized weights and coaching notes.
        Includes "mode" field: "adaptive", "static", or "error"
    """
    from src.agents.template_generator import generate_adaptive_template
    from datetime import date, timedelta

    # Check if user has enough history for adaptive templates
    workout_count = 0
    if adaptive:
        # Count recent workouts to ensure there's enough data
        try:
            from src.data import get_all_logs
            logs = get_all_logs()
            # Filter for this workout type
            type_logs = [log for log in logs if log.get('type') == workout_type]
            workout_count = len(type_logs)
        except Exception:
            workout_count = 0

    # Try adaptive template if enabled and enough data exists
    if adaptive and workout_count >= 5:
        try:
            template = generate_adaptive_template(workout_type)
            if not template.get("error"):
                template["found"] = True
                return template
        except Exception as e:
            # Fallback to static if adaptive generation fails
            print(f"Adaptive template generation failed: {e}")

    # Fallback: Static template
    template = get_template(workout_type.lower())

    if not template:
        # Try to find a template that contains this type
        all_templates = get_all_templates()
        for t in all_templates:
            if workout_type.lower() in t.get("type", "").lower():
                template = t
                break

    if not template:
        return {
            "found": False,
            "type": workout_type,
            "message": f"No template found for {workout_type}",
            "mode": "error"
        }

    return {
        "found": True,
        "id": template.get("id"),
        "name": template.get("name"),
        "type": template.get("type"),
        "exercises": template.get("exercises", []),
        "supersets": template.get("supersets", []),
        "notes": template.get("notes"),
        "mode": "static"
    }


@tool
def get_abs_status() -> dict:
    """
    Get current week's ab workout completion status.

    Returns status including count, target, dates, and whether abs can be done today.
    Useful for making recommendations about when to include abs.

    Returns:
        dict: {
            "count": int,           # Number of ab sessions this week
            "target": int,          # Weekly target (usually 2)
            "dates": list[str],     # Dates abs were completed
            "can_do_today": bool,   # Whether abs can be done today (spacing check)
            "days_since_last": int, # Days since last ab session
            "on_track": bool,       # Whether weekly target is being met
            "behind": bool          # Whether behind on weekly target
        }
    """
    status = get_supplementary_status("abs")
    can_do = can_do_supplementary_today("abs", date.today())

    # Calculate days since last ab session
    last_dates = status["dates"]
    if last_dates:
        last_date = date.fromisoformat(max(last_dates))
        days_since = (date.today() - last_date).days
    else:
        days_since = 999  # No previous sessions

    return {
        "count": status["count"],
        "target": status["target"],
        "dates": status["dates"],
        "can_do_today": can_do["can_do"],
        "spacing_reason": can_do["reason"],
        "days_since_last": days_since,
        "on_track": status["on_track"],
        "behind": status["count"] < status["target"]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_split_summary(completed: dict, targets: dict, remaining: dict) -> str:
    """Generate a human-readable weekly split summary."""
    parts = []
    
    for t, target in targets.items():
        done = completed.get(t, 0)
        if done >= target:
            parts.append(f"{t}: ✓ {done}/{target}")
        else:
            parts.append(f"{t}: {done}/{target}")
    
    return " | ".join(parts)


# Export all tools for the agent
RECOMMEND_TOOLS = [
    get_weekly_split_status,
    suggest_next_workout,
    get_last_workout_by_type,
    check_muscle_balance,
    get_workout_template,
    get_abs_status
]
