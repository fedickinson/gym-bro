"""
Test exercise intro information system.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.suggestion_engine import get_exercise_info


def test_exercise_info():
    """Test that get_exercise_info returns correct data."""
    print("=" * 60)
    print("🧪 Testing Exercise Info for UI")
    print("=" * 60)

    # Test with catalog exercise
    print("\n📋 Testing catalog exercise (Dumbbell Bench Press):")
    info = get_exercise_info("Dumbbell Bench Press")

    assert info['found_in_catalog'] == True, "Should find exercise in catalog"
    assert info['canonical_name'] == "Dumbbell Bench Press"
    assert len(info['muscle_groups']) > 0, "Should have muscle groups"
    assert len(info['equipment']) > 0, "Should have equipment"
    assert info['category'] == "compound", "Should be compound"
    assert info['beginner_weight_lbs'] == 20.0, "Should have beginner weight"
    assert len(info['weight_reasoning']) > 0, "Should have reasoning"

    print(f"  ✅ Canonical: {info['canonical_name']}")
    print(f"  ✅ Targets: {', '.join(info['muscle_groups'])}")
    print(f"  ✅ Equipment: {', '.join(info['equipment'])}")
    print(f"  ✅ Category: {info['category']}")
    print(f"  ✅ Beginner Weight: {info['beginner_weight_lbs']} lbs")
    print(f"  ✅ First Time: {info['is_first_time']}")
    print(f"  ✅ Reasoning: {info['weight_reasoning']}")

    # Test with variation
    print("\n📋 Testing exercise variation (DB Bench):")
    info = get_exercise_info("DB Bench")

    assert info['found_in_catalog'] == True, "Should match variation"
    assert info['canonical_name'] == "Dumbbell Bench Press", "Should map to canonical"
    print(f"  ✅ 'DB Bench' → '{info['canonical_name']}'")

    # Test with unknown exercise
    print("\n📋 Testing unknown exercise (Exotic Curl):")
    info = get_exercise_info("Exotic Curl")

    assert info['found_in_catalog'] == False, "Should not find in catalog"
    assert info['canonical_name'] == "Exotic Curl", "Should use original name"
    assert info['beginner_weight_lbs'] is not None, "Should still have default weight"

    print(f"  ✅ Not in catalog, but has defaults:")
    print(f"  ✅ Category: {info['category']}")
    print(f"  ✅ Beginner Weight: {info['beginner_weight_lbs']} lbs")
    print(f"  ✅ Reasoning: {info['weight_reasoning']}")

    # Test bodyweight exercise
    print("\n📋 Testing bodyweight exercise (Pull Ups):")
    info = get_exercise_info("Pull Ups")

    assert info['found_in_catalog'] == True
    assert info['category'] == "bodyweight"
    assert info['beginner_weight_lbs'] is None, "Bodyweight should have no weight"

    print(f"  ✅ Category: {info['category']}")
    print(f"  ✅ Weight: {info['beginner_weight_lbs']} (bodyweight)")
    print(f"  ✅ Reasoning: {info['weight_reasoning']}")

    print("\n" + "=" * 60)
    print("✅ ALL EXERCISE INFO TESTS PASSED!")
    print("=" * 60)
    print("\n🎯 Exercise intro system is ready for UI!")
    print("\nThe intro screen will now show:")
    print("  • Exercise canonical name")
    print("  • Muscle groups targeted")
    print("  • Equipment needed")
    print("  • Exercise category (compound/isolation/bodyweight)")
    print("  • Beginner weight guidance (if first time)")
    print("  • Weight reasoning/form tips\n")


if __name__ == "__main__":
    try:
        test_exercise_info()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
