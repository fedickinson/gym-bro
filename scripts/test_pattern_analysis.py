"""
Test Pattern Analysis Engine with Real Data.

This script tests all pattern analysis functions with the actual 128 workout dataset.
"""

import sys
sys.path.insert(0, '/Users/franklindickinson/Projects/gym-bro')

from src.analysis.workout_patterns import (
    analyze_exercise_patterns,
    analyze_volume_tolerance,
    analyze_progression_velocity,
    analyze_recovery_patterns,
    detect_overtraining_signals
)

print("=" * 80)
print("PATTERN ANALYSIS ENGINE TEST")
print("=" * 80)

# Test 1: Exercise Patterns for Pull workouts
print("\n1. EXERCISE PATTERNS (Pull Workouts, All Time)")
print("-" * 80)
pull_patterns = analyze_exercise_patterns("Pull", days=0)  # 0 = all time
print(f"Total Pull workouts analyzed: {pull_patterns['total_workouts_analyzed']}")
print(f"\nCommon exercises (≥60% frequency):")
for ex in pull_patterns['common_exercises']:
    print(f"  • {ex['name']}: {ex['frequency']*100:.0f}% frequency, {ex['avg_sets']:.1f} sets avg, done {ex['times_done']} times")

if pull_patterns['rarely_done']:
    print(f"\nRarely done (<30% frequency): {', '.join(pull_patterns['rarely_done'])}")

# Test 2: Volume Tolerance for Push workouts
print("\n\n2. VOLUME TOLERANCE (Push Workouts, Last 365 Days)")
print("-" * 80)
push_volume = analyze_volume_tolerance("Push", days=0)
print(f"Average total sets per workout: {push_volume['avg_total_sets']:.1f}")
print(f"Average sets per exercise: {push_volume['avg_sets_per_exercise']:.1f}")
print(f"Typical exercises per workout: {push_volume['typical_exercises_per_workout']:.1f}")
print(f"Volume trend: {push_volume['volume_trend']}")
print(f"  Recent avg: {push_volume['recent_avg_sets']:.1f} sets")
print(f"  Older avg: {push_volume['older_avg_sets']:.1f} sets")

# Test 3: Progression Velocity for specific exercise
print("\n\n3. PROGRESSION VELOCITY (Lat Pulldown)")
print("-" * 80)
lat_progression = analyze_progression_velocity("Lat Pulldown", days=0)
print(f"Exercise: {lat_progression['exercise']}")
print(f"Current weight: {lat_progression['current_weight']} lbs")
print(f"Velocity: {lat_progression['velocity']}")
print(f"Avg weekly increase: {lat_progression['avg_weekly_increase']:.2f} lbs/week")
print(f"Stall detected: {lat_progression['stall_detected']}")
print(f"Weeks at current weight: {lat_progression['weeks_at_current_weight']}")
print(f"Suggested action: {lat_progression['suggested_action'].upper()}")
print(f"Data points: {lat_progression['data_points']}")

# Test 4: Another exercise (Bench Press)
print("\n\n4. PROGRESSION VELOCITY (Dumbbell Bench Press)")
print("-" * 80)
bench_progression = analyze_progression_velocity("Dumbbell Bench Press", days=0)
print(f"Exercise: {bench_progression['exercise']}")
print(f"Current weight: {bench_progression['current_weight']} lbs")
print(f"Velocity: {bench_progression['velocity']}")
print(f"Avg weekly increase: {bench_progression['avg_weekly_increase']:.2f} lbs/week")
print(f"Suggested action: {bench_progression['suggested_action'].upper()}")
print(f"Data points: {bench_progression['data_points']}")

# Test 5: Recovery Patterns
print("\n\n5. RECOVERY PATTERNS (Back Muscle Group)")
print("-" * 80)
back_recovery = analyze_recovery_patterns("back", days=0)
print(f"Muscle group: {back_recovery['muscle_group']}")
print(f"Average frequency: {back_recovery['avg_frequency']:.1f} workouts/week")
print(f"Optimal rest days: {back_recovery['optimal_rest_days']}")
print(f"\nPerformance by rest days:")
for rest_key, perf in back_recovery['performance_by_rest'].items():
    print(f"  {rest_key}: {perf['avg_weight']:.1f} lbs avg, {perf['avg_reps']:.1f} reps avg ({perf['workouts']} workouts)")

# Test 6: Overtraining Detection
print("\n\n6. OVERTRAINING DETECTION (Last 30 Days)")
print("-" * 80)
overtraining = detect_overtraining_signals(days=30)
print(f"Overtraining risk: {overtraining['overtraining_risk'].upper()}")
print(f"Recommendation: {overtraining['recommendation']}")
print(f"Workouts last week: {overtraining['total_workouts_last_week']}")
print(f"Volume trend: {overtraining['volume_trend_pct']:+.1f}%")

if overtraining['signals']:
    print(f"\nSignals detected:")
    for signal in overtraining['signals']:
        print(f"  ⚠️  {signal}")
else:
    print(f"\n✓ No overtraining signals detected")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
