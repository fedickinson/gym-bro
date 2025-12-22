"""
Comprehensive Intent Router Tests

Tests the router's ability to classify various user inputs correctly,
including edge cases, ambiguous messages, and mixed intents.
"""

import os
from dotenv import load_dotenv
from src.agents.router import IntentRouter, quick_route

load_dotenv()

def test_intent_router():
    """Test intent classification with diverse inputs."""

    print("=" * 80)
    print("🧪 INTENT ROUTER COMPREHENSIVE TEST")
    print("=" * 80)

    router = IntentRouter()

    # Test cases with expected intents
    test_cases = [
        # === LOG INTENT ===
        ("Just finished push day", "log"),
        ("Did legs today - squats and deadlifts", "log"),
        ("Bench 135x8x3, overhead 95x8", "log"),
        ("Completed my workout: chest and triceps", "log"),
        ("Worked out today", "log"),

        # === QUERY INTENT ===
        ("What's my bench press PR?", "query"),
        ("How many workouts did I do last week?", "query"),
        ("Show me my squat progression", "query"),
        ("What did I lift on Monday?", "query"),
        ("Compare my bench to my squat", "query"),

        # === RECOMMEND INTENT ===
        ("What should I do today?", "recommend"),
        ("Plan my workout for tomorrow", "recommend"),
        ("Am I overtraining chest?", "recommend"),
        ("What's next in my rotation?", "recommend"),
        ("Should I do legs or upper today?", "recommend"),

        # === CHAT INTENT ===
        ("How are you?", "chat"),
        ("What's progressive overload?", "chat"),
        ("I'm feeling tired today", "chat"),
        ("Thanks for the help!", "chat"),
        ("Tell me about rest days", "chat"),

        # === ADMIN INTENT ===
        ("Delete my last workout", "admin"),
        ("Fix yesterday's log", "admin"),
        ("Edit my bench press weight", "admin"),
        ("Remove Tuesday's workout", "admin"),

        # === EDGE CASES ===
        ("bench?", "query"),  # Single word question
        ("legs", "recommend"),  # Ambiguous - likely asking what to do
        ("135", "chat"),  # Just a number - fallback to chat
        ("today", "recommend"),  # Ambiguous - likely asking what to do
        ("help", "chat"),  # Help request
    ]

    print(f"\nTesting {len(test_cases)} different inputs...\n")

    correct = 0
    incorrect = 0
    results = []

    for i, (user_input, expected) in enumerate(test_cases, 1):
        # Try quick route first
        quick = quick_route(user_input)

        # If quick route doesn't match, use full classification
        if quick:
            classified = quick
            method = "quick"
        else:
            try:
                result = router.classify(user_input)
                classified = result.intent
                method = "llm"
            except Exception as e:
                classified = "error"
                method = f"error: {e}"

        is_correct = classified == expected
        if is_correct:
            correct += 1
            status = "✅"
        else:
            incorrect += 1
            status = f"❌ (got {classified})"

        results.append({
            "input": user_input,
            "expected": expected,
            "classified": classified,
            "method": method,
            "correct": is_correct
        })

        print(f"{status} {i:2d}. '{user_input[:40]:<40}' → {classified:10} ({method})")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(test_cases)}")
    print(f"Correct: {correct} ({correct/len(test_cases)*100:.1f}%)")
    print(f"Incorrect: {incorrect} ({incorrect/len(test_cases)*100:.1f}%)")

    # Show incorrect classifications
    if incorrect > 0:
        print("\n❌ MISCLASSIFICATIONS:")
        for r in results:
            if not r["correct"]:
                print(f"  '{r['input']}' → Expected: {r['expected']}, Got: {r['classified']}")

    return results


if __name__ == "__main__":
    results = test_intent_router()
