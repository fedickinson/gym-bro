"""
Test Adaptive Template Generation.

This script tests the full adaptive template system end-to-end.
"""

import sys
sys.path.insert(0, '/Users/franklindickinson/Projects/gym-bro')

from src.agents.template_generator import generate_adaptive_template
from src.data import get_template

print("=" * 80)
print("ADAPTIVE TEMPLATE GENERATION TEST")
print("=" * 80)

# Test 1: Generate Adaptive Pull Template
print("\n1. ADAPTIVE PULL TEMPLATE")
print("-" * 80)

adaptive_pull = generate_adaptive_template("Pull")

print(f"Template ID: {adaptive_pull.get('id')}")
print(f"Template Name: {adaptive_pull.get('name')}")
print(f"Mode: {adaptive_pull.get('mode')}")
print(f"\nExercises ({len(adaptive_pull.get('exercises', []))}):")

for ex in adaptive_pull.get('exercises', []):
    print(f"\n  • {ex.get('name')}")
    print(f"    Sets: {ex.get('target_sets')} × {ex.get('target_reps')} reps")
    if ex.get('suggested_weight_lbs'):
        print(f"    Suggested Weight: {ex.get('suggested_weight_lbs'):.0f} lbs")
    print(f"    Rest: {ex.get('rest_seconds')}s")
    print(f"    💡 {ex.get('reasoning')}")

print(f"\nAdaptations:")
for adaptation in adaptive_pull.get('adaptations', []):
    print(f"  • {adaptation}")

if adaptive_pull.get('coaching_notes'):
    print(f"\nCoaching Notes:")
    for note in adaptive_pull['coaching_notes']:
        print(f"  {note}")

# Test 2: Compare with Static Template
print("\n\n2. COMPARISON: Adaptive vs Static")
print("-" * 80)

static_pull = get_template("pull_a")

if static_pull:
    print(f"Static Template: {len(static_pull.get('exercises', []))} exercises")
    print(f"Adaptive Template: {len(adaptive_pull.get('exercises', []))} exercises")

    print(f"\nStatic exercises:")
    for ex in static_pull.get('exercises', []):
        print(f"  • {ex.get('name')}")

    print(f"\nAdaptive exercises:")
    for ex in adaptive_pull.get('exercises', []):
        print(f"  • {ex.get('name')}")

# Test 3: Generate Adaptive Push Template
print("\n\n3. ADAPTIVE PUSH TEMPLATE")
print("-" * 80)

adaptive_push = generate_adaptive_template("Push")

print(f"Template Name: {adaptive_push.get('name')}")
print(f"\nExercises ({len(adaptive_push.get('exercises', []))}):")

for ex in adaptive_push.get('exercises', []):
    name = ex.get('name')
    weight = ex.get('suggested_weight_lbs')
    sets = ex.get('target_sets')

    if weight:
        print(f"  • {name}: {sets} sets × {weight:.0f} lbs")
    else:
        print(f"  • {name}: {sets} sets (no weight history)")

print(f"\nAdaptations:")
for adaptation in adaptive_push.get('adaptations', []):
    print(f"  • {adaptation}")

# Test 4: Test via get_workout_template tool
print("\n\n4. TEST VIA get_workout_template TOOL")
print("-" * 80)

from src.tools.recommend_tools import get_workout_template

# Test adaptive mode
print("Testing adaptive mode:")
template_adaptive = get_workout_template.invoke({"workout_type": "Pull", "adaptive": True})
print(f"  Mode: {template_adaptive.get('mode')}")
print(f"  Exercises: {len(template_adaptive.get('exercises', []))}")

# Test static mode
print("\nTesting static mode:")
template_static = get_workout_template.invoke({"workout_type": "Pull", "adaptive": False})
print(f"  Mode: {template_static.get('mode')}")
print(f"  Exercises: {len(template_static.get('exercises', []))}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
