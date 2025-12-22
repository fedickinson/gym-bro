"""
Comprehensive Log Graph Tests

Tests the LangGraph workflow with various workout input formats,
including edge cases, incomplete data, and different notation styles.
"""

import os
from dotenv import load_dotenv
from src.agents.log_graph import start_workout_log

load_dotenv()

def test_log_graph():
    """Test log graph with various workout formats."""

    print("=" * 80)
    print("🧪 LOG GRAPH COMPREHENSIVE TEST")
    print("=" * 80)

    test_workouts = [
        # Standard notation
        "bench 135x8x3, overhead 95x8x3",

        # With workout type mentioned
        "Did push today - bench 135x8, overhead 95x8, tricep pushdowns",

        # Different notation styles
        "Squat: 185 lbs for 8 reps, 3 sets",
        "3 sets of 8 reps at 135 on bench",
        "Deadlift 225x5x5",

        # Multiple exercises, varied format
        "leg press 270 x 12 x 3, leg curl 70x12x3, calf raises 3x20",

        # Incomplete data
        "did some curls today",
        "bench press and overhead press",
        "shoulders",

        # With extra context
        "Killed it today! Bench 145x8x4, felt strong, overhead 100x8x3",

        # Pull workout
        "pull day: lat pulldown 120x10x3, rows 55x10x3, curls 30x12x3",

        # Legs with detail
        "legs: squats 195x8x3, leg press 300x12x3, lunges 3x10 each leg",

        # Mixed units/notation
        "bench press 60kg x 8, overhead 40kg x 8",

        # Bodyweight
        "push-ups 3x20, pull-ups 3x10, dips 3x15",

        # Very minimal
        "gym",
        "worked out",

        # With date
        "Yesterday: bench 135x8, overhead 95x8",
    ]

    print(f"\nTesting {len(test_workouts)} different workout formats...\n")

    results = []
    for i, workout in enumerate(test_workouts, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(test_workouts)}")
        print("-" * 80)
        print(f"INPUT: {workout}")
        print("-" * 80)

        try:
            state = start_workout_log(workout)

            if state.get("parsed_workout"):
                parsed = state["parsed_workout"]
                print(f"✅ PARSED SUCCESSFULLY")
                print(f"   Date: {parsed.get('date')}")
                print(f"   Type: {parsed.get('type')}")
                print(f"   Exercises: {len(parsed.get('exercises', []))}")

                for ex in parsed.get('exercises', []):
                    sets_count = len(ex.get('sets', []))
                    print(f"     • {ex.get('name')}: {sets_count} sets")

                results.append({
                    "input": workout,
                    "success": True,
                    "exercises": len(parsed.get('exercises', [])),
                    "type": parsed.get('type')
                })
            else:
                print(f"❌ PARSE FAILED")
                print(f"   Response: {state.get('response', 'No response')[:100]}")
                results.append({
                    "input": workout,
                    "success": False,
                    "error": "Parse failed"
                })

        except Exception as e:
            print(f"❌ ERROR: {str(e)[:100]}")
            results.append({
                "input": workout,
                "success": False,
                "error": str(e)
            })

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n\n{'='*80}")
    print("LOG GRAPH SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(test_workouts)}")
    print(f"Successful parses: {successful}/{len(test_workouts)} ({successful/len(test_workouts)*100:.1f}%)")
    print(f"Failed: {len(test_workouts) - successful}")

    # Show failures
    failures = [r for r in results if not r["success"]]
    if failures:
        print(f"\n❌ FAILED TESTS:")
        for f in failures:
            print(f"   '{f['input'][:50]}...' → {f.get('error', 'Unknown error')}")

    # Stats on successful parses
    if successful > 0:
        total_exercises = sum(r.get('exercises', 0) for r in results if r["success"])
        avg_exercises = total_exercises / successful
        print(f"\n📊 STATISTICS:")
        print(f"   Average exercises per workout: {avg_exercises:.1f}")

        types = {}
        for r in results:
            if r["success"]:
                workout_type = r.get('type', 'Unknown')
                types[workout_type] = types.get(workout_type, 0) + 1

        print(f"   Workout types detected:")
        for t, count in types.items():
            print(f"     {t}: {count}")

    return results


if __name__ == "__main__":
    results = test_log_graph()
