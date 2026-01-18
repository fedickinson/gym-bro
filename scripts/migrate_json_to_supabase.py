"""
Migrate JSON data to Supabase.

This script reads all JSON data files and bulk imports them into Supabase.
Run this ONCE after setting up the database schema.

Usage:
    # Dry run (preview what will be migrated)
    python scripts/migrate_json_to_supabase.py --dry-run

    # Execute migration
    python scripts/migrate_json_to_supabase.py --execute
"""

import json
import argparse
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase.client import create_client


def get_supabase_client():
    """Get Supabase client from environment variables."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )

    return create_client(url, key)


def migrate_workout_logs(sb, dry_run=True):
    """Migrate workout logs from JSON to Supabase."""
    json_file = Path(__file__).parent.parent / "data" / "workout_logs.json"

    print(f"\n{'='*60}")
    print("MIGRATING WORKOUT LOGS")
    print(f"{'='*60}")

    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return 0

    with open(json_file) as f:
        data = json.load(f)

    logs = data.get("logs", [])
    print(f"Found {len(logs)} workout logs")

    if dry_run:
        print("DRY RUN - Preview of first 3 logs:")
        for log in logs[:3]:
            print(f"  - {log.get('date')} | {log.get('type')} | {log.get('id')}")
        if len(logs) > 3:
            print(f"  ... and {len(logs) - 3} more")
        return len(logs)

    # Execute migration in batches
    batch_size = 100
    total_inserted = 0

    for i in range(0, len(logs), batch_size):
        batch = logs[i:i+batch_size]
        try:
            result = sb.table("workout_logs").insert(batch).execute()
            inserted_count = len(result.data) if result.data else len(batch)
            total_inserted += inserted_count
            print(f"✅ Inserted batch {i//batch_size + 1}: {inserted_count} logs")
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
            raise

    print(f"✅ Migrated {total_inserted} workout logs")
    return total_inserted


def migrate_templates(sb, dry_run=True):
    """Migrate templates from JSON to Supabase."""
    json_file = Path(__file__).parent.parent / "data" / "templates.json"

    print(f"\n{'='*60}")
    print("MIGRATING TEMPLATES")
    print(f"{'='*60}")

    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return 0

    with open(json_file) as f:
        data = json.load(f)

    templates = data.get("templates", [])
    print(f"Found {len(templates)} templates")

    if dry_run:
        print("DRY RUN - Preview of templates:")
        for template in templates:
            print(f"  - {template.get('id')} | {template.get('name')} | {template.get('type')}")
        return len(templates)

    # Insert all templates
    try:
        result = sb.table("templates").insert(templates).execute()
        inserted_count = len(result.data) if result.data else len(templates)
        print(f"✅ Migrated {inserted_count} templates")
        return inserted_count
    except Exception as e:
        print(f"❌ Error inserting templates: {e}")
        raise


def migrate_weekly_split(sb, dry_run=True):
    """Migrate weekly split data from JSON to Supabase."""
    json_file = Path(__file__).parent.parent / "data" / "weekly_split.json"

    print(f"\n{'='*60}")
    print("MIGRATING WEEKLY SPLIT")
    print(f"{'='*60}")

    if not json_file.exists():
        print(f"❌ File not found: {json_file}")
        return 0

    with open(json_file) as f:
        data = json.load(f)

    print(f"Found weekly split config")

    if dry_run:
        print("DRY RUN - Preview of weekly split:")
        print(f"  - Types: {data.get('split_config', {}).get('types', [])}")
        print(f"  - Current week start: {data.get('current_week', {}).get('start_date')}")
        return 1

    # Insert weekly split as single row
    weekly_split_row = {
        "config": data.get("split_config", {}),
        "current_week": data.get("current_week", {})
    }

    try:
        result = sb.table("weekly_split").insert(weekly_split_row).execute()
        print(f"✅ Migrated weekly split configuration")
        return 1
    except Exception as e:
        print(f"❌ Error inserting weekly split: {e}")
        raise


def migrate_exercises(sb, dry_run=True):
    """Migrate exercises from JSON to Supabase."""
    json_file = Path(__file__).parent.parent / "data" / "exercises.json"

    print(f"\n{'='*60}")
    print("MIGRATING EXERCISES")
    print(f"{'='*60}")

    if not json_file.exists():
        print(f"⚠️  File not found: {json_file}")
        print("Skipping exercises migration (file may not exist yet)")
        return 0

    with open(json_file) as f:
        data = json.load(f)

    # Handle different possible JSON structures
    if isinstance(data, dict):
        exercises = data.get("exercises", [])
    elif isinstance(data, list):
        exercises = data
    else:
        print(f"❌ Unexpected data format in {json_file}")
        return 0

    print(f"Found {len(exercises)} exercises")

    # Transform exercises to match schema (canonical -> canonical_name)
    transformed_exercises = []
    for exercise in exercises:
        transformed = {
            "canonical_name": exercise.get('canonical', exercise.get('canonical_name', 'unknown')),
            "variations": exercise.get('variations', []),
            "muscle_groups": exercise.get('muscle_groups', []),
            "equipment": exercise.get('equipment', [])
        }
        transformed_exercises.append(transformed)

    if dry_run:
        print("DRY RUN - Preview of first 3 exercises:")
        for exercise in transformed_exercises[:3]:
            canonical = exercise.get('canonical_name', 'unknown')
            print(f"  - {canonical}")
        if len(transformed_exercises) > 3:
            print(f"  ... and {len(transformed_exercises) - 3} more")
        return len(transformed_exercises)

    # Insert all exercises
    try:
        result = sb.table("exercises").insert(transformed_exercises).execute()
        inserted_count = len(result.data) if result.data else len(exercises)
        print(f"✅ Migrated {inserted_count} exercises")
        return inserted_count
    except Exception as e:
        print(f"❌ Error inserting exercises: {e}")
        raise


def main():
    """Main migration entry point."""
    parser = argparse.ArgumentParser(description="Migrate JSON data to Supabase")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without executing"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the migration"
    )

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("❌ Please specify --dry-run or --execute")
        parser.print_help()
        sys.exit(1)

    dry_run = args.dry_run

    print("\n" + "="*60)
    print("GYM BRO: JSON → SUPABASE MIGRATION")
    print("="*60)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'EXECUTE (will write to database)'}")

    try:
        sb = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

    # Run migrations
    try:
        workout_count = migrate_workout_logs(sb, dry_run)
        template_count = migrate_templates(sb, dry_run)
        split_count = migrate_weekly_split(sb, dry_run)
        exercise_count = migrate_exercises(sb, dry_run)

        # Summary
        print(f"\n{'='*60}")
        print("MIGRATION SUMMARY")
        print(f"{'='*60}")
        print(f"Workout Logs:  {workout_count}")
        print(f"Templates:     {template_count}")
        print(f"Weekly Split:  {split_count}")
        print(f"Exercises:     {exercise_count}")
        print(f"{'='*60}")

        if dry_run:
            print("\n✅ DRY RUN COMPLETE")
            print("Run with --execute to perform the actual migration")
        else:
            print("\n✅ MIGRATION COMPLETE")
            print("Verify data in Supabase dashboard → Table Editor")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
