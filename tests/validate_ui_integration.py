"""
Quick validation script for UI integration code.

Checks that all the pieces are in place for chat-workout navigation flow.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def validate_chat_page():
    """Validate pages/2_Chat.py has navigation button code"""
    print("\n📄 Validating pages/2_Chat.py...")

    with open('pages/2_Chat.py', 'r') as f:
        content = f.read()

    checks = [
        ("process_message usage", "process_message(" in content),
        ("session_data extraction", "session_data = result.get(\"session_data\")" in content),
        ("session storage", "st.session_state.workout_session = session_data" in content),
        ("chat_initiated_workout flag", "st.session_state.chat_initiated_workout = True" in content),
        ("navigation button section", "if st.session_state.get('workout_session') and st.session_state.get('chat_initiated_workout')" in content),
        ("Continue to Workout button", "Continue to Workout" in content),
        ("switch_page call", "st.switch_page" in content),
        ("Cancel workout option", "Cancel Workout" in content),
    ]

    all_pass = True
    for check_name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"  {status} {check_name}")
        if not condition:
            all_pass = False

    return all_pass


def validate_orchestrator():
    """Validate orchestrator returns session_data"""
    print("\n📄 Validating src/agents/main.py...")

    with open('src/agents/main.py', 'r') as f:
        content = f.read()

    checks = [
        ("ChatAgent import", "from src.agents.chat_agent import ChatAgent" in content),
        ("ChatAgent initialization", "self.chat_agent = ChatAgent()" in content),
        ("session_data in return type", "tuple[str, str, Any]" in content or "-> tuple" in content),
        ("chat_agent routing", "self.chat_agent.chat(user_input)" in content),
        ("session_data extraction", "result.get(\"session_data\")" in content),
        ("session_data in result dict", "\"session_data\": session_data" in content),
    ]

    all_pass = True
    for check_name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"  {status} {check_name}")
        if not condition:
            all_pass = False

    return all_pass


def validate_session_tools():
    """Validate session tool returns data instead of modifying state"""
    print("\n📄 Validating src/tools/session_tools.py...")

    with open('src/tools/session_tools.py', 'r') as f:
        content = f.read()

    checks = [
        ("start_workout_session defined", "def start_workout_session" in content),
        ("Returns dict not None", "return {" in content),
        ("session_data in return", "\"session_data\": session_state" in content),
        ("Success flag", "\"success\": True" in content),
        ("Message field", "\"message\":" in content),
        ("NO st.session_state modification", "st.session_state" not in content),
        ("Tool decorator", "@tool" in content),
        ("initialize_planning_session call", "initialize_planning_session()" in content),
    ]

    all_pass = True
    for check_name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"  {status} {check_name}")
        if not condition:
            all_pass = False

    return all_pass


def validate_chat_agent():
    """Validate ChatAgent extracts session_data from tool results"""
    print("\n📄 Validating src/agents/chat_agent.py...")

    with open('src/agents/chat_agent.py', 'r') as f:
        content = f.read()

    checks = [
        ("ChatAgent class", "class ChatAgent:" in content),
        ("start_workout_session in tools", "start_workout_session" in content),
        ("Returns dict with session_data", "\"session_data\": session_data" in content),
        ("Extracts from ToolMessage", "ToolMessage" in content),
        ("ast.literal_eval", "ast.literal_eval" in content),
        ("Trigger phrases in prompt", "TRIGGER PHRASES" in content or "let's start" in content),
        ("Temperature setting", "temperature=0.2" in content),
    ]

    all_pass = True
    for check_name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"  {status} {check_name}")
        if not condition:
            all_pass = False

    return all_pass


def validate_session_state():
    """Validate session.py has chat_initiated_workout flag"""
    print("\n📄 Validating src/ui/session.py...")

    with open('src/ui/session.py', 'r') as f:
        content = f.read()

    checks = [
        ("chat_initiated_workout initialization", "'chat_initiated_workout'" in content),
        ("Reset includes chat flag", "chat_initiated_workout = False" in content),
    ]

    all_pass = True
    for check_name, condition in checks:
        status = "✅" if condition else "❌"
        print(f"  {status} {check_name}")
        if not condition:
            all_pass = False

    return all_pass


def main():
    """Run all validation checks"""
    print("=" * 70)
    print("🔍 UI INTEGRATION VALIDATION")
    print("=" * 70)
    print("\nValidating that all code pieces are correctly integrated...")

    results = []
    results.append(("Chat Page", validate_chat_page()))
    results.append(("Orchestrator", validate_orchestrator()))
    results.append(("Session Tools", validate_session_tools()))
    results.append(("Chat Agent", validate_chat_agent()))
    results.append(("Session State", validate_session_state()))

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for component, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {component}")

    total_passed = sum(1 for _, passed in results if passed)
    total = len(results)

    print(f"\n{total_passed}/{total} components validated")

    if total_passed == total:
        print("\n✅ All UI integration code is in place!")
        print("\nNext step: Manual testing in Streamlit UI")
        print("See tests/MANUAL_TESTING_GUIDE.md for test steps")
        return 0
    else:
        print("\n⚠️  Some components have issues. Review above.")
        return 1


if __name__ == "__main__":
    exit(main())
