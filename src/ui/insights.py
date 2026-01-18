"""
Smart Insights Engine for Progress Analytics.

Analyzes workout data and generates personalized, actionable insights for users.
"""

from datetime import date, timedelta
from src.data import get_exercise_history, get_all_logs, get_logs_by_date_range


def generate_exercise_insights(exercise: str, days: int = 90) -> dict:
    """
    Generate personalized insights for an exercise's progression.

    Args:
        exercise: Exercise name
        days: Time period to analyze

    Returns:
        dict with keys: 'has_data', 'quality', 'insights' (list of strings), 'recommendations'
    """
    history = get_exercise_history(exercise, days)

    if not history or len(history) < 2:
        return {
            'has_data': False,
            'quality': 'insufficient',
            'data_points': len(history) if history else 0,
            'needed': max(0, 3 - (len(history) if history else 0)),
            'insights': [],
            'recommendations': [f"Log {max(0, 3 - (len(history) if history else 0))} more workouts with {exercise} to see progression trends"]
        }

    # Extract data
    weights = [h['max_weight'] for h in history]
    dates = [h['date'] for h in history]

    # Calculate metrics
    first_weight = weights[0]
    last_weight = weights[-1]
    max_weight = max(weights)
    weight_gain = last_weight - first_weight
    weight_gain_pct = (weight_gain / first_weight * 100) if first_weight > 0 else 0

    # Determine data quality
    data_points = len(history)
    if data_points < 3:
        quality = 'low'
    elif data_points < 6:
        quality = 'moderate'
    else:
        quality = 'good'

    # Generate insights
    insights = []
    recommendations = []

    # Insight 1: Overall trend
    if weight_gain > 0:
        insights.append(f"💪 **Great progress!** You've gained {weight_gain:.1f} lbs ({weight_gain_pct:+.1f}%) on {exercise} in the last {days} days.")
    elif weight_gain < 0:
        insights.append(f"📉 Your {exercise} has decreased by {abs(weight_gain):.1f} lbs ({weight_gain_pct:.1f}%). This could indicate a deload period or technique focus.")
    else:
        insights.append(f"➡️ Your {exercise} weight has remained stable at {last_weight:.1f} lbs.")

    # Insight 2: PR detection
    if last_weight == max_weight and last_weight > first_weight:
        insights.append(f"🎯 **New PR!** Your most recent session was your personal record at {max_weight:.1f} lbs!")
    elif max_weight > last_weight:
        pr_date = dates[weights.index(max_weight)]
        insights.append(f"🏆 Your PR is {max_weight:.1f} lbs (set on {pr_date}). Current: {last_weight:.1f} lbs.")

    # Insight 3: Consistency check
    time_span_days = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days
    if time_span_days > 0:
        frequency = data_points / (time_span_days / 7)  # workouts per week
        if frequency >= 1.5:
            insights.append(f"⚡ Excellent consistency: {frequency:.1f}x per week on average.")
        elif frequency >= 0.5:
            insights.append(f"✓ Good consistency: {frequency:.1f}x per week on average.")
        else:
            insights.append(f"📅 Low frequency: {frequency:.1f}x per week. Consider increasing to 1-2x/week for better gains.")
            recommendations.append("Aim for at least 1-2 sessions per week for optimal progress")

    # Recommendation: Progressive overload
    if weight_gain_pct < 5 and data_points >= 6:
        recommendations.append("Consider increasing weight by 2.5-5 lbs next session to continue progressive overload")

    return {
        'has_data': True,
        'quality': quality,
        'data_points': data_points,
        'insights': insights,
        'recommendations': recommendations
    }


def generate_volume_insights(days: int = 90) -> dict:
    """
    Generate insights about training volume trends.

    Args:
        days: Time period to analyze

    Returns:
        dict with insights and recommendations
    """
    logs = get_logs_by_date_range(days)

    if not logs:
        return {
            'has_data': False,
            'insights': [],
            'recommendations': ["Start logging workouts to track your training volume"]
        }

    # Calculate weekly volumes
    weekly_volumes = {}
    for log in logs:
        log_date = date.fromisoformat(log['date'])
        week_start = log_date - timedelta(days=log_date.weekday())
        week_key = week_start.isoformat()

        total_volume = 0
        for exercise in log.get('exercises', []):
            for set_data in exercise.get('sets', []):
                weight = set_data.get('weight_lbs', 0)
                reps = set_data.get('reps', 0)
                total_volume += weight * reps

        weekly_volumes[week_key] = weekly_volumes.get(week_key, 0) + total_volume

    if not weekly_volumes:
        return {
            'has_data': False,
            'insights': [],
            'recommendations': ["Log exercises with weights and reps to track volume"]
        }

    volumes = list(weekly_volumes.values())
    avg_volume = sum(volumes) / len(volumes)
    max_volume = max(volumes)
    max_week = list(weekly_volumes.keys())[volumes.index(max_volume)]
    latest_volume = volumes[-1] if volumes else 0

    insights = []
    recommendations = []

    # Trend analysis
    if len(volumes) >= 4:
        recent_avg = sum(volumes[-4:]) / 4
        older_avg = sum(volumes[:-4]) / len(volumes[:-4]) if len(volumes) > 4 else avg_volume

        if recent_avg > older_avg * 1.1:
            insights.append(f"📈 **Volume trending up!** Recent weeks averaging {recent_avg:,.0f} lbs vs {older_avg:,.0f} lbs earlier.")
        elif recent_avg < older_avg * 0.9:
            insights.append(f"📉 Volume trending down: {recent_avg:,.0f} lbs vs {older_avg:,.0f} lbs. Could indicate recovery or deload.")

    # Peak week
    if max_volume > avg_volume * 1.2:
        insights.append(f"🏔️ Peak week: {max_volume:,.0f} lbs (week of {max_week}). That's {((max_volume/avg_volume - 1) * 100):.0f}% above average!")

    # Current vs average
    if latest_volume > avg_volume * 1.1:
        insights.append(f"💪 This week's volume ({latest_volume:,.0f} lbs) is above your average ({avg_volume:,.0f} lbs)!")
    elif latest_volume < avg_volume * 0.8:
        recommendations.append("This week's volume is below average. Consider adding sets or exercises if you're feeling recovered.")

    return {
        'has_data': True,
        'insights': insights,
        'recommendations': recommendations,
        'stats': {
            'avg_volume': avg_volume,
            'max_volume': max_volume,
            'latest_volume': latest_volume
        }
    }


def generate_consistency_insights(days: int = 90) -> dict:
    """
    Generate insights about workout consistency and streaks.

    Args:
        days: Time period to analyze

    Returns:
        dict with insights and recommendations
    """
    logs = get_all_logs()

    if not logs:
        return {
            'has_data': False,
            'insights': [],
            'recommendations': ["Start your fitness journey by logging your first workout!"]
        }

    # Calculate streaks
    logs_by_date = {}
    for log in logs:
        log_date = log.get('date')
        if log_date:
            logs_by_date[log_date] = True

    # Current streak
    streak = 0
    current_date = date.today()
    while current_date.isoformat() in logs_by_date:
        streak += 1
        current_date -= timedelta(days=1)

    # Workouts in period
    cutoff_date = date.today() - timedelta(days=days)
    recent_workouts = [log for log in logs if date.fromisoformat(log['date']) >= cutoff_date]
    workout_count = len(recent_workouts)
    workouts_per_week = workout_count / (days / 7) if days > 0 else 0

    insights = []
    recommendations = []

    # Streak insights
    if streak > 0:
        insights.append(f"🔥 **{streak}-day streak!** Keep the momentum going!")
    else:
        days_since_last = None
        for i in range(1, 30):
            check_date = date.today() - timedelta(days=i)
            if check_date.isoformat() in logs_by_date:
                days_since_last = i
                break

        if days_since_last:
            insights.append(f"Last workout was {days_since_last} day{'s' if days_since_last != 1 else ''} ago. Ready to get back at it?")
            recommendations.append("Log a workout today to rebuild your streak!")

    # Frequency insights
    if workouts_per_week >= 4:
        insights.append(f"💯 Outstanding frequency: {workouts_per_week:.1f} workouts per week!")
    elif workouts_per_week >= 3:
        insights.append(f"✅ Great consistency: {workouts_per_week:.1f} workouts per week.")
    elif workouts_per_week >= 2:
        insights.append(f"👍 Good consistency: {workouts_per_week:.1f} workouts per week.")
    elif workouts_per_week >= 1:
        insights.append(f"📊 Moderate activity: {workouts_per_week:.1f} workouts per week.")
        recommendations.append("Aim for 3-4 workouts per week for optimal progress")
    else:
        insights.append(f"📅 Low activity: {workouts_per_week:.1f} workouts per week.")
        recommendations.append("Try to establish a consistent 3-4 day per week routine")

    return {
        'has_data': True,
        'insights': insights,
        'recommendations': recommendations,
        'stats': {
            'streak': streak,
            'workout_count': workout_count,
            'workouts_per_week': workouts_per_week
        }
    }


def get_quick_stats() -> dict:
    """
    Get quick headline statistics for dashboard cards.

    Returns:
        dict with quick stats
    """
    logs = get_all_logs()

    if not logs:
        return {
            'total_workouts': 0,
            'current_streak': 0,
            'this_month': 0,
            'recent_pr': None
        }

    # Total workouts
    total_workouts = len(logs)

    # Current streak
    logs_by_date = {}
    for log in logs:
        log_date = log.get('date')
        if log_date:
            logs_by_date[log_date] = True

    streak = 0
    current_date = date.today()
    while current_date.isoformat() in logs_by_date:
        streak += 1
        current_date -= timedelta(days=1)

    # This month
    month_start = date.today().replace(day=1)
    this_month = len([log for log in logs if date.fromisoformat(log['date']) >= month_start])

    # Recent PR (simplified - just check last 30 days for any exercise improvements)
    recent_pr = None
    # This would require more complex logic to track PRs per exercise

    return {
        'total_workouts': total_workouts,
        'current_streak': streak,
        'this_month': this_month,
        'recent_pr': recent_pr
    }
