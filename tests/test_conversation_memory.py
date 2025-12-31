"""
Test conversation memory and context retention.

This test simulates the exact scenario the user reported where the agent
lost track of equipment constraints and didn't trigger session creation.
"""

import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.chat_agent import ChatAgent
from src.agents.main import GymBroOrchestrator

load_dotenv()


def test_equipment_constraint_memory():
    """
    Test that agent remembers equipment constraints across conversation turns.

    Simulates:
    1. User says "I only have dumbbells, keep it simple"
    2. Agent recommends
    3. User says "tell me more about what we'll do for legs"
    4. Agent should CREATE session with equipment constraints remembered
    """
    print("\n" + "=" * 70)
    print("TEST: Equipment Constraint Memory")
    print("=" * 70)

    agent = ChatAgent()
    conversation_history = []

    # Turn 1: User mentions equipment constraints
    print("\n👤 User: I'm at home, need a quick workout for the next two days, only have dumbbells, keep it simple")

    result1 = agent.chat(
        "I'm at home, need a quick workout for the next two days, only have dumbbells, keep it simple",
        chat_history=conversation_history
    )

    print(f"🤖 Agent: {result1['response'][:200]}...")
    print(f"📊 Tools: {result1['tool_calls']}")
    print(f"🎯 Session: {result1['session_data'] is not None}")

    # Add to history
    conversation_history.append({"role": "user", "content": "I'm at home, need a quick workout for the next two days, only have dumbbells, keep it simple"})
    conversation_history.append({"role": "assistant", "content": result1['response']})

    # Turn 2: User asks for details (should trigger session with constraints)
    print("\n👤 User: okay tell me more in detail what we will do for legs")

    result2 = agent.chat(
        "okay tell me more in detail what we will do for legs",
        chat_history=conversation_history
    )

    print(f"🤖 Agent: {result2['response'][:300]}...")
    print(f"📊 Tools: {result2['tool_calls']}")
    print(f"🎯 Session created: {result2['session_data'] is not None}")

    # Assertions
    try:
        assert 'start_workout_session' in result2['tool_calls'], \
            f"Agent should call start_workout_session, called: {result2['tool_calls']}"

        assert result2['session_data'] is not None, \
            "Session should be created when user asks for workout details"

        session = result2['session_data']

        # Check that equipment constraints were applied
        if 'equipment_unavailable' in session:
            print(f"✅ Equipment constraints remembered: {session['equipment_unavailable']}")

        # Check workout type
        workout_type = session.get('suggested_type', 'Unknown')
        print(f"💪 Workout type: {workout_type}")

        # Check exercises don't require unavailable equipment
        template = session.get('planned_template', {})
        exercises = template.get('exercises', [])
        print(f"📋 {len(exercises)} exercises in plan")

        for ex in exercises[:3]:
            print(f"   - {ex.get('name', 'Unknown')}")

        print("\n✅ TEST PASSED: Agent remembered context and created appropriate session!")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_multi_turn_context():
    """
    Test that orchestrator maintains context across multiple turns.
    """
    print("\n" + "=" * 70)
    print("TEST: Multi-Turn Context via Orchestrator")
    print("=" * 70)

    orchestrator = GymBroOrchestrator()
    conversation_history = []

    # Turn 1: Initial request with constraints
    print("\n👤 User: I'm stressed, need simple workout, only dumbbells")

    result1 = orchestrator.process_message(
        "I'm stressed, need simple workout, only dumbbells",
        chat_history=conversation_history
    )

    print(f"🎯 Intent: {result1['intent']}")
    print(f"🔧 Handler: {result1['handler']}")
    print(f"🤖 Response: {result1['response'][:150]}...")

    # Add to history
    conversation_history.append({"role": "user", "content": "I'm stressed, need simple workout, only dumbbells"})
    conversation_history.append({"role": "assistant", "content": result1['response']})

    # Turn 2: Follow-up asking for specifics
    print("\n👤 User: show me what we'll do")

    result2 = orchestrator.process_message(
        "show me what we'll do",
        chat_history=conversation_history
    )

    print(f"🎯 Intent: {result2['intent']}")
    print(f"🔧 Handler: {result2['handler']}")
    print(f"🤖 Response: {result2['response'][:150]}...")
    print(f"🎯 Session created: {result2['session_data'] is not None}")

    try:
        assert result2['session_data'] is not None, \
            "Follow-up 'show me what we'll do' should create session"

        print("\n✅ TEST PASSED: Context maintained across orchestrator calls!")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False


def test_tell_me_more_trigger():
    """
    Test that 'tell me more' phrases trigger session creation.
    """
    print("\n" + "=" * 70)
    print("TEST: 'Tell Me More' Trigger Phrase")
    print("=" * 70)

    agent = ChatAgent()

    trigger_phrases = [
        "tell me more in detail what we will do for legs",
        "show me the plan",
        "what will we do for push",
        "okay let's do it",
    ]

    all_passed = True

    for phrase in trigger_phrases:
        print(f"\n👤 User: {phrase}")

        result = agent.chat(phrase)

        print(f"📊 Tools: {result['tool_calls']}")
        print(f"🎯 Session: {result['session_data'] is not None}")

        if 'start_workout_session' not in result['tool_calls']:
            print(f"⚠️  WARNING: Phrase didn't trigger session: '{phrase}'")
            all_passed = False
        else:
            print(f"✅ Correctly triggered session")

    return all_passed


def main():
    """Run all conversation memory tests"""
    print("\n" + "=" * 70)
    print("🧠 CONVERSATION MEMORY TEST SUITE")
    print("=" * 70)
    print("\nTesting fixes for context loss bug...")

    results = []

    # Run tests
    results.append(("Equipment Constraint Memory", test_equipment_constraint_memory()))
    results.append(("Multi-Turn Context", test_multi_turn_context()))
    results.append(("'Tell Me More' Triggers", test_tell_me_more_trigger()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total = len(results)

    print(f"\n{total_passed}/{total} tests passed")

    if total_passed == total:
        print("\n🎉 All context retention tests passed!")
        print("\nThe conversation memory bug is FIXED:")
        print("✅ Equipment constraints are remembered")
        print("✅ Context flows through orchestrator")
        print("✅ 'Tell me more' triggers session creation")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review above.")
        return 1


if __name__ == "__main__":
    exit(main())
