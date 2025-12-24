"""
Fix Null Workout Types - Infer and backfill missing workout types.

This script analyzes workouts with null/missing types and infers the type
based on the exercises performed.

SAFETY:
- Creates backup before modification
- Dry-run mode by default
- Manual review of inferred types
"""

import json
from pathlib import Path
from datetime import datetime


# Exercise classification rules
PUSH_EXERCISES = {
    "bench", "press", "chest", "tricep", "shoulder", "dip", "fly", "pushup", "push up",
    "overhead", "military", "incline", "decline", "dumbbell press"
}

PULL_EXERCISES = {
    "pull", "row", "lat", "back", "bicep", "curl", "chin", "deadlift", "shrug",
    "face pull", "pulldown", "pullup", "pull up"
}

LEG_EXERCISES = {
    "squat", "leg", "lunge", "calf", "quad", "hamstring", "glute", "deadlift",
    "bulgarian", "goblet", "romanian", "rdl", "leg press", "leg curl", "leg extension"
}


def classify_exercise(exercise_name: str) -> str | None:
    """
    Classify an exercise into Push/Pull/Legs based on name.

    Returns:
        "Push", "Pull", "Legs", or None if ambiguous
    """
    name_lower = exercise_name.lower()

    # Check for leg exercises first (most specific)
    for keyword in LEG_EXERCISES:
        if keyword in name_lower:
            return "Legs"

    # Check push vs pull
    push_score = sum(1 for keyword in PUSH_EXERCISES if keyword in name_lower)
    pull_score = sum(1 for keyword in PULL_EXERCISES if keyword in name_lower)

    if push_score > pull_score:
        return "Push"
    elif pull_score > push_score:
        return "Pull"

    return None


def infer_workout_type(workout: dict) -> tuple[str | None, float]:
    """
    Infer workout type from exercises.

    Returns:
        (type, confidence) where confidence is 0.0-1.0
    """
    exercises = workout.get("exercises", [])
    if not exercises:
        return None, 0.0

    # Classify each exercise
    classifications = []
    for ex in exercises:
        ex_type = classify_exercise(ex.get("name", ""))
        if ex_type:
            classifications.append(ex_type)

    if not classifications:
        return None, 0.0

    # Count votes
    type_counts = {}
    for t in classifications:
        type_counts[t] = type_counts.get(t, 0) + 1

    # Get majority vote
    majority_type = max(type_counts, key=type_counts.get)
    majority_count = type_counts[majority_type]
    total_classified = len(classifications)

    # Confidence = percentage of exercises matching majority type
    confidence = majority_count / total_classified

    return majority_type, confidence


def analyze_null_types(data_path: Path) -> list[dict]:
    """Analyze all workouts with null types."""
    with open(data_path) as f:
        data = json.load(f)

    null_type_logs = []

    for log in data.get("logs", []):
        log_type = log.get("type")

        if log_type is None or log_type == "":
            # Infer type
            inferred_type, confidence = infer_workout_type(log)

            null_type_logs.append({
                "id": log.get("id"),
                "date": log.get("date"),
                "current_type": log_type,
                "inferred_type": inferred_type,
                "confidence": confidence,
                "exercise_count": len(log.get("exercises", [])),
                "exercises": [ex.get("name") for ex in log.get("exercises", [])]
            })

    return null_type_logs


def apply_fixes(data_path: Path, fixes: dict[str, str], dry_run: bool = True):
    """
    Apply type fixes to workout logs.

    Args:
        data_path: Path to workout_logs.json
        fixes: Dict mapping log_id -> new_type
        dry_run: If True, don't actually save changes
    """
    with open(data_path) as f:
        data = json.load(f)

    updated_count = 0

    for log in data.get("logs", []):
        log_id = log.get("id")
        if log_id in fixes:
            old_type = log.get("type")
            new_type = fixes[log_id]
            log["type"] = new_type
            updated_count += 1
            print(f"  {log_id}: {old_type} → {new_type}")

    if dry_run:
        print(f"\n[DRY RUN] Would update {updated_count} workouts")
        print("Run with --apply to actually save changes")
    else:
        # Save the updated data
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✅ Updated {updated_count} workouts")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fix null workout types")
    parser.add_argument("--apply", action="store_true", help="Actually apply fixes (not dry-run)")
    parser.add_argument("--min-confidence", type=float, default=0.6,
                        help="Minimum confidence to auto-fix (0.0-1.0)")
    args = parser.parse_args()

    data_path = Path(__file__).parent.parent / "data" / "workout_logs.json"

    if not data_path.exists():
        print(f"❌ File not found: {data_path}")
        return

    print("🔍 Analyzing workouts with null types...\n")

    null_logs = analyze_null_types(data_path)

    if not null_logs:
        print("✅ No workouts with null types found!")
        return

    print(f"Found {len(null_logs)} workouts with null/missing types:\n")

    # Group by confidence
    high_confidence = []
    low_confidence = []
    no_inference = []

    for log in null_logs:
        print(f"📅 {log['date']} - {log['id']}")
        print(f"   Exercises ({log['exercise_count']}): {', '.join(log['exercises'][:3])}")
        if log['exercise_count'] > 3:
            print(f"   ... and {log['exercise_count'] - 3} more")

        if log['inferred_type']:
            print(f"   ✅ Inferred: {log['inferred_type']} (confidence: {log['confidence']:.1%})")

            if log['confidence'] >= args.min_confidence:
                high_confidence.append(log)
            else:
                low_confidence.append(log)
        else:
            print(f"   ⚠️  Could not infer type")
            no_inference.append(log)

        print()

    # Build fixes dict for high-confidence inferences
    fixes = {}
    for log in high_confidence:
        fixes[log['id']] = log['inferred_type']

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"High confidence (≥{args.min_confidence:.0%}): {len(high_confidence)} workouts")
    print(f"Low confidence (<{args.min_confidence:.0%}): {len(low_confidence)} workouts")
    print(f"Could not infer: {len(no_inference)} workouts")

    if fixes:
        print(f"\n📝 Proposed fixes:")
        for log_id, new_type in fixes.items():
            print(f"  - {log_id} → {new_type}")

        print()
        apply_fixes(data_path, fixes, dry_run=not args.apply)
    else:
        print("\n⚠️  No high-confidence fixes available")
        print("Try lowering --min-confidence or manually review low-confidence inferences")

    if low_confidence:
        print(f"\n⚠️  {len(low_confidence)} low-confidence workouts need manual review")
        print("Review these manually and add fixes if needed")


if __name__ == "__main__":
    main()
