"""
Test Supabase connection and basic database operations.

Run this after setting up your .env file to verify everything works.

Usage:
    python scripts/test_supabase_connection.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_supabase_client
from datetime import date


def test_database_setup():
    """Test database connection and table access."""
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)

    # Test 1: Basic connection
    print("\n1. Testing connection...")
    try:
        client = get_supabase_client()
        print("   ✅ Connected to Supabase")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Check .env file has SUPABASE_URL and SUPABASE_KEY")
        print("  - Verify credentials are correct (copy from Supabase dashboard)")
        print("  - Ensure no extra spaces in .env values")
        return False

    # Test 2: Table access
    print("\n2. Testing table access...")
    tables = ["workout_logs", "templates", "weekly_split", "exercises"]

    for table in tables:
        try:
            result = client.table(table).select("*").limit(1).execute()
            count = len(result.data) if result.data else 0
            print(f"   ✅ {table}: accessible ({count} sample rows)")
        except Exception as e:
            print(f"   ❌ {table}: {str(e)[:50]}...")
            print("\nTroubleshooting:")
            print("  - Did you run scripts/schema.sql in Supabase SQL Editor?")
            print("  - Check Supabase → Table Editor → verify tables exist")
            return False

    # Test 3: Read operations
    print("\n3. Testing read operations...")
    try:
        from src.data import get_all_logs, get_all_templates

        logs = get_all_logs()
        print(f"   ✅ get_all_logs(): {len(logs)} workouts")

        templates = get_all_templates()
        print(f"   ✅ get_all_templates(): {len(templates)} templates")

    except Exception as e:
        print(f"   ❌ Read operations failed: {e}")
        return False

    # Test 4: Write operations (safe test)
    print("\n4. Testing write operations...")
    try:
        from src.data import add_log, delete_log_permanent

        test_log = {
            "id": "test-connection-001",
            "date": date.today().isoformat(),
            "type": "Push",
            "exercises": [
                {
                    "name": "Connection Test",
                    "sets": [{"reps": 1, "weight_lbs": 1}]
                }
            ],
            "notes": "Automated connection test - safe to delete",
            "completed": True
        }

        # Add test workout
        log_id = add_log(test_log)
        print(f"   ✅ add_log(): created test workout {log_id}")

        # Delete test workout (permanent)
        deleted = delete_log_permanent(log_id)
        if deleted:
            print(f"   ✅ delete_log_permanent(): cleaned up test workout")
        else:
            print(f"   ⚠️  Couldn't delete test workout (you may need to delete {log_id} manually)")

    except Exception as e:
        print(f"   ❌ Write operations failed: {e}")
        return False

    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nYour Supabase setup is working correctly!")
    print("\nNext steps:")
    print("  1. Run migration: python scripts/migrate_json_to_supabase.py --execute")
    print("  2. Test app locally: streamlit run app.py")
    print("  3. Deploy to Streamlit Cloud")
    print("\n")

    return True


if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
