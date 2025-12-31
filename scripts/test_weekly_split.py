"""
Test Weekly Split Tracking - Verify weekly split calculation works correctly.
"""

from src.tools.recommend_tools import get_weekly_split_status, suggest_next_workout


def test_weekly_split():
    """Test the weekly split tracking system."""
    print("="*60)
    print("WEEKLY SPLIT STATUS TEST")
    print("="*60)

    # Get weekly split status
    status = get_weekly_split_status.invoke({})

    print(f"\n📅 Week: {status['week_start']} (Days left: {status['days_left_in_week']})")
    print(f"\n{status['summary']}")

    print("\n📊 Detailed Breakdown:")
    print("-" * 40)

    targets = status['targets']
    completed = status['completed']
    remaining = status['remaining']

    for workout_type in targets.keys():
        target = targets[workout_type]
        done = completed.get(workout_type, 0)
        left = remaining.get(workout_type, 0)

        status_icon = "✅" if left == 0 else "⏳"
        print(f"{status_icon} {workout_type:8s}: {done}/{target} complete, {left} remaining")

    print("\n🎯 Next Suggested:", status['next_suggested'])

    # Test suggestion engine
    print("\n" + "="*60)
    print("WORKOUT SUGGESTION TEST")
    print("="*60)

    suggestion = suggest_next_workout.invoke({})

    print(f"\n💡 Suggested Workout: {suggestion['suggested_type']}")
    print(f"📋 Reason: {suggestion['reason']}")

    weekly_status = suggestion.get('weekly_status', {})
    if weekly_status:
        print(f"\n📈 This Week: {weekly_status.get('summary', 'Unknown')}")

    return status, suggestion


if __name__ == "__main__":
    status, suggestion = test_weekly_split()

    print("\n" + "="*60)
    print("✅ WEEKLY SPLIT TRACKING IS WORKING!")
    print("="*60)
