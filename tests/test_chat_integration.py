"""
Test suite for Chat-Workout Integration (Phase 1-3)

Tests the following capabilities:
1. Chat history queries (using Query tools)
2. Chat workout recommendations (using Recommend tools)
3. Workout session creation from chat
4. Session data extraction and return
"""

import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.chat_agent import ChatAgent
from src.agents.main import GymBroOrchestrator

load_dotenv()


def test_chat_history_query():
    """Test 1: ChatAgent should use Query tools to answer history questions"""
    print("\n" + "=" * 70)
    print("TEST 1: Chat History Query")
    print("=" * 70)

    agent = ChatAgent()

    test_queries = [
        "What did I bench last week?",
        "How many workouts did I do this month?",
        "Show me my squat progression"
    ]

    for query in test_queries:
        print(f"\n👤 User: {query}")
        print("🤖 Agent thinking...\n")

        try:
            result = agent.chat(query)

            print(f"✅ Response: {result['response'][:200]}...")
            print(f"📊 Tools used: {result['tool_calls']}")
            print(f"🎯 Session created: {result['session_data'] is not None}")

            # Assertions
            assert isinstance(result, dict), "Result should be dict"
            assert 'response' in result, "Should have response"
            assert 'tool_calls' in result, "Should have tool_calls"
            assert len(result['tool_calls']) > 0, "Should use at least one tool for data query"
            assert result['session_data'] is None, "History query shouldn't create session"

            print("✅ PASS")

        except Exception as e:
            print(f"❌ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def test_chat_recommendations():
    """Test 2: ChatAgent should use Recommend tools for workout suggestions"""
    print("\n" + "=" * 70)
    print("TEST 2: Chat Recommendations")
    print("=" * 70)

    agent = ChatAgent()

    test_queries = [
        "What should I train today?",
        "What's next in my rotation?",
        "Am I behind on any muscle groups?"
    ]

    for query in test_queries:
        print(f"\n👤 User: {query}")
        print("🤖 Agent thinking...\n")

        try:
            result = agent.chat(query)

            print(f"✅ Response: {result['response'][:200]}...")
            print(f"📊 Tools used: {result['tool_calls']}")
            print(f"🎯 Session created: {result['session_data'] is not None}")

            # Assertions
            assert isinstance(result, dict), "Result should be dict"
            assert 'response' in result, "Should have response"
            assert len(result['tool_calls']) > 0, "Should use tools for recommendations"
            assert result['session_data'] is None, "Recommendation shouldn't create session"

            # Check if weekly split tool was used
            if 'get_weekly_split_status' in result['tool_calls']:
                print("✅ Used weekly split status (good!)")

            print("✅ PASS")

        except Exception as e:
            print(f"❌ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def test_session_creation():
    """Test 3: ChatAgent should create session when user wants to start workout"""
    print("\n" + "=" * 70)
    print("TEST 3: Workout Session Creation")
    print("=" * 70)

    agent = ChatAgent()

    test_phrases = [
        "Let's do a push workout",
        "I want to start a leg workout",
        "Let's begin",
        "I'm ready to workout"
    ]

    for phrase in test_phrases:
        print(f"\n👤 User: {phrase}")
        print("🤖 Agent thinking...\n")

        try:
            result = agent.chat(phrase)

            print(f"✅ Response: {result['response'][:200]}...")
            print(f"📊 Tools used: {result['tool_calls']}")
            print(f"🎯 Session created: {result['session_data'] is not None}")

            # Assertions
            assert isinstance(result, dict), "Result should be dict"
            assert 'response' in result, "Should have response"
            assert 'start_workout_session' in result['tool_calls'], f"Should call start_workout_session, called: {result['tool_calls']}"
            assert result['session_data'] is not None, "Should create session data"

            # Validate session structure
            session = result['session_data']
            assert 'session_id' in session, "Session should have ID"
            assert 'suggested_type' in session, "Session should have workout type"
            assert 'planned_template' in session, "Session should have template"

            print(f"🏋️  Session ID: {session['session_id']}")
            print(f"💪 Workout Type: {session['suggested_type']}")
            print(f"📋 Exercises: {len(session['planned_template'].get('exercises', []))}")

            print("✅ PASS")

        except Exception as e:
            print(f"❌ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def test_orchestrator_integration():
    """Test 4: Orchestrator should route to ChatAgent and pass session_data"""
    print("\n" + "=" * 70)
    print("TEST 4: Orchestrator Integration")
    print("=" * 70)

    orchestrator = GymBroOrchestrator()

    # Test chat intent routing
    print("\n👤 User: Let's start a workout")
    print("🤖 Orchestrator routing...\n")

    try:
        result = orchestrator.process_message("Let's start a workout")

        print(f"🎯 Intent: {result['intent']}")
        print(f"🔧 Handler: {result['handler']}")
        print(f"✅ Response: {result['response'][:200]}...")
        print(f"🎯 Session data present: {result['session_data'] is not None}")

        # Assertions
        assert result['intent'] == 'chat', f"Should route to chat, got: {result['intent']}"
        assert result['handler'] == 'chat_agent', f"Should use chat_agent, got: {result['handler']}"
        assert result['session_data'] is not None, "Should have session data"

        print("✅ PASS")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_false_sessions():
    """Test 5: ChatAgent should NOT create sessions for casual conversation"""
    print("\n" + "=" * 70)
    print("TEST 5: No False Session Creation")
    print("=" * 70)

    agent = ChatAgent()

    casual_messages = [
        "Hey, how are you?",
        "Thanks for the help!",
        "What is progressive overload?",
        "I'm feeling tired today"
    ]

    for message in casual_messages:
        print(f"\n👤 User: {message}")
        print("🤖 Agent thinking...\n")

        try:
            result = agent.chat(message)

            print(f"✅ Response: {result['response'][:150]}...")
            print(f"📊 Tools used: {result['tool_calls']}")
            print(f"🎯 Session created: {result['session_data'] is not None}")

            # Assertions
            assert result['session_data'] is None, f"Casual message shouldn't create session: '{message}'"

            print("✅ PASS - No false session")

        except Exception as e:
            print(f"❌ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🏋️  CHAT-WORKOUT INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nTesting Phase 1-3 Implementation:")
    print("  ✓ ChatAgent with Query/Recommend tools")
    print("  ✓ start_workout_session tool")
    print("  ✓ Orchestrator integration")
    print("  ✓ Session data extraction\n")

    results = []

    # Run tests
    results.append(("Chat History Queries", test_chat_history_query()))
    results.append(("Chat Recommendations", test_chat_recommendations()))
    results.append(("Session Creation", test_session_creation()))
    results.append(("Orchestrator Integration", test_orchestrator_integration()))
    results.append(("No False Sessions", test_no_false_sessions()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\n{total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Chat-workout integration is working!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
