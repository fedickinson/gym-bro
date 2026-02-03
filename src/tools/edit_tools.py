"""
Edit Tools - Tools for modifying historical workout data.

These tools are used by the Chat Agent to handle user requests to edit
past workout entries (weights, reps, etc.).
"""

from datetime import date, timedelta
from typing import Optional, Union
from langchain_core.tools import tool
from src.data import get_logs_by_date_range
import re


def parse_date_fuzzy(date_str: str) -> Optional[date]:
    """
    Parse fuzzy date strings like 'last Tuesday', 'Jan 15', '3 days ago'.

    Args:
        date_str: Natural language date string

    Returns:
        date object or None if can't parse
    """
    date_str_lower = date_str.lower().strip()
    today = date.today()

    # "today"
    if date_str_lower in ["today"]:
        return today

    # "yesterday"
    if date_str_lower in ["yesterday"]:
        return today - timedelta(days=1)

    # "X days ago"
    match = re.match(r"(\d+)\s*days?\s*ago", date_str_lower)
    if match:
        days = int(match.group(1))
        return today - timedelta(days=days)

    # "last Monday/Tuesday/etc"
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day_name in enumerate(weekdays):
        if f"last {day_name}" in date_str_lower:
            # Calculate days back to that weekday
            current_weekday = today.weekday()
            target_weekday = i

            # If today is Wednesday (2) and we want last Monday (0)
            # Days back = (2 - 0) + 7 = 9... but we want just last week's Monday
            # Actually: if target <= current, days_back = current - target
            #          if target > current, days_back = current + (7 - target)

            # Simpler: always go back 7+ days to ensure we get "last" week
            days_back = (current_weekday - target_weekday) % 7
            if days_back == 0:
                days_back = 7  # "last Monday" when today is Monday means 7 days ago

            return today - timedelta(days=days_back)

    # "this Monday/Tuesday/etc" (current week)
    for i, day_name in enumerate(weekdays):
        if f"this {day_name}" in date_str_lower or date_str_lower == day_name:
            current_weekday = today.weekday()
            target_weekday = i

            # If target is before today in the week, it's earlier this week
            # If target is after today, it hasn't happened yet (return None or interpret as last week)
            if target_weekday <= current_weekday:
                days_back = current_weekday - target_weekday
                return today - timedelta(days=days_back)
            else:
                # Future day this week - interpret as last week
                days_back = current_weekday + (7 - target_weekday)
                return today - timedelta(days=days_back)

    # ISO format: "2024-01-15" or "01/15" or "Jan 15"
    try:
        # Try ISO format first
        return date.fromisoformat(date_str)
    except ValueError:
        pass

    # Try MM/DD format
    match = re.match(r"(\d{1,2})/(\d{1,2})", date_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        # Assume current year, or previous year if date is in the future
        year = today.year
        try:
            parsed_date = date(year, month, day)
            if parsed_date > today:
                parsed_date = date(year - 1, month, day)
            return parsed_date
        except ValueError:
            return None

    # Try "Jan 15" or "January 15" format
    months = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    for month_name, month_num in months.items():
        if month_name in date_str_lower:
            # Extract day number
            match = re.search(r"\d+", date_str)
            if match:
                day = int(match.group())
                year = today.year
                try:
                    parsed_date = date(year, month_num, day)
                    if parsed_date > today:
                        parsed_date = date(year - 1, month_num, day)
                    return parsed_date
                except ValueError:
                    return None

    return None


def fuzzy_match_exercise(query: str, exercise_list: list[str]) -> Optional[str]:
    """
    Fuzzy match exercise name from user input.

    Args:
        query: User's exercise query (e.g., "bench")
        exercise_list: List of exercise names to match against

    Returns:
        Best matching exercise name or None
    """
    query_lower = query.lower().strip()

    # Exact match
    for ex in exercise_list:
        if query_lower == ex.lower():
            return ex

    # Substring match (prefer shorter matches)
    matches = []
    for ex in exercise_list:
        if query_lower in ex.lower():
            matches.append(ex)

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        # Return shortest match (most specific)
        return min(matches, key=len)

    # Word boundary match (e.g., "bench" matches "Bench Press" but not "Incline Bench")
    for ex in exercise_list:
        ex_words = ex.lower().split()
        if query_lower in ex_words or any(w.startswith(query_lower) for w in ex_words):
            return ex

    return None


@tool
def edit_exercise_weight(
    date_description: str,
    exercise_name: str,
    new_weight: float,
    set_number: Optional[int] = None
) -> dict:
    """
    Edit the weight for a specific exercise in a past workout.

    Use this when the user wants to change/correct a weight they logged.
    Examples:
    - "Change my bench press from Tuesday to 145 lbs"
    - "Update last Monday's squat to 200 pounds"
    - "Fix the deadlift weight from Jan 15 to 315"

    Args:
        date_description: Fuzzy date like "last Tuesday", "Jan 15", "3 days ago"
        exercise_name: Name of exercise (fuzzy matching supported)
        new_weight: New weight in pounds
        set_number: Which set to edit (1-indexed). If None, will edit all sets or ask user.

    Returns:
        Dict with success status and edit_context for confirmation dialog
    """
    # Validate weight
    if new_weight < 0 or new_weight > 1000:
        return {
            "success": False,
            "error": f"Invalid weight: {new_weight} lbs. Must be between 0 and 1000."
        }

    # Parse date
    target_date = parse_date_fuzzy(date_description)
    if not target_date:
        return {
            "success": False,
            "error": f"Couldn't understand date: '{date_description}'. Try 'last Tuesday', 'Jan 15', or '3 days ago'."
        }

    # Find workout on that date
    # Search within a few days in case user's date is slightly off
    start_date = target_date - timedelta(days=2)
    end_date = target_date + timedelta(days=2)

    logs = get_logs_by_date_range(start_date, end_date)

    # Filter out deleted logs
    logs = [log for log in logs if not log.get("deleted", False)]

    if not logs:
        return {
            "success": False,
            "error": f"No workouts found near {target_date.isoformat()}. Check the date and try again."
        }

    # Find matching exercise in logs
    candidates = []

    for log in logs:
        exercises = log.get("exercises", [])
        exercise_names = [ex.get("name", "") for ex in exercises]

        matched_name = fuzzy_match_exercise(exercise_name, exercise_names)

        if matched_name:
            # Find exercise index
            for i, ex in enumerate(exercises):
                if ex.get("name") == matched_name:
                    candidates.append({
                        "log": log,
                        "exercise_index": i,
                        "exercise_name": matched_name,
                        "exercise_data": ex
                    })

    if not candidates:
        return {
            "success": False,
            "error": f"Couldn't find exercise '{exercise_name}' in workouts near {target_date.isoformat()}."
        }

    if len(candidates) > 1:
        # Multiple matches - return info for user to clarify
        match_info = []
        for c in candidates:
            log_date = c["log"].get("date")
            workout_type = c["log"].get("type")
            match_info.append(f"{workout_type} on {log_date}")

        return {
            "success": False,
            "error": f"Found {len(candidates)} workouts with {exercise_name}: {', '.join(match_info)}. Please be more specific about the date."
        }

    # Single match found!
    candidate = candidates[0]
    log = candidate["log"]
    exercise_index = candidate["exercise_index"]
    exercise_data = candidate["exercise_data"]
    exercise_full_name = candidate["exercise_name"]

    sets = exercise_data.get("sets", [])

    if not sets:
        return {
            "success": False,
            "error": f"Exercise '{exercise_full_name}' has no sets to edit."
        }

    # Determine which set to edit
    set_index: Union[int, str]  # Can be an int index or "all"
    if set_number is not None:
        # User specified a set number (1-indexed)
        if set_number < 1 or set_number > len(sets):
            return {
                "success": False,
                "error": f"Invalid set number: {set_number}. This exercise has {len(sets)} sets."
            }
        set_index = set_number - 1
    else:
        # No set specified - default to first set (most common case)
        # Or if all sets have same weight, edit all of them
        weights = [s.get("weight_lbs") for s in sets if s.get("weight_lbs") is not None]

        if len(set(weights)) == 1:
            # All sets have same weight - edit all of them
            set_index = "all"
        else:
            # Different weights - edit first set only
            set_index = 0

    # Get old weight
    if set_index == "all":
        old_weight = sets[0].get("weight_lbs", 0)
        set_display = "all sets"
    else:
        old_weight = sets[set_index].get("weight_lbs", 0)
        set_display = f"set {set_index + 1}"

    # Return edit context for confirmation dialog
    return {
        "success": True,
        "edit_context": {
            "log_id": log.get("id"),
            "workout_date": log.get("date"),
            "workout_type": log.get("type"),
            "exercise_name": exercise_full_name,
            "exercise_index": exercise_index,
            "set_index": set_index,  # Can be integer or "all"
            "old_weight": old_weight,
            "new_weight": new_weight,
            "set_display": set_display,
            "total_sets": len(sets)
        },
        "message": f"Found {exercise_full_name} in {log.get('type')} workout on {log.get('date')}. Ready to change {set_display} from {old_weight} lbs to {new_weight} lbs."
    }
