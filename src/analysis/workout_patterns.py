"""
Workout Pattern Analysis Engine.

Learns from historical workout data to detect:
- Exercise preferences and adherence
- Volume tolerance and trends
- Progression velocity per exercise
- Recovery patterns
- Overtraining signals
"""

from datetime import date, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import statistics

from src.data import get_logs_by_date_range, get_all_logs


def analyze_exercise_patterns(workout_type: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze which exercises user actually does for a workout type.

    Learns:
    - Which exercises from templates are consistently done
    - Which template exercises are skipped
    - Which exercises are frequently added (not in template)

    Args:
        workout_type: Push, Pull, Legs, Upper, or Lower
        days: Number of days to look back (default: 90, use 0 for all time)

    Returns:
        {
          "common_exercises": [
            {"name": "Lat Pulldown", "frequency": 0.95, "avg_sets": 4.2},
            {"name": "Dumbbell Row", "frequency": 0.90, "avg_sets": 4.0}
          ],
          "rarely_done": ["Cable Row"],
          "frequently_added": ["Hammer Curl"],
          "total_workouts_analyzed": 12
        }
    """
    # Get workouts of this type
    if days == 0:
        # Get all workouts
        all_logs = get_all_logs()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        all_logs = get_logs_by_date_range(start_date, end_date)

    # Filter by workout type
    workouts = [log for log in all_logs if log.get('type') == workout_type]

    if not workouts:
        return {
            "common_exercises": [],
            "rarely_done": [],
            "frequently_added": [],
            "total_workouts_analyzed": 0
        }

    # Count exercise frequency and sets
    exercise_stats = defaultdict(lambda: {"count": 0, "total_sets": 0})

    for workout in workouts:
        exercises_in_workout = set()

        for exercise in workout.get('exercises', []):
            name = exercise.get('name')
            if not name:
                continue

            exercises_in_workout.add(name)
            exercise_stats[name]["count"] += 1
            exercise_stats[name]["total_sets"] += len(exercise.get('sets', []))

    # Calculate frequency and average sets
    total_workouts = len(workouts)
    exercise_analysis = []

    for name, stats in exercise_stats.items():
        frequency = stats["count"] / total_workouts
        avg_sets = stats["total_sets"] / stats["count"] if stats["count"] > 0 else 0

        exercise_analysis.append({
            "name": name,
            "frequency": round(frequency, 2),
            "avg_sets": round(avg_sets, 1),
            "times_done": stats["count"]
        })

    # Sort by frequency (most common first)
    exercise_analysis.sort(key=lambda x: x["frequency"], reverse=True)

    # Identify common (>= 60% frequency), rare (< 30%), and frequently added
    common_exercises = [ex for ex in exercise_analysis if ex["frequency"] >= 0.6]
    rarely_done = [ex["name"] for ex in exercise_analysis if ex["frequency"] < 0.3]

    # For "frequently_added", we'd need template comparison
    # For now, all exercises with decent frequency are considered
    frequently_added = []  # TODO: Compare against base template

    return {
        "common_exercises": common_exercises,
        "rarely_done": rarely_done,
        "frequently_added": frequently_added,
        "total_workouts_analyzed": total_workouts
    }


def analyze_volume_tolerance(workout_type: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze user's typical training volume for a workout type.

    Learns:
    - Average total sets per workout
    - Average sets per exercise
    - Typical number of exercises per workout
    - Volume trend (increasing, stable, decreasing)

    Args:
        workout_type: Push, Pull, Legs, Upper, or Lower
        days: Number of days to look back (use 0 for all time)

    Returns:
        {
          "avg_total_sets": 18.5,
          "avg_sets_per_exercise": 3.7,
          "typical_exercises_per_workout": 5,
          "volume_trend": "increasing",  # or "stable", "decreasing"
          "recent_avg_sets": 20.2,
          "older_avg_sets": 16.8
        }
    """
    # Get workouts of this type
    if days == 0:
        all_logs = get_all_logs()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        all_logs = get_logs_by_date_range(start_date, end_date)

    workouts = [log for log in all_logs if log.get('type') == workout_type]

    if not workouts:
        return {
            "avg_total_sets": 0,
            "avg_sets_per_exercise": 0,
            "typical_exercises_per_workout": 0,
            "volume_trend": "unknown",
            "recent_avg_sets": 0,
            "older_avg_sets": 0
        }

    # Sort by date
    workouts.sort(key=lambda x: x.get('date', ''))

    # Calculate metrics
    total_sets_per_workout = []
    exercises_per_workout = []
    sets_per_exercise_all = []

    for workout in workouts:
        total_sets = 0
        num_exercises = 0

        for exercise in workout.get('exercises', []):
            num_sets = len(exercise.get('sets', []))
            total_sets += num_sets
            num_exercises += 1

            if num_sets > 0:
                sets_per_exercise_all.append(num_sets)

        total_sets_per_workout.append(total_sets)
        exercises_per_workout.append(num_exercises)

    # Calculate averages
    avg_total_sets = statistics.mean(total_sets_per_workout) if total_sets_per_workout else 0
    avg_exercises = statistics.mean(exercises_per_workout) if exercises_per_workout else 0
    avg_sets_per_exercise = statistics.mean(sets_per_exercise_all) if sets_per_exercise_all else 0

    # Determine trend (compare recent half vs older half)
    midpoint = len(total_sets_per_workout) // 2

    if midpoint > 0:
        older_sets = total_sets_per_workout[:midpoint]
        recent_sets = total_sets_per_workout[midpoint:]

        older_avg = statistics.mean(older_sets) if older_sets else 0
        recent_avg = statistics.mean(recent_sets) if recent_sets else 0

        # 10% threshold for "trend" detection
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        older_avg = 0
        recent_avg = avg_total_sets
        trend = "stable"

    return {
        "avg_total_sets": round(avg_total_sets, 1),
        "avg_sets_per_exercise": round(avg_sets_per_exercise, 1),
        "typical_exercises_per_workout": round(avg_exercises, 1),
        "volume_trend": trend,
        "recent_avg_sets": round(recent_avg, 1),
        "older_avg_sets": round(older_avg, 1)
    }


def analyze_progression_velocity(exercise_name: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze progression rate for a specific exercise.

    Detects:
    - How fast weight is increasing (lbs/week)
    - Whether user is plateaued
    - Suggested action (increase, maintain, deload)

    Args:
        exercise_name: Name of exercise (e.g., "Lat Pulldown")
        days: Number of days to look back (use 0 for all time)

    Returns:
        {
          "exercise": "Lat Pulldown",
          "velocity": "moderate",  # slow/moderate/fast
          "avg_weekly_increase": 2.5,
          "stall_detected": false,
          "weeks_at_current_weight": 2,
          "suggested_action": "maintain",  # increase/maintain/deload
          "current_weight": 140,
          "data_points": 8
        }
    """
    # Get all workout logs
    if days == 0:
        logs = get_all_logs()
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        logs = get_logs_by_date_range(start_date, end_date)

    # Extract history for this exercise
    history = []

    for log in logs:
        for exercise in log.get('exercises', []):
            if exercise.get('name') == exercise_name:
                sets = exercise.get('sets', [])
                if not sets:
                    continue

                # Get max weight for this workout
                max_weight = max([s.get('weight_lbs', 0) for s in sets])

                if max_weight > 0:
                    history.append({
                        'date': log.get('date'),
                        'max_weight': max_weight
                    })

    if not history:
        return {
            "exercise": exercise_name,
            "velocity": "unknown",
            "avg_weekly_increase": 0,
            "stall_detected": False,
            "weeks_at_current_weight": 0,
            "suggested_action": "maintain",
            "current_weight": 0,
            "data_points": 0
        }

    # Sort by date
    history.sort(key=lambda x: x['date'])

    current_weight = history[-1]['max_weight']
    data_points = len(history)

    # Calculate weekly increase if we have enough data
    if len(history) >= 2:
        first_weight = history[0]['max_weight']
        last_weight = history[-1]['max_weight']

        # Calculate time span in weeks
        first_date = date.fromisoformat(history[0]['date'])
        last_date = date.fromisoformat(history[-1]['date'])
        weeks_span = max((last_date - first_date).days / 7, 1)

        total_increase = last_weight - first_weight
        avg_weekly_increase = total_increase / weeks_span if weeks_span > 0 else 0

        # Classify velocity
        if avg_weekly_increase > 3:
            velocity = "fast"
        elif avg_weekly_increase > 1:
            velocity = "moderate"
        elif avg_weekly_increase > 0:
            velocity = "slow"
        else:
            velocity = "plateau"
    else:
        avg_weekly_increase = 0
        velocity = "insufficient_data"

    # Detect stall (same weight for 3+ consecutive workouts)
    if len(history) >= 3:
        recent_weights = [h['max_weight'] for h in history[-3:]]
        stall_detected = len(set(recent_weights)) == 1  # All same weight
        weeks_at_current = 0

        # Count weeks at current weight
        for h in reversed(history):
            if h['max_weight'] == current_weight:
                weeks_at_current += 1
            else:
                break
    else:
        stall_detected = False
        weeks_at_current = 1

    # Determine suggested action
    if stall_detected and weeks_at_current >= 4:
        suggested_action = "deload"  # Plateau for 4+ weeks
    elif velocity in ["moderate", "fast"] and not stall_detected:
        suggested_action = "increase"  # Good progression
    elif weeks_at_current <= 2:
        suggested_action = "maintain"  # Build consistency
    else:
        suggested_action = "maintain"  # Default

    return {
        "exercise": exercise_name,
        "velocity": velocity,
        "avg_weekly_increase": round(avg_weekly_increase, 2),
        "stall_detected": stall_detected,
        "weeks_at_current_weight": weeks_at_current,
        "suggested_action": suggested_action,
        "current_weight": current_weight,
        "data_points": data_points
    }


def analyze_recovery_patterns(muscle_group: str, days: int = 90) -> Dict[str, Any]:
    """
    Analyze recovery patterns for a muscle group.

    Finds:
    - Average training frequency per week
    - Optimal rest days between workouts
    - Performance correlation with rest

    Args:
        muscle_group: back, chest, legs, etc.
        days: Number of days to look back

    Returns:
        {
          "muscle_group": "back",
          "avg_frequency": 2.1,
          "optimal_rest_days": 3,
          "performance_by_rest": {
            "2_days": {"avg_reps": 9.2, "avg_weight": 135, "workouts": 3},
            "3_days": {"avg_reps": 10.1, "avg_weight": 140, "workouts": 5}
          }
        }
    """
    # Map muscle group to workout types
    muscle_to_type = {
        "back": ["Pull"],
        "chest": ["Push"],
        "legs": ["Legs"],
        "shoulders": ["Push"],
        "arms": ["Push", "Pull"]
    }

    workout_types = muscle_to_type.get(muscle_group.lower(), [])

    if not workout_types:
        return {
            "muscle_group": muscle_group,
            "avg_frequency": 0,
            "optimal_rest_days": 0,
            "performance_by_rest": {}
        }

    # Get relevant workouts
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    all_logs = get_logs_by_date_range(start_date, end_date)

    workouts = [log for log in all_logs if log.get('type') in workout_types]

    if len(workouts) < 2:
        return {
            "muscle_group": muscle_group,
            "avg_frequency": 0,
            "optimal_rest_days": 0,
            "performance_by_rest": {}
        }

    # Sort by date
    workouts.sort(key=lambda x: x.get('date', ''))

    # Calculate frequency (workouts per week)
    weeks_span = days / 7
    avg_frequency = len(workouts) / weeks_span if weeks_span > 0 else 0

    # Analyze performance by rest days
    performance_by_rest = defaultdict(lambda: {
        "total_reps": 0,
        "total_weight": 0,
        "count": 0
    })

    for i in range(1, len(workouts)):
        prev_date = date.fromisoformat(workouts[i-1]['date'])
        curr_date = date.fromisoformat(workouts[i]['date'])
        rest_days = (curr_date - prev_date).days

        # Get performance metrics from current workout
        total_reps = 0
        total_weight = 0
        set_count = 0

        for exercise in workouts[i].get('exercises', []):
            for s in exercise.get('sets', []):
                reps = s.get('reps', 0)
                weight = s.get('weight_lbs', 0)

                if reps and weight:
                    total_reps += reps
                    total_weight += weight
                    set_count += 1

        if set_count > 0:
            rest_key = f"{rest_days}_days"
            performance_by_rest[rest_key]["total_reps"] += total_reps
            performance_by_rest[rest_key]["total_weight"] += total_weight
            performance_by_rest[rest_key]["count"] += 1

    # Calculate averages
    perf_summary = {}
    best_rest_days = 2
    best_score = 0

    for rest_key, data in performance_by_rest.items():
        if data["count"] > 0:
            avg_reps = data["total_reps"] / data["count"]
            avg_weight = data["total_weight"] / data["count"]

            perf_summary[rest_key] = {
                "avg_reps": round(avg_reps, 1),
                "avg_weight": round(avg_weight, 1),
                "workouts": data["count"]
            }

            # Find optimal rest (highest avg_weight)
            if avg_weight > best_score:
                best_score = avg_weight
                best_rest_days = int(rest_key.split('_')[0])

    return {
        "muscle_group": muscle_group,
        "avg_frequency": round(avg_frequency, 1),
        "optimal_rest_days": best_rest_days,
        "performance_by_rest": perf_summary
    }


def detect_overtraining_signals(days: int = 30) -> Dict[str, Any]:
    """
    Detect signs of overtraining or excessive fatigue.

    Signals:
    - Rapid volume increase (>20% in 2 weeks)
    - Declining performance despite consistent training
    - Excessive frequency (>6 workouts/week)

    Args:
        days: Number of days to analyze (default: 30 for recent trend)

    Returns:
        {
          "overtraining_risk": "low",  # low/moderate/high
          "signals": [
            "Volume up 25% over last 2 weeks",
            "Performance declining on Bench Press"
          ],
          "recommendation": "continue" or "deload_recommended",
          "total_workouts_last_week": 4,
          "volume_trend_pct": 15.2
        }
    """
    # Get recent workouts
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    logs = get_logs_by_date_range(start_date, end_date)

    if len(logs) < 4:
        return {
            "overtraining_risk": "low",
            "signals": [],
            "recommendation": "continue",
            "total_workouts_last_week": len(logs),
            "volume_trend_pct": 0
        }

    # Sort by date
    logs.sort(key=lambda x: x.get('date', ''))

    signals = []
    risk_score = 0

    # Check 1: Frequency (workouts per week)
    recent_week = [log for log in logs if (
        end_date - date.fromisoformat(log.get('date', str(end_date)))
    ).days <= 7]

    workouts_last_week = len(recent_week)

    if workouts_last_week > 6:
        signals.append(f"High frequency: {workouts_last_week} workouts in last 7 days")
        risk_score += 2
    elif workouts_last_week > 5:
        signals.append(f"Moderate frequency: {workouts_last_week} workouts in last 7 days")
        risk_score += 1

    # Check 2: Volume trend (compare recent half vs older half)
    midpoint = len(logs) // 2

    older_workouts = logs[:midpoint]
    recent_workouts = logs[midpoint:]

    def calculate_total_volume(workouts):
        """Calculate total volume (weight × reps) across workouts."""
        volume = 0
        for log in workouts:
            for ex in log.get('exercises', []):
                for s in ex.get('sets', []):
                    reps = s.get('reps', 0)
                    weight = s.get('weight_lbs', 0)
                    if reps and weight:
                        volume += reps * weight
        return volume

    older_volume = calculate_total_volume(older_workouts)
    recent_volume = calculate_total_volume(recent_workouts)

    if older_volume > 0:
        volume_change_pct = ((recent_volume - older_volume) / older_volume) * 100

        if volume_change_pct > 25:
            signals.append(f"Volume up {volume_change_pct:.0f}% over last {days//2} days")
            risk_score += 2
        elif volume_change_pct > 15:
            signals.append(f"Volume up {volume_change_pct:.0f}% over last {days//2} days")
            risk_score += 1
    else:
        volume_change_pct = 0

    # Determine risk level and recommendation
    if risk_score >= 3:
        overtraining_risk = "high"
        recommendation = "deload_recommended"
    elif risk_score >= 2:
        overtraining_risk = "moderate"
        recommendation = "monitor"
    else:
        overtraining_risk = "low"
        recommendation = "continue"

    return {
        "overtraining_risk": overtraining_risk,
        "signals": signals,
        "recommendation": recommendation,
        "total_workouts_last_week": workouts_last_week,
        "volume_trend_pct": round(volume_change_pct, 1) if older_volume > 0 else 0
    }
