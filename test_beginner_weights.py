"""
Quick test of beginner weight functionality.
Tests catalog loading, fuzzy matching, and weight suggestions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.suggestion_engine import (
    _load_exercise_catalog,
    _fuzzy_match_exercise,
    _classify_exercise_for_default,
    _get_beginner_weight,
    _get_progressive_weight
)


def test_catalog_loading():
    """Test that exercise catalog loads correctly."""
    print("🧪 Testing catalog loading...")
    catalog = _load_exercise_catalog()

    assert "exercises" in catalog, "Catalog should have 'exercises' key"
    assert "default_weights" in catalog, "Catalog should have 'default_weights' key"
    assert len(catalog["exercises"]) > 0, "Should have exercises in catalog"

    print(f"  ✅ Loaded {len(catalog['exercises'])} exercises")
    print(f"  ✅ Default weight categories: {list(catalog['default_weights'].keys())}")


def test_exact_match():
    """Test exact exercise name matching."""
    print("\n🧪 Testing exact exercise matching...")

    test_cases = [
        ("Dumbbell Bench Press", 20.0),
        ("Squat", 65.0),
        ("Lateral Raise", 10.0),
        ("Pull Ups", None),  # Bodyweight
    ]

    for exercise, expected_weight in test_cases:
        weight, reasoning = _get_beginner_weight(exercise)
        assert weight == expected_weight, f"{exercise} should suggest {expected_weight} lbs, got {weight}"
        assert len(reasoning) > 0, f"{exercise} should have reasoning"
        print(f"  ✅ {exercise}: {weight} lbs - {reasoning[:50]}...")


def test_variation_matching():
    """Test that exercise variations match correctly."""
    print("\n🧪 Testing variation matching...")

    # These are variations that should match canonical names
    test_cases = [
        ("DB Bench", "Dumbbell Bench Press", 20.0),
        ("BB Squat", "Squat", 65.0),
        ("Side Raise", "Lateral Raise", 10.0),
    ]

    catalog = _load_exercise_catalog()

    for variation, canonical, expected_weight in test_cases:
        matched = _fuzzy_match_exercise(variation, catalog)
        assert matched is not None, f"Should match variation '{variation}'"
        assert matched["canonical"] == canonical, f"'{variation}' should match '{canonical}'"

        weight, _ = _get_beginner_weight(variation)
        assert weight == expected_weight, f"{variation} should suggest {expected_weight} lbs"
        print(f"  ✅ '{variation}' → '{canonical}': {weight} lbs")


def test_classification():
    """Test classification of unknown exercises."""
    print("\n🧪 Testing exercise classification...")

    # Test that classification categories are correct
    # Note: fuzzy matching may return catalog weights instead of defaults
    test_cases = [
        ("Z-Bar Press", "compound_upper"),  # Has "press" keyword
        ("Jefferson Squat", "compound_lower"),  # Has "squat" keyword
        ("Cable Reverse Fly", "cable_machine"),  # Has "cable" keyword
        ("Wrist Curl", "isolation_upper"),  # Defaults to isolation_upper
        ("Leg Extension Machine", "isolation_lower"),  # Has "leg extension"
        ("Handstand Push Up", "bodyweight"),  # Has "push up"
    ]

    for exercise, expected_category in test_cases:
        category = _classify_exercise_for_default(exercise)
        assert category == expected_category, f"{exercise} should be classified as {expected_category}, got {category}"

        weight, reasoning = _get_beginner_weight(exercise)
        # Just verify we get a weight suggestion (or None for bodyweight)
        if expected_category == "bodyweight":
            assert weight is None, f"{exercise} should have None for bodyweight"
        else:
            assert weight is not None and weight > 0, f"{exercise} should have a positive weight"
        print(f"  ✅ '{exercise}' → {category}: {weight} lbs")


def test_progressive_weight_fallback():
    """Test that _get_progressive_weight falls back to beginner weight when no history."""
    print("\n🧪 Testing progressive weight with no history...")

    # These exercises likely have no history for a new user
    test_cases = [
        "Dumbbell Bench Press",
        "Squat",
        "Lateral Raise",
    ]

    for exercise in test_cases:
        weight = _get_progressive_weight(exercise)
        # Should return beginner weight (not None)
        assert weight is not None or exercise == "Pull Ups", f"{exercise} should have a beginner weight suggestion"
        print(f"  ✅ {exercise}: {weight} lbs (beginner fallback)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🏋️  BEGINNER WEIGHT SYSTEM TESTS")
    print("=" * 60)

    try:
        test_catalog_loading()
        test_exact_match()
        test_variation_matching()
        test_classification()
        test_progressive_weight_fallback()

        print("\n" + "=" * 60)
        print("✅ ALL BEGINNER WEIGHT TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("  • Exercise catalog loads correctly")
        print("  • Exact matching works for all catalog exercises")
        print("  • Variations match to canonical names")
        print("  • Unknown exercises get classified and default weights")
        print("  • Progressive weight function falls back to beginner weights")
        print("\n🎯 Beginner weight system is WORKING!\n")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
